# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-PT/1.1.0/); versões segundo [SemVer](https://semver.org/lang/pt-BR/) (`0.x` até haver automação estável).

Este ficheiro é o **histórico de versões, para quem lê o repo**. O diário interno de cada sessão de trabalho está em [`docs/WORKLOG.md`](docs/WORKLOG.md).

## [Por lançar]

## [0.1.0] — 2026-09-27

Âmbito e postura de risco definidos. **Continua sem nenhum acesso ao jogo.**

### Decidido
- Alcance (D-002): automação até **A3** (treinos, transferências) já, e **A4** (anúncios) também aceite.
- Postura de risco (D-004): risco de ban aceite conscientemente pelo dono; testes começam em conta secundária.
- Anúncios (D-012): sem servidor dedicado — corre nas máquinas do dono conforme ligadas, sempre a respeitar os limites do jogo, sem horário fixo.
- Interface (D-006): CLI fina sobre a biblioteca existente, com arranque automático por máquina.
- Licença (D-007): nenhuma (todos os direitos reservados); disclaimer de risco reforçado no `README.md`.

### Investigado
- `docs/DISCOVERY.md`: deteção e histórico de bans no OSM (device ban; precedente de junho de 2026 sobre exceder limites via bug — não sobre automatizar dentro deles).

## [0.0.1] — 2026-09-27

Primeira versão: **documentação e lógica pura. Não há nenhum acesso ao jogo.**

### Adicionado
- Documentação de contexto: `CLAUDE.md`, `README.md` e `docs/` (`PROJECT_BRIEF`, `DISCOVERY`, `PRIOR_ART`, `OPTIONS`, `DECISIONS`, `RISKS_AND_COMPLIANCE`, `GLOSSARY`, `WORKLOG`).
- `docs/THEORY.md`: a metodologia de jogo do dono (tática, especialistas, treinos, transferências, estádio, patrocinadores, vídeos, poupança).
- Projeto Python (`pyproject.toml`, layout `src/`) com lógica pura, sem I/O:
  - `osmbot.models`: `Player`, `Position`.
  - `osmbot.theory.tactics`: escolha de formação, sliders, desarme.
  - `osmbot.theory.specialists`: capitão, penáltis, livres, cantos.
  - `osmbot.training.policy`: quem treinar em cada slot.
- 44 testes (pytest) com dados sintéticos.
- `.gitignore` que exclui credenciais, sessões, HARs e dados recolhidos.
