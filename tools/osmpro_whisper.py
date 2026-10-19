"""Transcrição dos vídeos do OSMPro com o Whisper, no próprio PC -> OSMPro/_kb/legendas/<id>.json (D-063). Retoma onde parou.

Porquê: o YouTube bloqueia as legendas (``IpBlocked``/429) ao fim de 12-18 vídeos por IP, com pausa ou sem ela; o
áudio continua a descarregar (2026-10-18). Por isso: só o áudio com o ``yt-dlp`` (numa pasta temporária, apagado logo
a seguir; nunca vai para o repo) e a transcrição com o ``faster-whisper`` na placa gráfica (GTX 1060: ~6 x o tempo
real com o modelo ``medium``; sem placa NVIDIA usa o processador, muito mais devagar).

Ordem: as categorias de teoria primeiro (Dicas, Táticas, "Não te esqueças da tática!", Atualizações, Curiosidades,
o canal inglês), depois o resto. Os vídeos que já têm legendas ficam como estão.

    python -m pip install faster-whisper "yt-dlp[default]" deno nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
    python tools/osmpro_whisper.py            # tudo, pela ordem
    python tools/osmpro_whisper.py --max 5    # só 5 (para testar)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "OSMPro"
OUT = ROOT / "_kb" / "legendas"
FIRST = ["Dicas", "Táticas", 'Série "Não te esqueças da tática!"', "Atualizações do jogo", "Curiosidades", "OSMPROworld"]
MODEL = "medium"
FAILS_BEFORE_PAUSE, PAUSE = 5, 15 * 60  # downloads failing in a row: wait, then go on


def cuda_dlls() -> None:
    """On Windows, the CUDA 12 libraries come from the nvidia-* pip packages; CTranslate2 must find their DLLs."""
    if sys.platform != "win32":
        return
    try:
        import nvidia.cublas
        import nvidia.cudnn
    except ImportError:
        return
    for package in (nvidia.cublas, nvidia.cudnn):
        folder = Path(list(package.__path__)[0]) / "bin"
        if folder.is_dir():
            os.add_dll_directory(str(folder))
            os.environ["PATH"] = str(folder) + os.pathsep + os.environ["PATH"]


def videos() -> list[dict]:
    rows = []
    for name in ("osmproworld.csv", "andresantana.csv"):
        for row in csv.DictReader((ROOT / name).open(encoding="utf-8")):
            found = re.search(r"(?:v=|shorts/)([\w-]{11})", row["link"])
            if found:
                rows.append({**row, "id": found.group(1), "canal": name[:-4]})
    rank = {category: n for n, category in enumerate(FIRST)}
    return sorted(rows, key=lambda r: rank.get(r.get("categoria") or "OSMPROworld", len(FIRST)))  # stable: list order inside


def download(video: dict, folder: Path) -> Path | None:
    env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]}  # deno for yt-dlp
    done = subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "-f", "ba[ext=m4a]/ba",
                           "-o", str(folder / "%(id)s.%(ext)s"), video["link"]], capture_output=True, text=True, env=env)
    found = list(folder.glob(f"{video['id']}.*"))
    if done.returncode or not found:
        print(f"  áudio falhou: {(done.stderr or '').strip()[-200:]}", flush=True)
        return None
    return found[0]


def pcm(path: Path):
    """The audio as 16 kHz mono floats, decoded by ffmpeg (PyAV in some versions breaks faster-whisper's own decoding)."""
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--max", type=int, default=0, help="parar ao fim de N vídeos transcritos")
    parser.add_argument("--modelo", default=MODEL, help="modelo do Whisper (por omissão: medium)")
    arguments = parser.parse_args()
    cuda_dlls()
    from faster_whisper import WhisperModel

    try:
        model, device = WhisperModel(arguments.modelo, device="cuda", compute_type="int8"), "cuda"
    except Exception:  # no NVIDIA card (e.g. the Mac): the processor
        model, device = WhisperModel(arguments.modelo, device="cpu", compute_type="int8"), "cpu"
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in videos() if not (OUT / f"{r['id']}.json").exists()]
    print(f"{len(rows)} por fazer · Whisper {arguments.modelo} ({device})", flush=True)
    done = fails = 0
    with tempfile.TemporaryDirectory(prefix="osmpro-") as temp:
        folder = Path(temp)
        for n, video in enumerate(rows, 1):
            started = time.time()
            audio = download(video, folder)
            if not audio:
                fails += 1
                if fails >= FAILS_BEFORE_PAUSE:
                    print(f"  {fails} falhas seguidas a descarregar: pausa de {PAUSE // 60} min", flush=True)
                    time.sleep(PAUSE)
                    fails = 0
                continue
            fails = 0
            try:
                language = "pt" if video["canal"] == "andresantana" else None  # the English channel: let Whisper tell
                segments, info = model.transcribe(pcm(audio), language=language, vad_filter=True, beam_size=1)
                lines = [{"text": s.text.strip(), "start": round(s.start, 2), "duration": round(s.end - s.start, 2)}
                         for s in segments]
                data = {**video, "lingua": info.language, "automatica": True, "fonte": f"whisper {arguments.modelo}",
                        "linhas": lines}
            except Exception as error:
                print(f"  transcrição falhou: {type(error).__name__}: {error}", flush=True)
                continue
            finally:
                audio.unlink(missing_ok=True)
            (OUT / f"{video['id']}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            done += 1
            print(f"[{n}/{len(rows)}] {video.get('categoria') or 'OSMPROworld'} · {video['titulo'][:60]} · "
                  f"{video['duracao']} em {time.time() - started:.0f} s", flush=True)
            if arguments.max and done >= arguments.max:
                break
    print(f"FIM: {done} transcritos", flush=True)


if __name__ == "__main__":
    main()
