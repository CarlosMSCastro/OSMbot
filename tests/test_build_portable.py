import importlib.util
from pathlib import Path


def test_portable_launcher_is_valid_python():
    path = Path(__file__).resolve().parent.parent / "tools" / "build_portable.py"
    spec = importlib.util.spec_from_file_location("build_portable", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    compile(module.SITECUSTOMIZE, "sitecustomize.py", "exec")


def test_the_mac_app_runs_its_own_python_and_names_itself_osmbot():
    path = Path(__file__).resolve().parent.parent / "tools" / "build_mac.py"
    spec = importlib.util.spec_from_file_location("build_mac", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.LAUNCHER.startswith("#!/bin/bash") and '"$HERE/python3"' in module.LAUNCHER
    info = module.info_plist("1.2.3", icon=True)
    assert info["CFBundleExecutable"] == "OSMbot" and info["CFBundleShortVersionString"] == "1.2.3"
    assert info["CFBundleIconFile"] == "osmbot" and "CFBundleIconFile" not in module.info_plist("1.2.3", icon=False)
