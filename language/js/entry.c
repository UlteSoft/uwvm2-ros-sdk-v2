/** @file entry.c
 * @brief Evaluate one embedded UTF-8 script in a bounded QuickJS runtime.
 * @details The SDK generates the operation table from the commit's ROS schema.
 * Host grants apply separately to each import. No module loader or file, shell,
 * network or native plugin interface is registered. QuickJS Date and the
 * default Math.random seed use the explicitly deployable real-time clock.
 */
#include <stdint.h>
#include <string.h>
#include "quickjs.h"
#include <wros/scene.h>
#include "application.inc"

#define HEAP_LIMIT (8u * 1024 * 1024)
#define BUFFER_LIMIT (1024u * 1024)
typedef uint32_t (*Operation)(uint64_t, uint32_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);
typedef struct { const char *name; Operation invoke; int partial_report; } Method;
#include "operations.inc"

typedef struct { uint64_t token; int closed; } Handle;
static JSClassID handle_class;

static void erase(void *data, size_t bytes) {
    volatile uint8_t *p = data;
    while (bytes--) *p++ = 0;
}

static void dispose_handle(JSRuntime *rt, JSValue value) {
    Handle *h = JS_GetOpaque(value, handle_class);
    if (h) {
        erase(h, sizeof(*h));
        js_free_rt(rt, h);
    }
}

static Handle *checked(JSContext *ctx, JSValueConst value) {
    Handle *h = JS_GetOpaque2(ctx, value, handle_class);
    if (h && h->closed) {
        JS_ThrowTypeError(ctx, "closed capability");
        return NULL;
    }
    return h;
}

#ifdef WROS_JS_ABI
static JSValue abi(JSContext *ctx, JSValueConst self, int argc, JSValueConst *argv) {
    (void)self; (void)argc; (void)argv;
    return JS_NewUint32(ctx, wr_abi());
}
#endif

#ifdef WROS_JS_OPEN
static JSValue open_cap(JSContext *ctx, JSValueConst self, int argc, JSValueConst *argv) {
    (void)self;
    if (argc != 1 || !JS_IsString(argv[0])) return JS_ThrowTypeError(ctx, "expected a capability alias");
    size_t bytes;
    const char *alias = JS_ToCStringLen(ctx, &bytes, argv[0]);
    if (!alias) return JS_EXCEPTION;
    JSValue obj = JS_NewObjectClass(ctx, handle_class);
    if (!JS_IsException(obj)) {
        Handle *h = js_mallocz(ctx, sizeof(*h));
        if (!h) {
            JS_FreeValue(ctx, obj);
            obj = JS_EXCEPTION;
        } else {
            JS_SetOpaque(obj, h);
            uint32_t status = wr_capability_open(0, (uintptr_t)alias, bytes, (uintptr_t)&h->token);
            if (status) {
                JS_FreeValue(ctx, obj);
                obj = JS_NewUint32(ctx, status);
            }
        }
    }
    JS_FreeCString(ctx, alias);
    return obj;
}
#endif

#ifdef WROS_JS_CLOSE
static JSValue close_cap(JSContext *ctx, JSValueConst self, int argc, JSValueConst *argv) {
    (void)self;
    if (argc != 1) return JS_ThrowTypeError(ctx, "expected one capability");
    Handle *h = checked(ctx, argv[0]);
    if (!h) return JS_EXCEPTION;
    uint32_t status = wr_capability_close(h->token);
    if (!status) { h->closed = 1; h->token = 0; }
    return JS_NewUint32(ctx, status);
}
#endif

static JSValue invoke(JSContext *ctx, JSValueConst self, int argc, JSValueConst *argv, int method) {
    (void)self;
    if (argc != 3 || !JS_IsNumber(argv[2])) return JS_ThrowTypeError(ctx, "expected handle, ArrayBuffer and capacity");
    uint64_t token = 0;
    if (!JS_IsNull(argv[0])) {
        Handle *h = checked(ctx, argv[0]);
        if (!h) return JS_EXCEPTION;
        token = h->token;
    }
    double limit;
    if (JS_ToFloat64(ctx, &limit, argv[2]) < 0) return JS_EXCEPTION;
    if (!(limit >= 0 && limit <= BUFFER_LIMIT) || (uint32_t)limit != limit)
        return JS_ThrowRangeError(ctx, "invalid response capacity");
    size_t n = 0, capacity = (size_t)limit;
    uint8_t *source = JS_GetArrayBuffer(ctx, &n, argv[1]);
    if (!source) return JS_EXCEPTION;
    if (n > BUFFER_LIMIT) return JS_ThrowRangeError(ctx, "request exceeds interpreter buffer limit");
    uint8_t *input = n ? js_malloc(ctx, n) : NULL;
    if (n && !input) return JS_EXCEPTION;
    uint8_t *output = capacity ? js_mallocz(ctx, capacity) : NULL;
    if (capacity && !output) { js_free(ctx, input); return JS_EXCEPTION; }
    if (n) memcpy(input, source, n);
    uint64_t written = 0;
    uint32_t status = methods[method].invoke(token, 0, (uintptr_t)input, n, (uintptr_t)output, capacity, (uintptr_t)&written);
    erase(input, n);
    js_free(ctx, input);
    int has_reply = status == 0 || (methods[method].partial_report && status == 95 && written != 0);
    JSValue value = JS_NULL;
    if (has_reply) {
        value = written <= capacity ? JS_NewArrayBufferCopy(ctx, output, (size_t)written)
                                    : JS_ThrowRangeError(ctx, "invalid VM reply length");
    }
    erase(output, capacity);
    js_free(ctx, output);
    if (JS_IsException(value)) return value;
    JSValue result = JS_NewObjectProto(ctx, JS_NULL);
    if (JS_IsException(result)) { JS_FreeValue(ctx, value); return result; }
    if (JS_DefinePropertyValueStr(ctx, result, "data", value, JS_PROP_ENUMERABLE) < 0 ||
        JS_DefinePropertyValueStr(ctx, result, "status", JS_NewUint32(ctx, status), JS_PROP_ENUMERABLE) < 0) {
        JS_FreeValue(ctx, result); return JS_EXCEPTION;
    }
    JSValue length = JS_NewBigUint64(ctx, written);
    if (JS_IsException(length) || JS_DefinePropertyValueStr(ctx, result, "written", length, JS_PROP_ENUMERABLE) < 0) {
        JS_FreeValue(ctx, result); return JS_EXCEPTION;
    }
    return result;
}

static int add(JSContext *ctx, JSValueConst target, const char *name, JSValue method) {
    if (JS_IsException(method)) return -1;
    return JS_DefinePropertyValueStr(ctx, target, name, method, JS_PROP_ENUMERABLE);
}

static int install(JSContext *ctx) {
    static const JSClassDef class_def = {.class_name="WrosCapability", .finalizer=dispose_handle};
    JS_NewClassID(&handle_class);
    if (JS_NewClass(JS_GetRuntime(ctx), handle_class, &class_def) < 0) return -1;
    JSValue api = JS_NewObjectProto(ctx, JS_NULL);
    if (JS_IsException(api)) return -1;
#ifdef WROS_JS_ABI
    if (add(ctx, api, "abi", JS_NewCFunction(ctx, abi, "abi", 0)) < 0) goto fail;
#endif
#ifdef WROS_JS_OPEN
    if (add(ctx, api, "open", JS_NewCFunction(ctx, open_cap, "open", 1)) < 0) goto fail;
#endif
#ifdef WROS_JS_CLOSE
    if (add(ctx, api, "close", JS_NewCFunction(ctx, close_cap, "close", 1)) < 0) goto fail;
#endif
    for (int i = 0; methods[i].name; ++i) {
        const char *name = methods[i].name;
        if (add(ctx, api, name, JS_NewCFunctionMagic(ctx, invoke, name, 3, JS_CFUNC_generic_magic, i)) < 0) goto fail;
    }
    JSValue global = JS_GetGlobalObject(ctx);
    int ret = add(ctx, global, "wros", api);
    JS_FreeValue(ctx, global);
    return ret;
fail:
    JS_FreeValue(ctx, api);
    return -1;
}

void _start(void) {
    JSRuntime *rt = JS_NewRuntime();
    if (!rt) __builtin_trap();
    JS_SetMaxStackSize(rt, 32 * 1024);
    JS_SetMemoryLimit(rt, HEAP_LIMIT);
    JSContext *ctx = JS_NewContext(rt);
    int failed = !ctx;
    if (ctx) {
        failed = install(ctx) < 0;
        if (!failed) {
            JSValue result = JS_Eval(ctx, application, sizeof(application)-1, "application.js", JS_EVAL_TYPE_GLOBAL);
            failed = JS_IsException(result);
            JS_FreeValue(ctx, result);
        }
        JS_FreeContext(ctx);
    }
    JS_FreeRuntime(rt);
    if (failed) __builtin_trap();
}
