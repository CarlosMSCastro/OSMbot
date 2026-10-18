"""Legendas de todos os vídeos das listas do OSMPro -> OSMPro/_kb/legendas/<id>.json (D-063). Retoma onde parou.

Prefere as legendas feitas pelo autor (português, depois inglês) às automáticas. Um vídeo sem legendas fica com
``erro``; para os tentar outra vez, apagar esses ficheiros. Pausa de 20-40 s entre vídeos (com 3-6 s o YouTube
bloqueou o IP ao fim de ~20 vídeos, 2026-10-17). Num bloqueio espera 1 h e tenta outra vez; ao 6.º seguido para
(correr outra vez mais tarde). ~1180 vídeos = 8-12 h: deixar a correr de noite.

    python -m pip install youtube-transcript-api
    python tools/osmpro_legendas.py
"""
import csv, json, random, re, sys, time
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "OSMPro"
out = root / "_kb" / "legendas"
out.mkdir(parents=True, exist_ok=True)
api = YouTubeTranscriptApi()
rows = []
for name in ("osmproworld.csv", "andresantana.csv"):
    for r in csv.DictReader((root / name).open(encoding="utf-8")):
        m = re.search(r"(?:v=|shorts/)([\w-]{11})", r["link"])
        if m:
            rows.append({**r, "id": m.group(1), "canal": name[:-4]})
blocked = 0
for i, r in enumerate(rows, 1):
    target = out / f"{r['id']}.json"
    if target.exists():
        continue
    try:
        tl = list(api.list(r["id"]))
        pick = sorted(tl, key=lambda t: (t.is_generated, not t.language_code.startswith("pt"),
                                         not t.language_code.startswith("en")))[0]
        lines = pick.fetch().to_raw_data()
        data = {**r, "lingua": pick.language_code, "automatica": pick.is_generated, "linhas": lines}
        blocked = 0
    except Exception as e:
        kind = type(e).__name__
        if "Block" in kind or "TooMany" in kind or "RequestBlocked" in kind:
            blocked += 1
            print(f"[{i}/{len(rows)}] BLOQUEIO {kind}; pausa", flush=True)
            if blocked >= 6:
                print("PARADO: o YouTube está a bloquear. Retomar mais tarde.", flush=True)
                break
            time.sleep(3600)
            continue
        data = {**r, "erro": kind}
    target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    if i % 25 == 0:
        print(f"[{i}/{len(rows)}] ok", flush=True)
    time.sleep(random.uniform(20, 40))
done = list(out.glob("*.json"))
print("FIM:", len(done), "de", len(rows))
