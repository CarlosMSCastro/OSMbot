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

Com ``--assemblyai`` a transcrição é feita nos servidores da AssemblyAI (o áudio é enviado para lá) e não precisa da
placa gráfica: a chave ``ASSEMBLYAI_API_KEY`` vem do ``.env.local`` (fora do git). Os downloads continuam um a um;
só as transcrições correm em paralelo. Sem o Modo Carreira por omissão (``--carreira`` para o incluir). Antes de
começar mostra o custo estimado e pergunta (``--sim`` para não perguntar). O crédito é único e não renova (2026-10-19).

    python tools/osmpro_whisper.py --assemblyai --max 1
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
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "OSMPro"
OUT = ROOT / "_kb" / "legendas"
FIRST = ["Dicas", "Táticas", 'Série "Não te esqueças da tática!"', "Atualizações do jogo", "Curiosidades", "OSMPROworld"]
MODEL = "medium"
FAILS_BEFORE_PAUSE, PAUSE = 5, 15 * 60  # downloads failing in a row: wait, then go on (twice in a row: stop)
API = "https://api.assemblyai.com/v2"
PRICE_HOUR = 0.21  # USD per audio hour, the dearer of the base models (Universal-2 is 0.15): the estimate errs high
WORKERS, GAP = 4, 5  # transcriptions at once; seconds between downloads


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


def seconds(duration: str) -> int:
    total = 0
    for part in duration.split(":"):
        total = total * 60 + int(part or 0)
    return total


def api_key() -> str:
    for name in (".env.local", ".env"):
        path = REPO / name
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                key, _, value = line.partition("=")
                if key.strip() == "ASSEMBLYAI_API_KEY" and value.strip():
                    return value.strip().strip('"')
    return os.environ.get("ASSEMBLYAI_API_KEY", "")


def call(key: str, method: str, url: str, body: bytes | dict | None = None) -> dict:
    headers = {"authorization": key}
    if isinstance(body, dict):
        body, headers["content-type"] = json.dumps(body).encode(), "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read())


def assemblyai(key: str, video: dict, audio: Path) -> dict:
    """Upload, ask for the transcript, wait for it; the lines are AssemblyAI's sentences. The audio is deleted here."""
    try:
        upload = call(key, "POST", f"{API}/upload", audio.read_bytes())["upload_url"]
    finally:
        audio.unlink(missing_ok=True)
    language = {"language_code": "pt"} if video["canal"] == "andresantana" else {"language_detection": True}
    job = call(key, "POST", f"{API}/transcript", {"audio_url": upload, **language})
    while job["status"] not in ("completed", "error"):
        time.sleep(5)
        job = call(key, "GET", f"{API}/transcript/{job['id']}")
    if job["status"] == "error":
        raise RuntimeError(job.get("error"))
    sentences = call(key, "GET", f"{API}/transcript/{job['id']}/sentences")["sentences"]
    lines = [{"text": s["text"], "start": round(s["start"] / 1000, 2), "duration": round((s["end"] - s["start"]) / 1000, 2)}
             for s in sentences]
    return {**video, "lingua": job.get("language_code") or "pt", "automatica": True,
            "fonte": f"assemblyai {job.get('speech_model') or ''}".strip(), "linhas": lines}


def run_assemblyai(rows: list[dict], arguments) -> None:
    key = api_key()
    if not key:
        sys.exit("Falta a ASSEMBLYAI_API_KEY no .env.local")
    if arguments.max:
        rows = rows[:arguments.max]
    hours = sum(seconds(r["duracao"]) for r in rows) / 3600
    print(f"{len(rows)} vídeos · {hours:.1f} h de áudio · ~{hours * PRICE_HOUR:.2f} $ (no máximo, a {PRICE_HOUR} $/h)",
          flush=True)
    if not arguments.sim and input("Continuar? [s/N] ").strip().lower() not in ("s", "sim"):
        return
    done = fails = pauses = 0

    def finish(video: dict, audio: Path, started: float) -> None:
        nonlocal done
        try:
            data = assemblyai(key, video, audio)
        except Exception as error:
            print(f"  transcrição falhou ({video['id']}): {type(error).__name__}: {error}", flush=True)
            return
        (OUT / f"{video['id']}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        done += 1
        print(f"[{done}] {video.get('categoria') or 'OSMPROworld'} · {video['titulo'][:60]} · {video['duracao']} "
              f"em {time.time() - started:.0f} s", flush=True)

    with tempfile.TemporaryDirectory(prefix="osmpro-") as temp, ThreadPoolExecutor(WORKERS) as pool:
        folder = Path(temp)
        for n, video in enumerate(rows, 1):
            started = time.time()
            audio = download(video, folder)
            if not audio:
                fails += 1
                if fails >= FAILS_BEFORE_PAUSE:
                    pauses += 1
                    if pauses >= 2:
                        print("  o YouTube continua a falhar depois da pausa: paro", flush=True)
                        break
                    print(f"  {fails} falhas seguidas a descarregar: pausa de {PAUSE // 60} min", flush=True)
                    time.sleep(PAUSE)
                    fails = 0
                continue
            fails = pauses = 0
            print(f"  áudio {n}/{len(rows)}: {video['id']}", flush=True)
            pool.submit(finish, video, audio, started)
            time.sleep(GAP)
    print(f"FIM: {done} transcritos", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--max", type=int, default=0, help="parar ao fim de N vídeos transcritos")
    parser.add_argument("--modelo", default=MODEL, help="modelo do Whisper (por omissão: medium)")
    parser.add_argument("--assemblyai", action="store_true", help="transcrever na AssemblyAI em vez do Whisper")
    parser.add_argument("--carreira", action="store_true", help="com a AssemblyAI, incluir o Modo Carreira")
    parser.add_argument("--sim", action="store_true", help="com a AssemblyAI, não perguntar antes de começar")
    arguments = parser.parse_args()
    if arguments.assemblyai:
        OUT.mkdir(parents=True, exist_ok=True)
        rows = [r for r in videos() if not (OUT / f"{r['id']}.json").exists()
                and (arguments.carreira or not (r.get("categoria") or "").startswith("Modo Carreira"))]
        return run_assemblyai(rows, arguments)
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
