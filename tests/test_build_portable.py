import importlib.util
from pathlib import Path


def test_portable_launcher_is_valid_python():
    path = Path(__file__).resolve().parent.parent / "tools" / "build_portable.py"
    spec = importlib.util.spec_from_file_location("build_portable", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    compile(module.SITECUSTOMIZE, "sitecustomize.py", "exec")
