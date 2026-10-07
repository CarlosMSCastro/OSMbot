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

SITECUSTOMIZE = '''"""Runs when Python starts. As OSMbot.exe (a renamed python.exe) it opens the osmbot menu or runs a command."""
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

        traceback.print_exc()
        input("\\nErro. Enter para fechar...")
        code = 1
    sys.stdout.flush()
    os._exit(code)
'''

README = """OSMbot - versao portatil (Windows)
==================================

Nao instala nada. Copia esta pasta para onde quiseres.

Abre o  OSMbot.exe  (duplo clique). Aparece um menu na consola:

  1  Iniciar   (treinos, estadio, patrocinadores, videos, avisos)   Ctrl+C para parar
  2  Login: abre o Firefox. Entra com o Facebook e FECHA a janela.
  0  Sair

Num PC novo, comeca pela opcao 2 (login). A sessao fica em %USERPROFILE%\\.osmbot
(por PC; nunca copiar para outro PC).

Regra: so uma maquina com o bot ligado de cada vez.

Nao mexer nos outros ficheiros e pastas (sao o Python, as bibliotecas e o Firefox).
Se o Windows avisar ("SmartScreen"): Mais informacoes -> Executar mesmo assim.

Comandos diretos (para quem quiser): OSMbot.exe ativo --simular | ativo --sem-anuncios | status | treinos | slots
"""


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


def build(make_zip: bool, make_installer: bool = False, icon: Path = ICON) -> None:
    if sys.platform != "win32":
        raise SystemExit("Este script constroi a versao Windows; corre-o no Windows.")
    if OUT.exists():
        shutil.rmtree(OUT)
    app_dir = OUT / "app"
    OUT.mkdir(parents=True)

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
        "playwright", "certifi")

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
