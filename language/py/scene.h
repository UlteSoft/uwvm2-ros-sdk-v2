/** @file scene.h
 *  @brief Expose the specifically selected ROSv2 operations to embedded CPython.
 *
 *  @details The generated operations.inc names individually selected imports.
 *  Capability tokens live in opaque guest-owned capsules. Only call-scoped
 *  request and response buffers cross the host boundary. The VM applies its
 *  policy independently of the set of imports selected when linking.
 */
#include <wros/scene.h>
#include <string.h>

typedef uint32_t (*WrCall)(uint64_t, uint32_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);
typedef struct { const char *name; WrCall call; int partial; } WrMethod;
#include "operations.inc"

enum { WR_BUFFER_LIMIT = 4 * 1024 * 1024 };

/** @brief Overwrite temporary ABI memory before its allocator can reuse it. */
static void wr_erase(void *memory, size_t length)
{
    volatile unsigned char *p = memory;
    while (length--) *p++ = 0;
}

#if defined(WR_PY_OPEN) || defined(WR_PY_CLOSE) || defined(WR_PY_CALL)
/** @brief A live VM token, scoped to one guest object. */
typedef struct { uint64_t token; int live; } WrHandle;
static const char wr_capsule[] = "wros.capability";

/** @brief Retrieve one guest-owned live handle or set a Python exception. */
static WrHandle *wr_checked(PyObject *object)
{
    WrHandle *handle = PyCapsule_GetPointer(object, wr_capsule);
    if (handle && !handle->live) {
        PyErr_SetString(PyExc_ValueError, "closed WROS capability");
        return NULL;
    }
    return handle;
}
#endif

#ifdef WR_PY_ABI
/** @brief Read the host ABI after module exposure has been checked by the VM. */
static PyObject *wr_python_abi(PyObject *self, PyObject *unused)
{
    return PyLong_FromUnsignedLong(wr_abi());
}
#endif

#ifdef WR_PY_OPEN
/** @brief Clear and release guest capsule storage without initiating a host operation. */
static void wr_dispose(PyObject *capsule)
{
    WrHandle *handle = PyCapsule_GetPointer(capsule, wr_capsule);
    if (handle) {
        wr_erase(handle, sizeof(*handle));
        PyMem_Free(handle);
    }
}

/** @brief Resolve one exact alias and return its opaque capability or a host status. */
static PyObject *wr_python_open(PyObject *self, PyObject *name)
{
    if (!PyUnicode_CheckExact(name)) {
        PyErr_SetString(PyExc_TypeError, "expected a capability alias string");
        return NULL;
    }
    Py_ssize_t size;
    const char *alias = PyUnicode_AsUTF8AndSize(name, &size);
    if (!alias) return NULL;
    WrHandle *handle = PyMem_Calloc(1, sizeof(*handle));
    if (!handle) return PyErr_NoMemory();
    PyObject *object = PyCapsule_New(handle, wr_capsule, wr_dispose);
    if (!object) { PyMem_Free(handle); return NULL; }
    uint32_t status = wr_capability_open(0, (uintptr_t)alias, (uint64_t)size, (uintptr_t)&handle->token);
    if (status != 0) {
        Py_DECREF(object);
        return PyLong_FromUnsignedLong(status);
    }
    handle->live = 1;
    return object;
}
#endif

#ifdef WR_PY_CLOSE
/** @brief Close a live capability and invalidate its wrapper on successful release. */
static PyObject *wr_python_close(PyObject *self, PyObject *object)
{
    WrHandle *handle = wr_checked(object);
    if (!handle) return NULL;
    uint32_t status = wr_capability_close(handle->token);
    if (!status) { handle->live = 0; handle->token = 0; }
    return PyLong_FromUnsignedLong(status);
}
#endif

#ifdef WR_PY_CALL
/** @brief Invoke one selected buffer operation, preserving its status and bounded reply. */
static PyObject *wr_python_call(PyObject *self, PyObject *args)
{
    const char *name;
    PyObject *object, *payload;
    Py_ssize_t capacity;
    if (!PyArg_ParseTuple(args, "sOOn:call", &name, &object, &payload, &capacity))
        return NULL;
    const WrMethod *method = wr_methods;
    while (method->name && strcmp(name, method->name)) ++method;
    if (!method->name) { PyErr_SetString(PyExc_KeyError, name); return NULL; }
    WrHandle *handle = object == Py_None ? NULL : wr_checked(object);
    if (!handle && object != Py_None) return NULL;
    if (!PyBytes_CheckExact(payload)) {
        PyErr_SetString(PyExc_TypeError, "payload must be bytes");
        return NULL;
    }
    Py_ssize_t length = PyBytes_GET_SIZE(payload);
    if (capacity < 0 || capacity > WR_BUFFER_LIMIT || length > WR_BUFFER_LIMIT) {
        PyErr_SetString(PyExc_ValueError, "operation buffer exceeds 4 MiB");
        return NULL;
    }
    void *input = length ? PyMem_Malloc((size_t)length) : NULL;
    void *output = capacity ? PyMem_Calloc(1, (size_t)capacity) : NULL;
    if ((length && !input) || (capacity && !output)) {
        PyMem_Free(input); PyMem_Free(output);
        return PyErr_NoMemory();
    }
    if (length) memcpy(input, PyBytes_AS_STRING(payload), (size_t)length);
    uint64_t written = 0;
    uint32_t status = method->call(handle ? handle->token : 0, 0, (uintptr_t)input,
                                    length, (uintptr_t)output, capacity, (uintptr_t)&written);
    wr_erase(input, (size_t)length);
    PyMem_Free(input);
    PyObject *value = NULL;
    if (status == 0 || (method->partial && status == 95 && written)) {
        if (written <= (uint64_t)capacity)
            value = PyBytes_FromStringAndSize(output, (Py_ssize_t)written);
        else
            PyErr_SetString(PyExc_ValueError, "host response exceeds output capacity");
    } else {
        value = Py_NewRef(Py_None);
    }
    wr_erase(output, (size_t)capacity);
    PyMem_Free(output);
    return value ? Py_BuildValue("INK", status, value, (unsigned long long)written) : NULL;
}
#endif

static PyMethodDef wr_python_methods[] = {
#ifdef WR_PY_ABI
    {"abi", wr_python_abi, METH_NOARGS, "Return the ROSv2 host ABI."},
#endif
#ifdef WR_PY_OPEN
    {"open", wr_python_open, METH_O, "Open one configured capability alias."},
#endif
#ifdef WR_PY_CLOSE
    {"close", wr_python_close, METH_O, "Close one capability and return its status."},
#endif
#ifdef WR_PY_CALL
    {"call", wr_python_call, METH_VARARGS, "Invoke a selected buffered operation."},
#endif
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef wr_module = {PyModuleDef_HEAD_INIT, "wros", NULL, -1, wr_python_methods};
/** @brief Create the built-in module containing the selected permission-scoped API. */
static PyObject *PyInit_wros(void) { return PyModule_Create(&wr_module); }
