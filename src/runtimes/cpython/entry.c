/* Start CPython in the guest. The WASI CRT supplies argv, constructors and exit. */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "frozen.h"

typedef struct {
    const char *name, *filename;
    uint32_t offset, size;
    int package;
} EmbeddedModule;

typedef struct {
    const char *name;
    unsigned arity, wide;
    uint32_t (*invoke)(const uint64_t *);
} RawMethod;

extern const unsigned char wros_sources[];
#include "application.inc"
#include "operations.inc"

static PyObject *lookup(PyObject *self, PyObject *arg)
{
    const char *name = PyUnicode_AsUTF8(arg);
    if (!name) return NULL;
    size_t lo = 0, hi = sizeof(modules) / sizeof(modules[0]);
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        const EmbeddedModule *item = &modules[mid];
        int order = strcmp(name, item->name);
        if (order == 0)
            return Py_BuildValue("(y#sO)", (const char *)wros_sources + item->offset,
                                 (Py_ssize_t)item->size, item->filename, item->package ? Py_True : Py_False);
        if (order < 0) hi = mid;
        else lo = mid + 1;
    }
    Py_RETURN_NONE;
}

static PyObject *buffer_address(PyObject *self, PyObject *arg)
{
    Py_buffer view;
    if (PyObject_GetBuffer(arg, &view, PyBUF_WRITABLE | PyBUF_C_CONTIGUOUS) < 0)
        return NULL;
    PyObject *value = PyLong_FromUnsignedLongLong((uint64_t)(uintptr_t)view.buf);
    PyBuffer_Release(&view);
    return value;
}

static PyObject *raw(PyObject *self, PyObject *const *args, Py_ssize_t argc)
{
    if (argc < 1) {
        PyErr_SetString(PyExc_TypeError, "raw requires a ROS operation name");
        return NULL;
    }
    const char *name = PyUnicode_AsUTF8(args[0]);
    if (!name) return NULL;
    for (const RawMethod *method = methods; method->name; ++method) {
        if (strcmp(name, method->name)) continue;
        if (argc - 1 != method->arity) {
            PyErr_Format(PyExc_TypeError, "%s takes %u operands", name, method->arity);
            return NULL;
        }
        uint64_t operands[7] = {0};
        for (unsigned i = 0; i < method->arity; ++i) {
            operands[i] = PyLong_AsUnsignedLongLong(args[i + 1]);
            if (PyErr_Occurred()) return NULL;
            if (!(method->wide & (1u << i)) && operands[i] > UINT32_MAX) {
                PyErr_SetString(PyExc_OverflowError, "i32 operand exceeds 32 unsigned bits");
                return NULL;
            }
        }
        return PyLong_FromUnsignedLong(method->invoke(operands));
    }
    PyErr_Format(PyExc_LookupError, "ROS import %s was not selected when this guest was linked", name);
    return NULL;
}

static PyMethodDef runtime_methods[] = {
    {"lookup", lookup, METH_O, "Read a bundled module by its qualified Python name."},
    {"address", buffer_address, METH_O, "Return the guest address of writable contiguous pinned storage."},
    {"raw", (PyCFunction)(void (*)(void))raw, METH_FASTCALL, "Invoke an explicitly linked ROS import."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef runtime_module = {
    PyModuleDef_HEAD_INIT, "_uwros_runtime", "Guest CPython SDK support.", -1, runtime_methods
};

static PyObject *runtime_init(void) { return PyModule_Create(&runtime_module); }

static void require_ok(PyStatus status)
{
    if (PyStatus_Exception(status)) Py_ExitStatusException(status);
}

int main(int argc, char **argv)
{
    if (PyImport_AppendInittab("_uwros_runtime", runtime_init) != 0) return 1;
    PyImport_FrozenModules = sdk_frozen;
    PyPreConfig pre;
    PyPreConfig_InitIsolatedConfig(&pre);
    pre.utf8_mode = 1;
    pre.configure_locale = 0;
    require_ok(Py_PreInitialize(&pre));
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.site_import = 0;
    config.user_site_directory = 0;
    config.use_environment = 0;
    config.parse_argv = 0;
    config.write_bytecode = 0;
    config.install_signal_handlers = 0;
    config.use_frozen_modules = 1;
    config.module_search_paths_set = 1;
    config.pathconfig_warnings = 0;
    config.configure_c_stdio = 0;
    config.use_hash_seed = 1;
    config.hash_seed = 0;
    require_ok(PyConfig_SetString(&config, &config.program_name, L"cpython.wasm"));
    require_ok(PyConfig_SetString(&config, &config.home, L"/wros/python"));
    require_ok(PyConfig_SetString(&config, &config.filesystem_encoding, L"utf-8"));
    require_ok(PyConfig_SetString(&config, &config.stdio_encoding, L"utf-8"));
    char *default_args[] = {"-", NULL};
    if (embedded_main && argc > 0) {
        require_ok(PyConfig_SetBytesArgv(&config, argc, argv));
    } else if (!embedded_main && argc > 1) {
        require_ok(PyConfig_SetBytesArgv(&config, argc - 1, argv + 1));
    } else {
        require_ok(PyConfig_SetBytesArgv(&config, 1, default_args));
    }
    PyStatus status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    require_ok(status);
    PyObject *globals = PyDict_New();
    PyObject *result = globals ? PyRun_String(bootstrap, Py_file_input, globals, globals) : NULL;
    int code = result ? 0 : 1;
    if (!result) {
        /* CPython handles SystemExit here with its normal status convention.
           All diagnostics and process exits still cross the real WASI policy. */
        PyErr_Print();
    }
    Py_XDECREF(result);
    Py_XDECREF(globals);
    return Py_FinalizeEx() < 0 ? 120 : code;
}
