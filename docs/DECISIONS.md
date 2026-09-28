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

### D-013 · Contacto com o jogo real adiado · Aceite · 2026-09-27 · **Encerrada 2026-09-28**
D-004 (conta e postura de risco) não precisa de estar fechada já. Até ser decidida, só se trabalha em coisas que **não tocam no jogo**: arquitetura, lógica pura (políticas de treino/transferência), testes com dados sintéticos. Verificação de endpoints e login só depois de D-004 e com OK explícito.
**Porquê:** o dono perguntou se tinha de decidir já; não é necessário para avançar.
**Encerramento (2026-09-28):** o dono deu OK explícito nesta sessão para contacto real com o jogo (login e leitura), conforme exige a regra 5 do `CLAUDE.md`. A partir daqui o trabalho pode tocar no jogo (conta principal, ver D-004 emendada), começando por login e leitura, antes de qualquer ação de escrita.

### D-001 · Linguagem: Python · Aceite · 2026-09-27
Python ≥ 3.11 (testado em 3.12), layout `src/`, testes com pytest. Sem dependências de runtime por agora; `httpx` entra quando houver cliente de API.
**Porquê:** recomendação aceite pelo dono; prior art em Python; Playwright disponível se um dia se avançar para anúncios.

### D-003 · Idioma: docs em PT-PT, código em inglês · Aplicada (provisória) · 2026-09-27
Identificadores, docstrings e testes em inglês (convenção para um repo público); docs em `docs/` em português europeu. Mensagens de commit e README público por decidir.
**Porquê:** assumido por nós ao começar a escrever código; o dono pode inverter.

### D-004 · Postura de risco face aos ToS · Aceite · 2026-09-27 · **Emendada 2026-09-28**
O dono aceita o risco de ban ao nível **A3** (ações automáticas: treinos e transferências) desde já, e **A4** (anúncios) quando D-012 estiver decidida.
**Emenda (2026-09-28):** o plano original de começar numa conta secundária foi substituído — o dono decidiu conscientemente começar já pela **conta principal**, sem conta de teste. Fica registado que isto expõe a conta principal diretamente ao risco descrito abaixo (não há isolamento de "conta descartável").
**Porquê (original):** decisão consciente do dono, informado do precedente de junho 2026 (contas banidas por volume anómalo de vídeos mesmo sendo um bug do jogo, não intenção maliciosa) e de que a deteção tende a olhar para o **padrão de comportamento** (timing, ausência de eventos reais de rato/teclado), não só para o volume. Ver `DISCOVERY.md` §5.

### D-002 · Alcance (A0–A4) · Aceite · 2026-09-27
Alcance = **A3** para treinos e transferências (ações automáticas, escrita na conta). **A4** (ver anúncios) fica dependente de D-012 — não por risco, mas por infraestrutura (precisa de algo sempre online: servidor próprio ou Raspberry Pi, que o dono não quer pagar por agora).
**Porquê:** decorre de D-010 (propósito) e D-004 (risco aceite).

### D-012 · Anúncios (A4): incluir, sem servidor dedicado · Aceite · 2026-09-27
O bot vê anúncios **sempre a respeitar os limites do próprio jogo** (nunca exceder tetos tipo "4/hora"; nunca forjar callbacks de recompensa — isso fica excluído por completo, regra 8 do `CLAUDE.md`). Corre nas máquinas do dono conforme estiverem ligadas — **PC pessoal, MacBook, PC da empresa** (este último sob controlo do próprio dono, que é o IT da empresa, logo sem o risco de política de TI de terceiros) — **sem horário fixo codificado** e **sem servidor/Raspberry Pi/dispositivo dedicado**. Dentro das horas em que uma máquina está ligada, salta propositadamente algumas janelas de anúncio (não tenta 100%) com timings aleatórios entre cliques, para não ter uma disponibilidade "perfeita demais".
**Porquê:** ver `DISCOVERY.md` §5 e `RISKS_AND_COMPLIANCE.md` — o único precedente de ban conhecido (jun. 2026) foi por **exceder** o teto do jogo via bug, não por automatizar dentro dos limites; essa segunda situação continua **desconhecida** (nem confirmada nem afastada), daí a mitigação de variar o padrão em vez de o maximizar. **Percentagem alvo de janelas apanhadas: por afinar quando construirmos** (ordem de grandeza 60-70%, não é definitivo).

### D-006 · Interface: CLI fina + biblioteca · Aceite · 2026-09-27
`osmbot/` continua biblioteca pura; uma CLI fina chama as suas funções (`osmbot treinos --aplicar`, etc.). Para correr "sozinho", cada máquina arranca o processo automaticamente ao ligar/sessão iniciar (Windows: Task Scheduler/Startup; macOS: LaunchAgent) e ele fica ativo enquanto a máquina estiver ligada — sem horário fixo, adapta-se aos ritmos reais do dono.
**Porquê:** uso é só pessoal (sem necessidade de Discord/Telegram/web); Python (D-001) já é multi-plataforma; evita custo/complexidade de servidor.

### D-007 · Licença do repo: nenhuma (todos os direitos reservados) · Aceite · 2026-09-27
Sem ficheiro `LICENSE`. O repo fica público e visível, mas sem autorização legal para terceiros copiarem/reutilizarem/redistribuírem o código. Adicionado disclaimer de risco em `README.md`.
**Porquê:** o dono não está preocupado com apropriação de ideias (baixa visibilidade do seu GitHub), mas o bot é para uso **só dele** (D-002); "sem licença" é mais coerente com essa intenção do que MIT, que convidaria à redistribuição como ferramenta. Diferença prática pequena — o risco de ban (D-004) depende do que o dono corre contra o OSM, não da licença do código.

## Em aberto

| ID | Decisão | Depende de | Notas |
|---|---|---|---|
| D-008 | Git / repo no GitHub | — | **Do dono.** Ele faz commits, pulls e tudo o que é git/GitHub. O Claude só ajuda com mensagens de commit e versões quando pedido |
