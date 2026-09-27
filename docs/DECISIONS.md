# Decisões

Formato: `D-NNN · Título · Estado · Data`. Estados: **Aceite**, **Em aberto**, **Substituída por D-NNN**.

## Aceites

### D-000 · "OSM" = Online Soccer Manager · Aceite · 2026-09-27
O projeto é um bot para o jogo Online Soccer Manager (Gamebasics). Não é OpenStreetMap nem Online Scout Manager.
**Porquê:** confirmado pelo utilizador; a sigla é ambígua e a pesquisa mistura os três.

### D-005 · Manter fase de descoberta antes de escolher stack · Aceite · 2026-09-27
Nenhum código nem escolha de linguagem até fechar D-002 e D-004.
**Porquê:** pedido explícito do utilizador ("antes de decidirmos linguagem, alcance, etc, quero ver o que é possível").

### D-009 · Propósito: codificar a teoria de jogo do dono · **Substituída por D-010** · 2026-09-27
Hipótese inicial: o bot serve para codificar a teoria do dono (táticas, transferências, capitães/roles). O dono esclareceu de seguida que a teoria já é conhecida por ele, não há nada a testar, e a parte tática tem pouco a automatizar.

### D-010 · Propósito: automatizar tarefas repetitivas (coins, treinos, transferências) · Aceite · 2026-09-27
O bot existe para poupar tempo ao dono: (1) obter coins via vídeos promocionais, (2) encurtar treinos, (3) tudo o que se consiga cortar em vídeos promocionais, (4) possivelmente parte das transferências. Táticas ficam fora do alcance inicial.
**Porquê:** declarado pelo dono. **Implicação:** o alcance é A3/A4 (ações autónomas com escrita na conta) — o nível de maior conflito com os ToS e de maior risco de ban. Ver `RISKS_AND_COMPLIANCE.md`. D-004 (postura de risco) passa a bloqueante.

### D-011 · Construir de raiz, `osm-ad-bot` só como referência · Aceite · 2026-09-27
Não adaptamos nem copiamos o repo `nsozturk/osm-ad-bot`; usamo-lo como especificação (mapa da API, lógica dos treinos). Escrevemos o nosso código.
**Porquê:** sem LICENSE (não se pode copiar para repo público), pode estar desatualizado, é macOS-cêntrico, e a política de seleção deve ser a do dono. Ver `PRIOR_ART.md`.

### D-013 · Contacto com o jogo real adiado · Aceite · 2026-09-27
D-004 (conta e postura de risco) não precisa de estar fechada já. Até ser decidida, só se trabalha em coisas que **não tocam no jogo**: arquitetura, lógica pura (políticas de treino/transferência), testes com dados sintéticos. Verificação de endpoints e login só depois de D-004 e com OK explícito.
**Porquê:** o dono perguntou se tinha de decidir já; não é necessário para avançar.

### D-001 · Linguagem: Python · Aceite · 2026-09-27
Python ≥ 3.11 (testado em 3.12), layout `src/`, testes com pytest. Sem dependências de runtime por agora; `httpx` entra quando houver cliente de API.
**Porquê:** recomendação aceite pelo dono; prior art em Python; Playwright disponível se um dia se avançar para anúncios.

### D-003 · Idioma: docs em PT-PT, código em inglês · Aplicada (provisória) · 2026-09-27
Identificadores, docstrings e testes em inglês (convenção para um repo público); docs em `docs/` em português europeu. Mensagens de commit e README público por decidir.
**Porquê:** assumido por nós ao começar a escrever código; o dono pode inverter.

## Em aberto

| ID | Decisão | Depende de | Notas |
|---|---|---|---|
| D-012 | Anúncios: incluir ou não, e como | D-004 | O repo forja callbacks de recompensa; **não vamos replicar isso**. Ver `PRIOR_ART.md` |
| D-002 | Alcance (A0–A4) | D-004 | Ver `OPTIONS.md` §A |
| D-004 | Postura de risco face aos ToS | — | Ver `RISKS_AND_COMPLIANCE.md` |
| D-006 | Interface (CLI/Discord/Telegram/web/lib) | D-002 | |
| D-007 | Licença do repo | D-004 | Relevante se o destino for GitHub público |
| D-008 | Git / repo no GitHub | — | **Do dono.** Ele faz commits, pulls e tudo o que é git/GitHub. O Claude só ajuda com mensagens de commit e versões quando pedido |
