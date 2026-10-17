"""Build the Mac app of osmbot (D-061): ``python tools/build_mac.py [--zip] [--dmg]``.

Result: ``dist/mac/OSMbot.app``, a whole app (nothing to install): a relocatable CPython
(python-build-standalone) laid out so that ``Contents/MacOS/python3`` is the app's own process (the Dock
and the menu bar show OSMbot and its icon), osmbot's dependencies, osmbot's code and the Playwright Firefox.
``--zip`` also makes ``OSMbot-<version>-mac-portable.zip`` (the app zipped), ``--dmg`` the
``OSMbot-<version>-mac.dmg`` (open it and drag OSMbot to Applications). The session (``~/.osmbot``)
stays per machine: Login once on each Mac. The app is for this Mac's processor (Intel or Apple);
it is signed ad hoc only, so the first open is right click -> Open (or Privacy & Security -> Open Anyway).
Needs the Playwright Firefox already installed on THIS Mac (``playwright install firefox``) and
internet on the first run (to fetch the Python).
"""
from __future__ import annotations

import argparse
import platform
import plistlib
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_portable import DIST, ICON, firefox_revision, playwright_version, project_version  # noqa: E402

OUT_DIR = DIST / "mac"
APP = OUT_DIR / "OSMbot.app"
PYTHON_VERSION, PYTHON_BUILD = "3.12.15", "20261003"  # python-build-standalone release
ARCH = {"x86_64": "x86_64", "arm64": "aarch64"}.get(platform.machine(), platform.machine())
PYTHON_URL = ("https://github.com/astral-sh/python-build-standalone/releases/download/"
              f"{PYTHON_BUILD}/cpython-{PYTHON_VERSION}%2B{PYTHON_BUILD}-{ARCH}-apple-darwin-install_only.tar.gz")

LAUNCHER = """#!/bin/bash
# OSMbot.app: opens the osmbot window; from a terminal, Contents/MacOS/OSMbot <command> runs a command.
HERE="$(cd "$(dirname "$0")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$HERE/../Resources/browsers"
export PYTHONNOUSERSITE=1
unset PYTHONPATH PYTHONHOME
if [ ! -t 1 ]; then  # opened from the Finder: no terminal, keep what is printed (and any error) in a file
  mkdir -p "$HOME/.osmbot"
  exec >>"$HOME/.osmbot/app.log" 2>&1
fi
exec "$HERE/python3" -c 'from osmbot.cli import main; main()' "$@"
"""

README = """OSMbot - versao para Mac
========================

Arrasta o OSMbot para a pasta Aplicacoes (ou para onde quiseres) e abre-o.

Na primeira vez o macOS avisa que nao conhece o programador (a app nao e assinada pela Apple):
botao direito no OSMbot -> Abrir -> Abrir. Se nao aparecer o "Abrir": Definicoes do Sistema ->
Privacidade e Seguranca -> "Abrir na mesma".

Abre uma janela pequena: Abrir (o bot comeca a trabalhar), Login (entra no Firefox e FECHA a janela
do Firefox), Sair. Num Mac novo, comeca pelo Login. A sessao fica em ~/.osmbot (por Mac; nunca copiar).

Com o bot a trabalhar, o Mac nao adormece nem apaga o ecra. Fechar a tampa adormece-o na mesma:
deixa-o aberto e ligado a corrente. O icone fica na barra de cima.

Regra: so uma maquina com o bot ligado de cada vez.

Comandos (Terminal): OSMbot.app/Contents/MacOS/OSMbot menu | ativo --simular | status | treinos | slots
"""

# The window only uses QtCore, QtGui and QtWidgets (D-024); on the Mac QtGui also links QtDBus.
QT_KEEP_MODULES = {"QtCore", "QtGui", "QtWidgets"}
QT_KEEP_FRAMEWORKS = {"QtCore", "QtGui", "QtWidgets", "QtDBus"}
QT_KEEP_PLUGINS = ("platforms", "styles", "imageformats", "iconengines")
PY_DROP = ("test", "idlelib", "tkinter", "turtledemo", "ensurepip")  # parts of the standard library the bot never loads


def trim_pyside(site: Path) -> None:
    """Remove the parts of PySide6 the window does not use (keeps Core, Gui, Widgets and their plugins)."""
    qt = site / "PySide6"
    for item in qt.iterdir():
        if item.suffix == ".app":
            shutil.rmtree(item)
        elif item.name.startswith("Qt") and item.suffix in (".so", ".pyi") and item.name.split(".")[0] not in QT_KEEP_MODULES:
            item.unlink()
    for folder in ("qml", "metatypes", "include", "typesystems", "glue", "scripts", "translations", "resources"):
        shutil.rmtree(qt / "Qt" / folder, ignore_errors=True)
        shutil.rmtree(qt / folder, ignore_errors=True)
    for framework in (qt / "Qt" / "lib").glob("*.framework"):
        if framework.stem not in QT_KEEP_FRAMEWORKS:
            shutil.rmtree(framework)
    plugins = qt / "Qt" / "plugins"
    for folder in plugins.iterdir():
        if folder.name not in QT_KEEP_PLUGINS:
            shutil.rmtree(folder)
    for plugin in [*plugins.glob("*/*svg*"), *plugins.glob("*/*pdf*")]:
        plugin.unlink()  # they need QtSvg / QtPdf, left out above


def trim_python(contents: Path) -> None:
    lib = contents / "lib" / f"python{PYTHON_VERSION.rsplit('.', 1)[0]}"
    for name in PY_DROP:
        shutil.rmtree(lib / name, ignore_errors=True)
    for item in {*(lib / "lib-dynload").glob("_tkinter*"), *(contents / "lib").glob("*tcl*"), *(contents / "lib").glob("*tk*")}:
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    for folder in ("bin", "include", "share"):
        shutil.rmtree(contents / folder, ignore_errors=True)


def run(*command: str) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def fetch_python() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archive = OUT_DIR / f"cpython-{PYTHON_VERSION}-{PYTHON_BUILD}-{ARCH}.tar.gz"
    if not archive.exists():
        print(f"A descarregar {PYTHON_URL} ...")
        import certifi  # the Mac's Python often has no certificates of its own

        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(PYTHON_URL, context=context) as response, open(archive, "wb") as file:
            shutil.copyfileobj(response, file)
    return archive


def playwright_firefox() -> Path:
    found = sorted((Path.home() / "Library" / "Caches" / "ms-playwright").glob("firefox-*"))
    if not found:
        raise SystemExit("Firefox do Playwright nao encontrado. Corre primeiro: python -m playwright install firefox")
    return found[-1]


def make_icns(icon: Path, target: Path) -> bool:
    """The .ico (largest image, 256 px) as a .icns, with the Mac's own sips and iconutil."""
    with tempfile.TemporaryDirectory() as temp:
        png = Path(temp) / "icon.png"
        iconset = Path(temp) / "osmbot.iconset"
        iconset.mkdir()
        try:
            run("sips", "-s", "format", "png", str(icon), "--out", str(png))
            for size in (16, 32, 128, 256):
                for scale in (1, 2):
                    if size * scale <= 256:
                        name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
                        run("sips", "-z", str(size * scale), str(size * scale), str(png), "--out", str(iconset / name))
            run("iconutil", "-c", "icns", str(iconset), "-o", str(target))
        except (OSError, subprocess.CalledProcessError):
            return False
    return True


def info_plist(version: str, icon: bool) -> dict:
    info = {"CFBundleName": "OSMbot", "CFBundleDisplayName": "OSMbot", "CFBundleIdentifier": "io.github.osmbot",
            "CFBundleExecutable": "OSMbot", "CFBundlePackageType": "APPL", "CFBundleVersion": version,
            "CFBundleShortVersionString": version, "NSHighResolutionCapable": True}
    if icon:
        info["CFBundleIconFile"] = "osmbot"
    return info


def running_app() -> bool:
    """An OSMbot started from this build's app: emptying it would delete the code and the Firefox of a running bot."""
    return subprocess.run(["pgrep", "-f", str(APP / "Contents" / "MacOS")], capture_output=True).returncode == 0


def build(make_zip: bool, make_dmg: bool, icon: Path = ICON) -> None:
    if sys.platform != "darwin":
        raise SystemExit("Este script constroi a versao Mac; corre-o no Mac.")
    if running_app():
        raise SystemExit(f"Ha um OSMbot a correr a partir de {APP}. Fecha-o (Bot -> Sair) e volta a correr o build.")
    shutil.rmtree(APP, ignore_errors=True)
    contents = APP / "Contents"
    version = project_version()

    print("1/5 Python")
    with tempfile.TemporaryDirectory() as temp, tarfile.open(fetch_python()) as archive:
        archive.extractall(temp, filter="tar")
        shutil.copytree(Path(temp) / "python", contents, symlinks=True)
    # the python binary finds its library at ../lib and its prefix one level up: in Contents/MacOS it is the app's process
    (contents / "MacOS").mkdir()
    shutil.copy2(contents / "bin" / f"python{PYTHON_VERSION.rsplit('.', 1)[0]}", contents / "MacOS" / "python3")
    python = str(contents / "MacOS" / "python3")

    print("2/5 Dependencias")
    run(python, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "--no-warn-script-location",
        f"playwright=={playwright_version()}", "certifi", "PySide6-Essentials")
    site = next((contents / "lib").glob("python3.*/site-packages"))
    trim_pyside(site)

    print("3/5 Codigo do osmbot")
    shutil.copytree(Path(__file__).resolve().parent.parent / "src" / "osmbot", site / "osmbot",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    run(python, "-m", "pip", "uninstall", "--quiet", "--yes", "pip")
    trim_python(contents)

    print("4/5 Firefox do Playwright (demora)")
    firefox = playwright_firefox()
    wanted = firefox_revision(site)
    if firefox.name != f"firefox-{wanted}":
        raise SystemExit(f"O Playwright da app quer firefox-{wanted}, mas este Mac tem {firefox.name}. "
                         "Corre: python -m playwright install firefox")
    shutil.copytree(firefox, contents / "Resources" / "browsers" / firefox.name, symlinks=True)

    print("5/5 Arranque, icone e assinatura")
    launcher = contents / "MacOS" / "OSMbot"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    launcher.chmod(0o755)
    has_icon = icon.exists() and make_icns(icon, contents / "Resources" / "osmbot.icns")
    if icon.exists():
        shutil.copy(icon, contents / "Resources" / "osmbot.ico")  # the window's logo (gui.window.logo_path)
    with open(contents / "Info.plist", "wb") as file:
        plistlib.dump(info_plist(version, has_icon), file)
    signed = all(subprocess.run(["codesign", "--force", "--sign", "-", str(path)], capture_output=True).returncode == 0
                 for path in (contents / "MacOS" / "python3", APP))  # the binary inside first, then the app
    if not signed:
        print("  (assinatura ad hoc falhou: a app abre na mesma num Mac Intel)")
    (OUT_DIR / "LEIA-ME.txt").write_text(README, encoding="utf-8")

    size = sum(f.stat().st_size for f in APP.rglob("*") if f.is_file() and not f.is_symlink()) / 1e6
    print(f"Pronto: {APP}  ({size:.0f} MB, {ARCH})")
    if make_zip:
        target = OUT_DIR / f"OSMbot-{version}-mac-portable.zip"
        print("A criar o .zip ...")
        run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(APP), str(target))
        print(f"Zip: {target}  ({target.stat().st_size / 1e6:.0f} MB)")
    if make_dmg:
        target = OUT_DIR / f"OSMbot-{version}-mac.dmg"
        print("A criar o .dmg (demora uns minutos) ...")
        with tempfile.TemporaryDirectory() as temp:
            run("ditto", str(APP), str(Path(temp) / "OSMbot.app"))
            (Path(temp) / "Applications").symlink_to("/Applications")
            shutil.copy(OUT_DIR / "LEIA-ME.txt", Path(temp) / "LEIA-ME.txt")
            run("hdiutil", "create", "-quiet", "-volname", f"OSMbot {version}", "-srcfolder", temp, "-ov",
                "-format", "UDZO", str(target))
        print(f"Dmg: {target}  ({target.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--zip", action="store_true", help="also create dist/mac/OSMbot-<version>-mac-portable.zip")
    parser.add_argument("--dmg", action="store_true", help="also create dist/mac/OSMbot-<version>-mac.dmg")
    parser.add_argument("--icone", type=Path, default=ICON, help="icon (.ico) for the app; default: osmbot's own")
    arguments = parser.parse_args()
    build(arguments.zip, arguments.dmg, arguments.icone)
