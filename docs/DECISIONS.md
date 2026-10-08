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

### D-014 · Autonomia do Claude no contacto com o jogo · Aceite · 2026-10-05
Substitui o "OK por sessão" da regra 5 por três níveis (texto na regra 5 do `CLAUDE.md`): **livre** (leitura), **autónomo com o bot ativo** (`recolher`/`treinar`, sem teto de ações), **pede OK** (escritas novas ou potencialmente abusivas). Em desenvolvimento o Claude não escreve na conta. `recolher`/`treinar` devem passar a escrever por omissão, com `--simular` para ver sem escrever (o dono escolheu isto em 2026-10-05).
**Estado da implementação:** feito em 2026-10-05 depois de o dono acrescentar `.claude/settings.json` (a 1.ª tentativa tinha sido bloqueada pelo sistema de permissões). `recolher`/`treinar` escrevem por omissão; `--simular` é o ensaio; `--confirmar` ficou como alias escondido sem efeito.
**Porquê:** o dono quer um Claude mais útil e autónomo; o risco de ban na conta principal (D-004) mantém-se, por isso as escritas novas continuam a pedir OK.

### D-015 · Interface: quadro de consola, sem browser · Aceite · 2026-10-05
O `osmbot ativo` mostra um **quadro fixo na consola** que se redesenha sozinho (estado, contagem decrescente, 2 clubes com os 8 treinos, boss coins, estado dos anúncios, últimas linhas do registo, aviso de slot livre). Sem página web, sem botões: pára-se com Ctrl+C; `--sem-quadro` volta às linhas simples (também é o que acontece quando a saída não é um terminal). Sem dependências novas. O bot **acorda** no mais próximo de: fim do próximo treino, reposição dos vídeos da loja, reposição dos vídeos de treino (e, quando existirem, dos de dinheiro), com um máximo de 30 min.
**Porquê:** o dono quer algo simples, de consola (já decidido em 2026-09-28: consola visível); um servidor local e uma página seriam mais peças a manter. Substitui a parte "interface" da D-006 (o arranque continua manual, uma máquina de cada vez). Um desenho em browser foi feito e descartado.
**Substituída em parte por D-024 (2026-10-08):** a interface principal passa a ser uma janela (PySide6); o quadro de consola continua em `osmbot menu` e `osmbot ativo`.

### D-016 · Distribuição: pasta portátil só para Windows · Aceite · 2026-10-05
Versão **portátil** para Windows: uma pasta (ou .zip) com o Python embutido oficial, as dependências, o Firefox do Playwright e **`OSMbot.exe` (um `python.exe` oficial, assinado pela PSF, com outro nome; o `app/sitecustomize.py` faz-lhe abrir o menu na consola; sem `.bat`, por isso sem o "Terminate batch job")** (iniciar o bot, sem anúncios, estado, ensaio, login). O mesmo menu abre com `osmbot` sem argumentos. Não instala nada; copia-se para outro PC. Construída por `python tools/build_portable.py [--zip]` (sai para `dist/`, ignorado pelo git). Sem PyInstaller: evita falsos positivos de antivírus (o executável é o do próprio Python) e atualizar é só reconstruir/copiar a pasta. A raiz da pasta tem os ficheiros do runtime ao lado do `OSMbot.exe` (o executável tem de estar junto das DLL). O **Mac** continua com o ambiente de desenvolvimento (`git pull` + venv); um pacote para Mac exigiria assinar a app. **Instalador** (2026-10-05): `python tools/build_portable.py --zip --installer` gera também `dist/OSMbot-Setup.exe` (Inno Setup 6, `tools/installer.iss`): instala por utilizador em `%LOCALAPPDATA%\OSMbot` (sem administrador), cria atalho no menu Iniciar (e opcionalmente no ambiente de trabalho) com o ícone do OSM, e tem desinstalador. A sessão em `~/.osmbot` nunca é tocada. O ícone dos atalhos é um **desenho original** (`tools/make_icon.py` → `tools/assets/osmbot.ico`, uma bola de futebol); o ícone oficial do jogo (arte da Gamebasics) só se usa numa cópia pessoal com `--icone tools/local/osmbot.ico` (`tools/local/` está no `.gitignore`). O `.exe` assinado não é alterado (mudar-lhe o ícone invalidaria a assinatura).
**Publicação (2026-10-05):** o dono escolheu repo **e** Release públicos, ciente dos riscos (identidade ligada ao bot, deteção por popularidade, termos do jogo, pedidos de remoção). Medidas tomadas: documentos, testes e código sem nomes de clubes, ligas, jogadores ou utilizadores de terceiros (termos genéricos); instalador sem arte do jogo; nenhum segredo nem sessão no pacote. **Limite:** o histórico do git já enviado contém os nomes antigos (2 commits); reescrevê-lo é uma decisão do dono (git é dele, regra 9).
**Sessão:** continua por máquina (`~/.osmbot`), nunca vai no pacote; em cada PC faz-se a opção *Login* do menu uma vez.

### D-017 · Histórico do git com os nomes antigos · Aceite · 2026-10-06
O repo é público e 2 commits antigos do histórico contêm nomes de clubes e jogadores do dono (o estado atual do repo está limpo, verificado com `git grep` em `origin/main`). O dono **aceita** deixar o histórico como está, sem o reescrever nem recriar o repo.
**Porquê:** o dono pesou o risco (identidade ligada ao bot, D-016) e preferiu a simplicidade; reescrever o histórico mexeria em commits já enviados e quem já clonou ficaria com a versão antiga.

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
*(Janelas saltadas: só na loja desde 2026-10-08, ver D-021.)*
O bot vê anúncios **sempre a respeitar os limites do próprio jogo** (nunca exceder tetos tipo "4/hora"; nunca forjar callbacks de recompensa — isso fica excluído por completo, regra 8 do `CLAUDE.md`). Corre nas máquinas do dono conforme estiverem ligadas — **PC pessoal, MacBook, PC da empresa** (este último sob controlo do próprio dono, que é o IT da empresa, logo sem o risco de política de TI de terceiros) — **sem horário fixo codificado** e **sem servidor/Raspberry Pi/dispositivo dedicado**. Dentro das horas em que uma máquina está ligada, salta propositadamente algumas janelas de anúncio (não tenta 100%) com timings aleatórios entre cliques, para não ter uma disponibilidade "perfeita demais".
**Porquê:** ver `DISCOVERY.md` §5 e `RISKS_AND_COMPLIANCE.md` — o único precedente de ban conhecido (jun. 2026) foi por **exceder** o teto do jogo via bug, não por automatizar dentro dos limites; essa segunda situação continua **desconhecida** (nem confirmada nem afastada), daí a mitigação de variar o padrão em vez de o maximizar. **Percentagem alvo de janelas apanhadas: por afinar quando construirmos** (ordem de grandeza 60-70%, não é definitivo).

### D-006 · Interface: CLI fina + biblioteca · Aceite · 2026-09-27 · **Interface e arranque substituídos por D-015**
`osmbot/` continua biblioteca pura; uma CLI fina chama as suas funções (`osmbot treinos --aplicar`, etc.). Para correr "sozinho", cada máquina arranca o processo automaticamente ao ligar/sessão iniciar (Windows: Task Scheduler/Startup; macOS: LaunchAgent) e ele fica ativo enquanto a máquina estiver ligada — sem horário fixo, adapta-se aos ritmos reais do dono.
**Porquê:** uso é só pessoal (sem necessidade de Discord/Telegram/web); Python (D-001) já é multi-plataforma; evita custo/complexidade de servidor.

### D-007 · Licença do repo: nenhuma (todos os direitos reservados) · Aceite · 2026-09-27
Sem ficheiro `LICENSE`. O repo fica público e visível, mas sem autorização legal para terceiros copiarem/reutilizarem/redistribuírem o código. Adicionado disclaimer de risco em `README.md`.
**Porquê:** o dono não está preocupado com apropriação de ideias (baixa visibilidade do seu GitHub), mas o bot é para uso **só dele** (D-002); "sem licença" é mais coerente com essa intenção do que MIT, que convidaria à redistribuição como ferramenta. Diferença prática pequena — o risco de ban (D-004) depende do que o dono corre contra o OSM, não da licença do código.

### D-020 · Recompensas diárias automáticas (início de sessão, missões, vídeos acumulados) · Aceite · 2026-10-07
O bot reclama sozinho, no modo ativo: a recompensa de início de sessão, as 3 missões diárias e a recompensa do dia (**sempre "guardar"**, nunca gasta), e a recompensa dos vídeos acumulados (também para o inventário). Regras em `THEORY.md` §17. Passam para o nível "autónomo com o bot ativo" da regra 5 (D-014), juntamente com `recolher` e `treinar`. Nunca se usam itens do inventário.
**Porquê:** pedido do dono, depois de ver os pedidos reais (`inspect-writes`, 2026-10-07) e de aceitar o risco (D-004). São cliques que o dono já dá à mão, dentro dos limites do jogo.

### D-019 · O bot não pára à primeira falha · Aceite · 2026-10-08
- **Escrita dos treinos falhou** (p. ex. o dono recolheu o mesmo treino à mão): o bot regista, volta a ver 10 min depois (lê o jogo de novo) e só pára se falhar em **3 passagens seguidas**.
- **Sem rede:** novas tentativas com pausas cada vez maiores (1, 2, 5, 10 e depois 15 min); só pára ao fim de **6 h** sem rede.
- **Vídeos de um tipo que falham sempre** (loja, treino, dinheiro): esse tipo espera cada vez mais (10, 20, 40 e depois 60 min); os outros continuam.
- Sessão perdida (`osmbot login`) continua a parar logo, porque só o dono resolve.
**Porquê:** o dono deixa o bot sozinho na fábrica o dia todo; uma falha pontual ou 3 min sem rede deixavam-no parado até voltar ao PC.

### D-021 · Só a loja salta janelas; vídeos de treino e de dinheiro vêem-se sempre · Aceite · 2026-10-08
Substitui D-012 **só na parte das janelas saltadas**. O salto ao acaso (15%) fica apenas nos vídeos da **loja** (boss coins). Os vídeos de **treino** (−2h) e de **dinheiro** vêem-se sempre que o jogo os deixa, na mesma passagem (com as pausas aleatórias de 20-75 s entre vídeos). O resto de D-012 mantém-se.
**Porquê:** dono, 2026-10-08: uma janela de treino saltada atrasava os −2h até à passagem seguinte (~40 min nesse caso); "os coins da loja é que podem demorar", o tempo de treino não.

### D-022 · O registo do bot vai para o repo, completo · Aceite · 2026-10-08
Cada linha do registo do bot vai também para `logs/<nome do PC>/AAAA-MM-DD.log` no repo (um ficheiro por PC e por dia, para não haver conflitos no git). **Completo, com os nomes dos clubes e jogadores**: exceção à regra de D-016 só para `logs/`, escolhida pelo dono ("não estou preocupado com isso"). O `~/.osmbot/bot.log` mantém-se. Segredos **nunca** (regra 6): tokens e e-mails são apagados antes de escrever. O bot não mexe no git (regra 9): commit e push são do dono. Pasta do repo: encontrada sozinha a correr do código; no bot instalado escolhe-se uma vez (menu "Pasta dos logs" / `osmbot pasta-logs`), o que copia também o registo antigo desse PC.
**Porquê:** o dono trabalha em várias máquinas (casa, fábrica, Mac) e quer analisar os logs de qualquer uma.

### D-023 · O bot encontra sozinho o repo para os logs · Aceite · 2026-10-08
Substitui D-022 **só na parte da pasta do repo**. O bot (código, portátil ou instalado) procura o repo sozinho: primeiro `OSMBOT_REPO` ou a pasta escolhida com `osmbot pasta-logs`, depois o código de onde corre, depois um repo OSMbot **ao lado da pasta do bot** ou na pasta pessoal, `Documents`, `Desktop` (também os do OneDrive); se houver vários, ganha o que se chama `OSMbot`. Na primeira linha de um PC copia também o `~/.osmbot/bot.log` antigo. A opção "Pasta dos logs" sai do menu; o comando `osmbot pasta-logs` fica só para um repo noutro sítio. O resto de D-022 mantém-se.
**Porquê:** dono, 2026-10-08: "os logs devem ficar no repo em cada uma das máquinas" sem ter de escolher a pasta; na fábrica o portátil corria em `Documents\osmbot-portable` e os logs ficavam só em `~/.osmbot`.

### D-024 · Interface em janela (PySide6), só Windows por agora · Aceite · 2026-10-08
O bot ganha uma janela de programa em **PySide6 (Qt)**, para a **0.9.0**. **Só Windows** por agora (o Mac fica para depois). **Sem telemóvel.** Mostra a mesma informação que o quadro da consola. Abre logo no quadro, com o bot parado e o botão Iniciar; o menu à parte desaparece. **Revisto pelo dono em 2026-10-08 (0.9.1):** abre pequena, num ecrã inicial com **Abrir · Login · Sair**. Abrir mostra um símbolo de carregamento, põe o bot a trabalhar e a mesma janela cresce para o quadro quando o jogo carrega. Não há barra de botões (Iniciar, Parar e Login ficam no menu Bot e no ícone). Os avisos e erros passam para Ver → Avisos e erros. O resumo da sessão passa a uma fila de números com legenda. O X com o bot parado fecha o programa. Estilo de programa de Windows, não de página web: tema escuro (Fusion), barra de título escura, logótipo, menu (Bot · Ver · Ajuda), barra de ferramentas (Iniciar, Parar, Login, Pasta dos logs), um painel por clube lado a lado, tabelas com cabeçalho, painel "Conta", tabela "Avisos e erros" pequena por omissão, barra de estado com a próxima verificação. A janela é redimensionável. **Fechar a janela (X)** esconde-a e o bot continua; para sair a sério usa-se Bot → Sair ou o ícone. **Ícone junto ao relógio:** o logótipo do OSMbot com uma bolinha **verde** a trabalhar e **cinzenta** parado; sem vermelho. Menu do ícone: Abrir, Iniciar/Parar, Sair. **Sem notificações do Windows** por agora. A consola continua disponível.
**Porquê:** o dono prefere uma janela a uma consola. O PySide6 junta janela, ícone e avisos num só pacote. Maquetes aprovadas pelo dono em 2026-10-08 ("Está melhor, sim").

### D-025 · Amigável e análise do adversário automáticos, 4 h antes do jogo · Aceite · 2026-10-08
No modo ativo, para **todas as equipas** da conta: quando faltarem 4 horas ou menos para o próximo jogo, se a checklist do jogo ainda não tiver amigável, o bot faz **1** (4 boss coins, adversário indiferente); se ainda não houver análise, envia o analista ao próximo adversário. Nunca antes das 4 h e nunca por cima do que o dono já fez. Regras em `THEORY.md` §6; pedidos observados com `inspect-writes` em `DISCOVERY.md` §3. Mais amigáveis por dia (talvez 5) ficam para depois.
**Porquê:** pedido do dono ("Podes avançar com o código"), que faz estes dois pontos sempre, mas quer as últimas horas livres para os confrontos diretos.

### D-026 · Quadro da janela revisto (0.9.3) · Aceite · 2026-10-08
Revê o aspeto de D-024; o resto de D-024 mantém-se. Respostas do dono, 2026-10-08:
- **Clubes em grelha 2×2** (até 4). **Cabeçalho:** logótipo do jogo, nome grande, faixa com a cor tirada do logótipo.
- **Próximo jogo:** adversário, (H) casa / (A) fora e hora. **Confronto direto** (adversário a 1 ou 2 lugares do clube na classificação): símbolo de perigo (`THEORY.md` §1).
- **Liga:** só a posição. **Taça:** a fase ("quartos-de-final", "eliminado nos oitavos"; o mesmo antes de começar e depois de ganhar). **Valor do plantel:** posição na liga, total e média por jogador; o jogo tem uma tabela junto à classificação e à lista de treinadores (por observar); até lá, soma do valor dos jogadores.
- **Lista de transferências:** só aparece com vaga livre ("1 vaga livre na lista de transferências", com ícone de importância).
- **Cansados** mantêm-se. **Pré-jogo** sempre visível, como checklist a completar. **Treinos** e **patrocinadores** ficam como estão.
- **Dinheiro:** uma linha (fundos + poupança). Por baixo, cada venda ("Jogador X vendido XX,X M") até o dono voltar a ocupar essa vaga da lista; se vender 3, mostra os 3. O valor é o preço da listagem (o dono: é o mesmo que entra no dinheiro).
- **Estádio:** uma linha, "Treinos 3/3 · Campo 1/3 ↑12h06 · Capacidade 0/3".
- **Parte de baixo** num só painel: boss coins em grande com o "+X" da sessão; contadores ("novos vídeos na loja", "acelerar treinos", dinheiro, troca de posição, diárias). **Sem** os números da sessão. Barra de estado só com o estado e o próximo evento.
- **Aspeto:** tema escuro, cores mais organizadas e simples, símbolos de perigo; títulos maiores, o resto quase igual. Menu de cima mantém-se.
- **Processo:** maquetes com os dados reais primeiro; código só depois de aprovadas. Versão 0.9.3 se ficar bom; 1.0 em breve.
- **Correções à 2.ª maqueta (dono, 2026-10-09):**
  - Liga, Taça e **"Valor do plantel"** centrados; o valor ocupa a metade direita do cartão.
  - Dinheiro alinhado com os outros valores; a venda aparece **à frente** do dinheiro, não por baixo.
  - Estádio em 2 linhas: em cima as partes paradas ("Treinos 3/3 · Capacidade 0/3"); em baixo a parte a subir, como "Campo 1/3", com o tempo que falta, sem percentagem.
  - "Troca de posição" passa a **"Reward cumulativo"** (0/10).
  - **Lesionados e suspensos** no cartão do clube: "Lesionados: 0", ou "Lesionados: Fulano (6 jogos) → no médico 2h10" (o mesmo para suspensos e advogado).
- **Analista (dono, 2026-10-09):** o bot também o **levanta** quando a hora acaba, mesmo que tenha sido o dono a enviá-lo (a partir das 4 h antes do jogo). Pedido observado (`DISCOVERY.md` §3).
- **Médico e advogado (pedido do dono, 2026-10-09):** de graça, com timer, levantam-se no fim; o bot trata dos dois. O médico está a ser observado; o advogado é igual por hipótese, até se ver (regra 7).

## Em aberto

| ID | Decisão | Depende de | Notas |
|---|---|---|---|
| D-008 | Git / repo no GitHub | — | **Do dono.** Ele faz commits, pulls e tudo o que é git/GitHub. O Claude só ajuda com mensagens de commit e versões quando pedido |
| D-018 | Histórico de estatísticas unificado entre as 3 máquinas | — | Pedido em 2026-09-28 (boss coins, vídeos, horas); por desenhar. O resumo atual é só por execução |
