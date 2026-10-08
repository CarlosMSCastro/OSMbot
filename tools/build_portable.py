"""Build the Windows portable folder of osmbot (D-016): ``python tools/build_portable.py [--zip]``.

Result: ``dist/osmbot-portable/`` with ``OSMbot.exe`` (a renamed copy of the official, signed
embeddable ``python.exe``; ``app/sitecustomize.py`` turns it into the osmbot menu), the Python
runtime next to it, osmbot's dependencies and the Playwright Firefox. Copy the folder (or the .zip)
to another Windows PC and double-click ``OSMbot.exe``; nothing is installed. The session
(``~/.osmbot``) stays per machine: choose "Login" in the menu once on each PC.
Needs the Playwright Firefox already installed on THIS machine (``playwright install firefox``)
and internet on the first run (to fetch the embeddable Python).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUT = DIST / "osmbot-portable"
PYTHON_VERSION = "3.12.10"  # same minor version as the dependencies are installed for
EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"

SITECUSTOMIZE = '''"""Runs when Python starts. As OSMbot.exe (a renamed python.exe) it opens the osmbot window or runs a command."""
import os
import sys

if os.path.basename(sys.executable).lower() == "osmbot.exe":
    here = os.path.dirname(os.path.abspath(sys.executable))
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(here, "browsers"))
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleTitleW("OSMbot")
    except Exception:
        pass
    code = 0
    try:
        from osmbot.cli import main

        main([arg for arg in sys.argv if arg])  # python.exe takes the first word for a script name: pass them all on
    except SystemExit as stop:
        if isinstance(stop.code, str):
            print(stop.code)
            code = 1
        else:
            code = stop.code or 0
    except KeyboardInterrupt:
        pass
    except BaseException:
        import traceback

        try:  # the window hides the console: show it again so the error can be read
            import ctypes

            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 5)
        except Exception:
            pass
        traceback.print_exc()
        input("\\nErro. Enter para fechar...")
        code = 1
    sys.stdout.flush()
    os._exit(code)
'''

README = """OSMbot - versao portatil (Windows)
==================================

Nao instala nada. Copia esta pasta para onde quiseres.

Abre o  OSMbot.exe  (duplo clique). Abre uma janela pequena:

  Abrir     carrega o jogo e o bot comeca a trabalhar (treinos, estadio, patrocinadores, videos,
            recompensas diarias, avisos); a janela cresce para o quadro
  Login     abre o Firefox. Entra com o Facebook e FECHA a janela do Firefox.
  Sair

No quadro: menu Bot (Iniciar, Parar, Login, Sair) e menu Ver (Avisos e erros, Pasta dos logs...).
Com o bot a trabalhar, fechar a janela (X) so a esconde: o bot continua, com o icone junto ao relogio
(bolinha verde = a trabalhar, cinzenta = parado). Para sair: menu Bot -> Sair, ou o icone -> Sair.

Num PC novo, comeca pelo Login. A sessao fica em %USERPROFILE%\\.osmbot
(por PC; nunca copiar para outro PC).

Regra: so uma maquina com o bot ligado de cada vez.

Nao mexer nos outros ficheiros e pastas (sao o Python, as bibliotecas e o Firefox).
Se o Windows avisar ("SmartScreen"): Mais informacoes -> Executar mesmo assim.

Comandos diretos (para quem quiser): OSMbot.exe menu (o menu antigo, na consola) | ativo --simular | ativo --sem-anuncios | status | treinos | slots
"""


# The window only uses QtCore, QtGui and QtWidgets (D-024): the rest of PySide6 (QML, Quick, Designer, tools...)
# is ~100 MB the bot never loads, so it is left out of the portable folder.
QT_KEEP_MODULES = {"QtCore", "QtGui", "QtWidgets"}
QT_DROP_DIRS = ("qml", "metatypes", "include", "typesystems", "glue", "scripts", "translations", "resources")
QT_DROP_DLLS = ("Qt6Quick", "Qt6Qml", "Qt6Designer", "Qt6LabsStyleKit", "Qt6OpenGL", "Qt6Network", "Qt6Pdf",
                "Qt6Concurrent", "Qt6Sql", "Qt6Test", "Qt6Xml", "Qt6DBus", "Qt6PrintSupport", "Qt6Help", "Qt6UiTools",
                "Qt6Svg", "Qt6Multimedia", "Qt6Web", "opengl32sw")
QT_KEEP_PLUGINS = ("platforms", "styles", "imageformats", "iconengines")


def trim_pyside(site: Path) -> None:
    """Remove the parts of PySide6 the window does not use (keeps Core, Gui, Widgets and their plugins)."""
    qt = site / "PySide6"
    for name in QT_DROP_DIRS:
        shutil.rmtree(qt / name, ignore_errors=True)
    for item in qt.iterdir():
        if item.suffix == ".exe":
            item.unlink()
        elif item.suffix in (".pyd", ".pyi") and item.stem.startswith("Qt") and item.stem not in QT_KEEP_MODULES:
            item.unlink()
        elif item.suffix == ".dll" and item.name.startswith(QT_DROP_DLLS):
            item.unlink()
    plugins = qt / "plugins"
    if plugins.exists():
        for folder in plugins.iterdir():
            if folder.name not in QT_KEEP_PLUGINS:
                shutil.rmtree(folder, ignore_errors=True)
        for folder in ("imageformats", "iconengines"):
            for plugin in (plugins / folder).glob("*svg*"):
                plugin.unlink()  # svg needs Qt6Svg, left out above


def run(*command: str) -> None:
    subprocess.run(command, check=True)


def fetch_embedded_python() -> Path:
    DIST.mkdir(exist_ok=True)
    archive = DIST / f"python-{PYTHON_VERSION}-embed-amd64.zip"
    if not archive.exists():
        print(f"A descarregar {EMBED_URL} ...")
        urllib.request.urlretrieve(EMBED_URL, archive)
    return archive


def playwright_firefox() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "ms-playwright"
    found = sorted(base.glob("firefox-*"))
    if not found:
        raise SystemExit("Firefox do Playwright nao encontrado. Corre primeiro: python -m playwright install firefox")
    return found[-1]


ICON = ROOT / "tools" / "assets" / "osmbot.ico"  # osmbot's own icon (tools/make_icon.py); --icone PATH overrides it for a personal build
ISCC_PATHS = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
    Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
)


def project_version() -> str:
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=")[1].strip().strip('"')
    return "0.0.0"


def build_installer(icon: Path) -> None:
    """Compile tools/installer.iss with Inno Setup into dist/OSMbot-Setup.exe."""
    iscc = next((p for p in ISCC_PATHS if p.exists()), None)
    if not iscc:
        raise SystemExit("Inno Setup nao encontrado. Instala-o: winget install JRSoftware.InnoSetup")
    command = [str(iscc), "/Qp", f"/DAppVersion={project_version()}", f"/DSourceDir={OUT}", f"/DOutDir={DIST}"]
    if icon.exists():
        command.append(f"/DIconFile={icon}")
    print("A criar o instalador (demora uns minutos) ...")
    run(*command, str(ROOT / "tools" / "installer.iss"))
    target = DIST / "OSMbot-Setup.exe"
    print(f"Instalador: {target}  ({target.stat().st_size / 1e6:.0f} MB)")


def running_from(folder: Path) -> list[str]:
    """Paths of OSMbot.exe processes started from ``folder`` (Windows): the build must not empty a folder in use."""
    result = subprocess.run(["powershell", "-NoProfile", "-Command",
                             "Get-Process OSMbot -ErrorAction SilentlyContinue | ForEach-Object { $_.Path }"],
                            capture_output=True, text=True)
    inside = str(folder.resolve()).lower()
    return [line.strip() for line in result.stdout.splitlines() if line.strip().lower().startswith(inside)]


def build(make_zip: bool, make_installer: bool = False, icon: Path = ICON) -> None:
    if sys.platform != "win32":
        raise SystemExit("Este script constroi a versao Windows; corre-o no Windows.")
    if OUT.exists() and running_from(OUT):  # emptying it would delete the code and the Firefox of a running bot
        raise SystemExit(f"Ha um OSMbot a correr a partir de {OUT}. Fecha-o (Bot -> Sair) e volta a correr o build.")
    if OUT.exists():  # empty the folder instead of deleting it: a terminal opened inside it would block the delete
        for child in OUT.iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    app_dir = OUT / "app"
    OUT.mkdir(parents=True, exist_ok=True)

    print("1/5 Python embutido")
    with zipfile.ZipFile(fetch_embedded_python()) as archive:
        archive.extractall(OUT)
    pth = next(OUT.glob("python*._pth"))
    stem = pth.stem.split("._")[0]
    pth.write_text(f"{stem}.zip\n.\nLib\\site-packages\napp\nimport site\n", encoding="utf-8")
    shutil.move(OUT / "python.exe", OUT / "OSMbot.exe")  # the signed python.exe, under osmbot's name
    (OUT / "pythonw.exe").unlink(missing_ok=True)

    print("2/5 Dependencias")
    run(sys.executable, "-m", "pip", "install", "--quiet", "--target", str(OUT / "Lib" / "site-packages"),
        "playwright", "certifi", "PySide6-Essentials")
    trim_pyside(OUT / "Lib" / "site-packages")

    print("3/5 Codigo do osmbot")
    shutil.copytree(ROOT / "src" / "osmbot", app_dir / "osmbot", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (app_dir / "sitecustomize.py").write_text(SITECUSTOMIZE, encoding="utf-8")

    print("4/5 Firefox do Playwright (demora)")
    firefox = playwright_firefox()
    shutil.copytree(firefox, OUT / "browsers" / firefox.name)

    print("5/5 Leia-me e icone")
    (OUT / "LEIA-ME.txt").write_text(README, encoding="utf-8")
    if icon.exists():
        shutil.copy(icon, OUT / "osmbot.ico")  # used by the installer's shortcuts (the signed exe is left untouched)
    else:
        print("  (sem icone: atalhos com o icone do Python)")

    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"Pronto: {OUT}  ({size:.0f} MB)")
    if make_zip:
        print("A criar o .zip ...")
        target = shutil.make_archive(str(DIST / "osmbot-portable"), "zip", DIST, "osmbot-portable")
        print(f"Zip: {target}  ({Path(target).stat().st_size / 1e6:.0f} MB)")
    if make_installer:
        build_installer(icon)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--zip", action="store_true", help="also create dist/osmbot-portable.zip")
    parser.add_argument("--installer", action="store_true", help="also create dist/OSMbot-Setup.exe (needs Inno Setup)")
    parser.add_argument("--icone", type=Path, default=ICON, help="icon (.ico) for the shortcuts; default: osmbot's own")
    arguments = parser.parse_args()
    build(arguments.zip, arguments.installer, arguments.icone)
