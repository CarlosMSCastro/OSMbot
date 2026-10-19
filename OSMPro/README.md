# OSMPro

Vídeos de OSM de dois canais portugueses, para estudar (pedido do dono, 2026-10-16). Listas lidas com o `yt-dlp`, sem descarregar vídeos.

| Canal | Ficheiros | Vídeos de OSM |
|---|---|---|
| [@OSMPROworld](https://www.youtube.com/@OSMPROworld) (em inglês) | [osmproworld.md](osmproworld.md) · `osmproworld.csv` | 43 (27 vídeos, 16 shorts) |
| [@andresantana_yt](https://www.youtube.com/@andresantana_yt) (em português, OSM PRO) | [andresantana.md](andresantana.md) · `andresantana.csv` | 1136 de 1445 (o resto não é de OSM) |

## Estudo (D-063)

- `_kb/legendas/<id>.json`: o texto de cada vídeo, transcrito no PC com o Whisper (`tools/osmpro_whisper.py`, teoria primeiro; retoma onde parou). As primeiras 30 vieram das legendas do YouTube (`tools/osmpro_legendas.py`), que bloqueia ao fim de ~15 vídeos.
- `_kb/notas/<id>.md`: as conclusões de cada vídeo, 1 a 1, comparadas com `docs/THEORY.md`.
- `_kb/ESTADO.md`: o que está transcrito e analisado, por vídeo e por categoria. Gerado por `tools/osmpro_estado.py`; não editar à mão.
