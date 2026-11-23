"""Initialize guest module loading and evaluate the selected Python application."""
import _frozen_importlib
import _uwros_runtime
import sys


class EmbeddedModules:
    def find_spec(self, fullname, path=None, target=None):
        entry = _uwros_runtime.lookup(fullname)
        if entry is None:
            return None
        source, filename, package = entry
        spec = _frozen_importlib.ModuleSpec(fullname, self, origin=filename, is_package=package)
        spec.has_location = True
        spec.loader_state = source
        return spec

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        spec = module.__spec__
        source = spec.loader_state
        spec.loader_state = None
        exec(compile(source, spec.origin, "exec", dont_inherit=True), module.__dict__)

    def get_source(self, fullname):
        source, _, _ = _uwros_runtime.lookup(fullname)
        import importlib.util
        return importlib.util.decode_source(source)


def run():
    # Preserve ordinary priority for CPython's builtin and frozen modules.
    sys.meta_path.insert(2, EmbeddedModules())
    entry = _uwros_runtime.lookup("__main__")
    if entry is not None:
        source, filename, _ = entry
        sys.argv[0] = filename
    else:
        filename = sys.argv[0]
        if filename == "-":
            filename = "<stdin>"
            if sys.stdin is None:
                raise PermissionError("the shared interpreter requires a readable Preview1 stdin")
            source = sys.stdin.buffer.read()
        else:
            with open(filename, "rb") as stream:
                source = stream.read()
            # Guest paths resolve only through the VM's configured preopens.
            sys.path.insert(0, filename.rpartition("/")[0] or ".")
    namespace = sys.modules["__main__"].__dict__
    namespace["__file__"] = filename
    namespace["__package__"] = None
    exec(compile(source, filename, "exec", dont_inherit=True), namespace)


run()
