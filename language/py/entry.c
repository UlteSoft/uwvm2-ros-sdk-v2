/** @file entry.c
 *  @brief Interpret the embedded application in a statically linked guest CPython.
 *  @details All code and module lookup stay in the guest. Startup uses frozen
 *  encodings, an isolated config and an empty environment. Application failures
 *  report a Wasm trap. Successful SystemExit(0) returns from the module.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include "frozen.h"
#include "application.inc"
#include "scene.h"

static void require_status(PyStatus status)
{
    if (PyStatus_Exception(status))
        __builtin_trap();
}

/** @brief Initialize one private interpreter, evaluate the application and finalize it. */
__attribute__((export_name("_start"))) void wros_start(void)
{
    if (PyImport_AppendInittab("wros", PyInit_wros) != 0)
        __builtin_trap();
    PyImport_FrozenModules = sdk_frozen;
    PyPreConfig pre;
    PyPreConfig_InitIsolatedConfig(&pre);
    pre.utf8_mode = 1;
    pre.configure_locale = 0;
    require_status(Py_PreInitialize(&pre));
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
    require_status(PyConfig_SetString(&config, &config.program_name, L"wrpy"));
    require_status(PyConfig_SetString(&config, &config.home, L"/wros/frozen"));
    require_status(PyConfig_SetString(&config, &config.filesystem_encoding, L"utf-8"));
    require_status(PyConfig_SetString(&config, &config.stdio_encoding, L"utf-8"));
    PyStatus status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    require_status(status);
    PyObject *module = PyImport_AddModule("__main__");
    if (module == NULL)
        __builtin_trap();
    PyObject *globals = PyModule_GetDict(module);
    if (module_loader[0]) {
        PyObject *loader_globals = PyDict_New();
        if (!loader_globals) __builtin_trap();
        PyObject *bridge = PyRun_StringFlags(module_loader, Py_file_input, loader_globals, loader_globals, NULL);
        Py_DECREF(loader_globals);
        if (!bridge) __builtin_trap();
        Py_DECREF(bridge);
    }
    PyObject *result = PyRun_StringFlags(application, Py_file_input, globals, globals, NULL);
    int ok = result != NULL;
    if (!ok && PyErr_ExceptionMatches(PyExc_SystemExit)) {
        PyObject *exc = PyErr_GetRaisedException();
        PyObject *code = PyObject_GetAttrString(exc, "code");
        ok = code == Py_None || (code && PyLong_Check(code) && PyLong_AsLong(code) == 0 && !PyErr_Occurred());
        Py_XDECREF(code);
        Py_DECREF(exc);
    }
    Py_XDECREF(result);
    if (Py_FinalizeEx() < 0 || !ok)
        __builtin_trap();
}
