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

**Alterada pelo dono em 2026-10-11:** **4 amigáveis** por equipa antes de cada jogo, em vez de 1 (os do dono contam), na mesma janela das 4 h; a checklist da janela mostra "Amigáveis (N)", verde a partir do 1.º (o bot faz os 4 na mesma) (`THEORY.md` §6).
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
- **Correções do dono (2026-10-09, 0.9.5):**
  - O **"+X"** ao lado dos boss coins conta só o que os **vídeos da loja** deram desde que o bot arrancou; o que o dono gasta no jogo fica de fora (nunca negativo). Letra um pouco maior.
  - **Estádio:** por baixo das partes paradas, cada parte a subir numa linha: "Campo 1/3", uma barra e o tempo que falta (duração em `THEORY.md` §15).
  - **Pré-jogo:** sem percentagem, só as marcas (✓, ○, ⏳).
  - **Barra de baixo:** "A trabalhar desde HH:MM · agora: vídeo da loja 8/9 · a seguir: vídeo de treino Fulano (Clube)", no singular; à espera: "agora: à espera · a seguir: recolher treino Fulano (Clube) às 15:51".
- **Analista (dono, 2026-10-09):** o bot também o **levanta** quando a hora acaba, mesmo que tenha sido o dono a enviá-lo (a partir das 4 h antes do jogo). Pedido observado (`DISCOVERY.md` §3).
- **Médico e advogado (pedido do dono, 2026-10-09):** de graça, com timer, levantam-se no fim; o bot trata dos dois. O médico está a ser observado; o advogado é igual por hipótese, até se ver (regra 7).

### D-027 · A janela lê o quadro sozinha, de 3 em 3 minutos · Aceite · 2026-10-09
Substitui a parte de D-024 que só deixava a janela ler o jogo com o bot parado. A janela lê o quadro (**só GET**) **de 3 em 3 minutos** e quando o dono carrega em **Ver → Atualizar** (primeira opção do menu Ver; por baixo, Avisos e erros, Pasta dos logs, Capturas das falhas), **com o bot a trabalhar ou não**, sem esperar por ele (p. ex. a meio de um vídeo). O quadro mostra sempre a leitura mais recente, seja do bot ou da janela. As leituras do bot (fim de cada passagem, depois de cada escrita) mantêm-se. Uma leitura são ~36 pedidos (~720/hora a mais), medido em 2026-10-09.
Para os dois não se atrapalharem: um só cadeado no programa para renovar a sessão (o segundo usa o passe que o primeiro guardou) e outro para o ficheiro das vendas. As definições HTTPS passam a ser criadas uma só vez (antes, cada pedido gastava ~0,35 s de CPU a carregar os certificados).
**Porquê:** dono, 2026-10-09: o quadro não mostrava o que ele mudou no jogo (lista de transferências, banco) porque só o bot o lia, no fim de cada passagem; "Atualiza sempre a cada 3 minutos (para além dos updates que já faz)", "mesmo que tivesse a ver um vídeo".

### D-028 · O bot carrega em "Claim" na janela "Unclaimed Energy" · Aceite · 2026-10-09
No browser dos vídeos, a janela **"Unclaimed Energy … Claim"** (energia por reclamar, p. ex. depois de o bot guardar o prémio de energia das missões) tapa a página inicial e fazia falhar todos os vídeos. O bot carrega **sempre em Claim**, como faz com os ecrãs do jogo; a energia vai para a carteira de energia. Exceção à regra "nunca usar itens" de D-020, só para esta janela. Regra em `THEORY.md` §17.
**Porquê:** dono, 2026-10-09: "dá claim sempre". Visto nas capturas das 14:00 e 14:04 (os dois clubes bloqueados).

### D-029 · O bot guarda todas as transferências das ligas, 1 vez por dia · Aceite · 2026-10-09
Só leitura (`GET leagues/{L}/transfers`, que dá as últimas 100; `DISCOVERY.md` §3). Uma vez por dia, para a liga de **todas as equipas** da conta, o bot junta as transferências novas a `logs/<PC>/transferencias/<liga>.json` (uma pasta por PC como em D-022; cada transferência uma vez, pelo `id`). Fica no repo, completo (dados de terceiros aceites em `logs/`, D-022). O bot não decide nada com isto: serve para o estudo do preço dos jogadores caros (`PROJECT_BRIEF.md` 13) quando o dono quiser.
**Porquê:** dono, 2026-10-09: "guarda sempre todas as transferências (só precisa de atualizar 1x por dia)". A 1.ª leitura (Espanha, ~10 dias; Arménia, ~2,5 dias) não tinha nenhuma venda de utilizador com preço máximo acima de 100 M€; os jogadores valem mais à medida que a época avança, por isso é preciso ir guardando.

### D-030 · Janela nova: cartões com anéis, linha do tempo e fundo de estádio · Aceite · 2026-10-09
Substitui D-026 **na disposição** (o conteúdo de cada clube mantém-se). A partir de uma maquete do dono:
- **Fundo:** imagem de um estádio à noite (`src/osmbot/gui/assets/fundo.jpg`, reduzida para 2560 px); as caixas ficam por cima, meio transparentes. Vai no repo (escolha do dono).
- **Barra de cima:** à esquerda as diárias (início de sessão, missões, prémio do dia); à direita só "● A trabalhar desde HH:MM" (sem relógio nem "agora"). O painel de baixo e a barra de estado saem.
- **Cartão de cada clube (um por linha, com scroll para 3–4 clubes), 3 colunas:** (1) logótipo, nome, "Liga N.º · Taça: …", **faixa do próximo jogo** na cor do clube (tirada do interior do logótipo; antes verde em casa / vermelha fora, mudado pelo dono em 2026-10-10; o cartão leva a mesma cor de forma discreta: risca no topo, brilho leve e contorno; letra da janela: Sora) com "em 3h33", valor do plantel (revisto em 2026-10-10: lugar a cores, 1.º–2.º verde, 3 últimos vermelho, resto amarelo, + total; jogadores e média ao passar o rato), dinheiro, patrocinadores (revisto em 2026-10-10: só o valor por ronda, ⚠ se faltar algum), estádio com a barra da parte a subir; (2) **treinos em anéis** com o tempo ao centro, jogador e posição por baixo; (3) **pré-jogo em coluna** com a contagem no título ("PRÉ-JOGO · 8/8"), e por baixo cansados, lesionados e suspensos em texto (sem caixas).
- **Coluna da direita:** **boss coins** em destaque (com o "+X" da loja) e a **linha do tempo**: o **"agora"** a meio; **por cima o que vem a seguir**, o mais próximo junto ao "agora" e, a subir, mais longe no futuro; **por baixo o que já passou** (as ações do bot nesta sessão: vídeos, treinos recolhidos e postos, médico, amigável, estádio…), a escurecer à medida que desce. A cor da bolinha é a do clube.
**Porquê:** dono, 2026-10-09: gostou dos cartões com anéis e da linha do tempo lateral com os boss coins em destaque; quer a linha do tempo à volta do "agora".
**Revisto pelo dono no mesmo dia:** o **estádio** passa a 3 círculos pequenos (nível ao centro; a parte a subir enche a roxo com o tempo que falta; as paradas em cinzento, 3/3 a verde); **médico e advogado** em 2 círculos por baixo dos treinos (ninguém · a tratar com o tempo · pronto a levantar · à espera; no advogado, suspensão de 1 jogo = "não dá"), em vez do texto de lesionados e suspensos; o confronto direto é só o **⚠**; caixas um pouco menos transparentes. **2.ª revisão:** "2.º Campeonato" e, por baixo, "🏆 Quartos-de-final"; a faixa do jogo leva "CASA"/"FORA" num rodapé no canto e o adversário numa só linha; a venda aparece por baixo do dinheiro (só o ✓ a verde); estádio centrado; médico e advogado encostados à esquerda, com 🩺 e ⚖️ quando não há ninguém; pré-jogo com letra maior.
**Revisões de 2026-10-10 (0.9.7–0.10.2, pedidos do dono):** a venda passa a ser uma seta verde animada ao lado do dinheiro (quem e quanto ao passar o rato); o dinheiro vai para a linha do nome, à direita, com ícone; os treinos mostram o cone dentro do anel e o tempo só ao passar o rato; médico e advogado com as figuras do jogo dentro do anel (D-033), sem 🩺/⚖️; todos os temporizadores na cor do clube meio apagada, verde só quando acabam; a linha do tempo usa ícones em vez de bolinhas (bola nos jogos, temporizador em "agora" quando o bot está à espera) e o emblema pequeno do clube antes do nome; a janela tem largura mínima para os cartões caberem inteiros.


### D-031 · A janela fala português ou inglês · Aceite · 2026-10-09
No menu de cima, **Idioma / Language** escolhe **Português** ou **English**; a escolha fica guardada em `~/.osmbot/config.json` (por PC) e aplica-se logo. Em inglês ficam a **janela** (ecrã inicial, menus, cartões, linha do tempo, Sobre) e as mensagens de **Avisos e erros**. Os **ficheiros de log** (`logs/`, `bot.log`) e a consola continuam **sempre em português**, para serem comparáveis entre PCs. Português por omissão. As traduções vivem num só sítio (`src/osmbot/i18n.py`); uma mensagem sem tradução aparece em português.
**Porquê:** pedido do dono, 2026-10-09 ("janela e avisos").

### D-032 · Um pedido que o jogo recusa não se repete · Aceite · 2026-10-09
Quando o jogo responde "não" (4xx, exceto 401, 408 e 429) a um pedido de escrita, o bot anota-o em `~/.osmbot/recusas.json` (o quê, para que jogador/clube) e só volta a tentar quando faz sentido: **jornada seguinte** (médico e advogado por jogador, levantar, analista, amigável contra esse clube), **dia de jogo seguinte** (04:00 UTC: início de sessão, missões, patrocinador recusado), **fim do tratamento em curso** (o 2.º lesionado quando o jogo só aceita um) ou **mais dinheiro** (estádio). Avisa uma vez. As anotações apagam-se quando muda a versão. Treinos e vídeos ficam como estavam (já têm limite). Falta de rede, erro do servidor e "demasiados pedidos" não contam como "não". Código: `src/osmbot/game/refusals.py`.
**Porquê:** o advogado de um suspenso de 1 jogo levou 400 a cada ~1 min durante uma noite; pedidos recusados em repetição são o tipo de comportamento que um anti-bot deteta (`RISKS_AND_COMPLIANCE.md`). Tabela "hoje → com a regra" aprovada pelo dono em 2026-10-09.

### D-033 · Ícones do próprio jogo dentro do programa · Aceite · 2026-10-10
A janela usa imagens dadas pelo dono: o **boss coin** (arte do OSM/Gamebasics), o ícone do **dinheiro do clube**, o **cone** dos treinos e as figuras do **médico** e do **árbitro com o cartão vermelho** (estas duas recortadas em círculo; acrescentadas no mesmo dia). Vão em `src/osmbot/gui/assets/` (`bosscoin.png`, `clubfunds.png`, `training.png`, `doctor.png`, `lawyer.png`, `missions.png`, `stadium.png`, e desde a 0.11.6 `inventory.png` e `universal.png`, tirados do site do jogo, reduzidas ao tamanho de uso; as duas últimas para a linha do tempo) e, por isso, no repo público e nas releases. **Risco aceite pelo dono** (pergunta de 2026-10-10: "No repo, aceito o risco"), como exceção a D-016 só para estas imagens. Se a Gamebasics pedir, saem e a janela funciona sem elas (sem o ficheiro, o ícone fica vazio).
**Porquê:** o dono quer a janela com a cara do jogo; o risco é de direitos de autor sobre imagens pequenas, não de segredos.
| ID | Decisão | Depende de | Notas |
|---|---|---|---|
| D-008 | Git / repo no GitHub | — | **Do dono.** Ele faz commits, pulls e tudo o que é git/GitHub. O Claude só ajuda com mensagens de commit e versões quando pedido |
| D-018 | Histórico de estatísticas unificado entre as 3 máquinas | — | Pedido em 2026-09-28 (boss coins, vídeos, horas); por desenhar. O resumo atual é só por execução |
### D-034 · Registo das passagens do motor de transferências · Aceite · 2026-10-11
A cada leitura do quadro (3 em 3 min), o bot compara a lista de transferências de cada liga com a anterior (só leitura; estado em `~/.osmbot/mercado.json`). Quando os jogadores postos pelo jogo (clubes de fora da liga) baixam de preço, ou um jogador de um treinador sai da lista, grava um registo em `logs/<PC>/transferencias/motor/<liga>.jsonl` (uma linha JSON por mudança): entre que leituras foi, quantos preços do jogo desceram, o que estava à venda na leitura antes (preço, valor, % do máximo, idade, posição, ratings, desde quando, se é do dono) e o que saiu, separado em **vendido** (aparece nas transferências da liga; 1 GET só quando alguém sai) e **retirado**. No registo do bot, uma linha: "Motor de transferências (liga): passou entre HH:MM e HH:MM; vendidos X de Y à venda (teus: A de B)". Código: `transfers/engine.py` (puro), `game/market.py`. Nada é decidido a partir disto; serve para estudar com o tempo a probabilidade de venda por preço e por % do máximo, dentro e fora de eventos.
**Porquê:** pedido do dono ("configura os logs das transferências como achares útil para tirarmos conclusões com o tempo"), depois da pesquisa no fórum (`DISCOVERY.md` §6c: motor 8×/dia, venda por sorte com probabilidade por preço e taxa). A hipótese "o jogo baixa os seus preços a cada passagem" fica por confirmar com estes registos.

### D-047 · Banco pela posição específica e hover das "Posições" · Aceite · 2026-10-14
O aviso "suplente melhor que titular" só compara jogadores com a mesma `specificPosition`; a ordem do banco continua pela posição geral. O ponto "Posições" da checklist diz no hover quem está fora da sua posição específica, pelo mapa de lugares de cada formação lido no código do site (`theory/lineup.places`), confirmado pela checklist real (Betis 9/11 com Messi e Haaland trocados). Fechadas no `THEORY.md` as suposições do rating por posição e do `statAtt` (o site usa a mesma conta na força da equipa). Versão 0.11.10.
**Porquê:** o aviso dizia "Dembélé no banco, Messi a jogar" (PL contra extremo). O dono testou: as barras de força não mudam com a troca, mas o jogo avisa que "os jogadores rendem mais na sua posição específica". Ordem do banco: "posição geral, como está". Hover: "Sim, analisa o q precisares".

### D-046 · Avisos do pré-jogo, setas de venda, força do próprio clube e hovers · Aceite · 2026-10-13
Na checklist do cartão, **Banco**, **Onze** e **Especialistas** ficam amarelos quando o jogo os dá como feitos mas fogem à regra (`THEORY.md` §21), e o hover diz porquê: banco com um suplente pior à frente de um melhor da mesma posição (sempre) ou um suplente em forma melhor do que um titular; onze com o desarme que não serve ao árbitro do próximo jogo (campo `style`; árbitro do calendário) ou formação fora do §1 (antes da análise só 4-3-3 A); especialistas com o papel errado e quem a regra pede. Só avisa, não escreve. A **força do próprio clube** conta pela formação da tática (antes: sem círculo com um lugar vazio no onze); a do adversário continua só depois da análise. As **setas verdes** das vendas desaparecem quando os slots de venda enchem. Todos os **hovers** com cantos redondos, mais espaço e a 1.ª linha como título. Corrigido no §2: no 4-3-3, marcação **à zona**. Leitura nova: `teamtactics` do próprio clube e `referees` da liga, na leitura do quadro (10 min de cache para os árbitros). Versão 0.11.9.
**Porquê:** pedidos do dono (2026-10-13), depois de responder às perguntas: setas "quando os slots enchem"; força do adversário "só depois da análise"; banco "ordem dentro da posição" (avisa mesmo com o melhor cansado) e "suplente melhor que titular" (não avisa com o suplente cansado); onze "desarme vs árbitro, formação"; desarme com brando "Agressivo ou Extremo", com muito brando "Extremo"; hovers "caixa moderna + 1.ª linha título"; marcação "4-3-3 à zona".

### D-045 · Formação: 4-3-3 A por omissão, 5-3-2 só contra mais fortes por mais de 5 % · Aceite · 2026-10-13
Substitui a regra de 2026-09-27 (`THEORY.md` §1): o 4-3-3 B deixa de ser a regra para jogos parecidos; 5-3-2 com o adversário mais forte por mais de 5 % (antes: 2 pontos de rating); em tudo o resto, 4-3-3 A. O dono pode experimentar o 4-3-3 B, e o registo dos jogos (D-044) diz depois se compensa. Código `theory/tactics.choose_formation` (o bot não muda táticas; o dono fá-las à mão).
**Porquê:** análise de 272 jogos das 2 ligas (`WORKLOG.md` 2026-10-13): o 4-3-3 A rendeu mais em todas as situações com dados suficientes. O dono: "tendo em conta nossa estratégia, e que vamos ter sempre dos melhores planteis, mais vale continuar sempre de 433A?" → "Sim, podes".

### D-044 · Registo dos jogos com o jogo real (onze, eventos, força do jogo) · Aceite · 2026-10-13
Completa a D-041. Cada linha de `logs/<PC>/jogos/` passa a levar o jogo como a página Resultados o mostra: `estatisticas` (por lado a **força do jogo** ataque/defesa/total, formação "433B", remates, posse, cantos, faltas, conversão, estágio; zonas; homem do jogo), `onze` (por lado quem jogou: titulares 1–11 e suplentes que entraram, com nota, posição e ratings **do momento do registo**) e `eventos` (minuto, lado, tipo: golo, cartão, lesão, substituição, ocasião, VAR…). Leituras novas por jornada: `playergrades/{jornada}` de cada clube e `matches/{n}/events/{jornada}` de cada jogo (`DISCOVERY.md`). **Uma vez por liga, a época inteira** até agora, com o mesmo detalhe (o jogo guarda tudo; corrige a D-041, que dizia que as notas antigas se perdiam), com 0,3 s entre pedidos. Um jogo já registado por inteiro por qualquer PC (`logs/*/jogos`, depois do pull) não volta a ser lido. A linha do registo do bot de cada jogo do dono diz também a força do jogo ("força do jogo 720/782"). Código `game/matchlog.py`.
**Porquê:** o dono (2026-10-13), depois de mostrar que Resultados dá "o 11, a tática, TUDO" de todos os jogos: "Quero que guardemos sempre todos os logs dos jogos a partir de agora!!!"

### D-043 · Força das equipas, objetivo da época e posição sem suplente na janela · Aceite · 2026-10-13
A janela mostra: (1) a **força da equipa** num círculo, o número do jogo (melhores por posição na formação atual, `DISCOVERY.md`), a do clube do dono sempre e a do adversário **só depois da análise** (opção escolhida pelo dono, em vez de uma estimativa); (2) no hover do lugar do campeonato, os **3 primeiros com os pontos** (`GET leagues/{L}/standings`) e o **objetivo da época** (campo `goal`), e "Campeões" com o título matematicamente garantido; (3) na linha dos cansados, **"sem suplente"** e até 3 jogadores "SALE" da posição que cabem no dinheiro. Só leituras novas: a classificação e o plantel do próximo adversário, no máximo de 10 em 10 min; nada se compra. Regras em `THEORY.md` §16 e §19 (com suposições [S]: cores do círculo, o que conta como suplente e como título garantido). Versão 0.11.8.
**Porquê:** pedidos do dono na conversa do plano de época (2026-10-13), depois de ver prints; correção do dono a meio: o círculo é o rating ("tipo 105"), não o valor em dinheiro.
**Também nesta sessão:** verificador de tipos (pyright) experimentado e **posto de lado** pelo dono (o teste novo do ciclo com várias passagens cobre o erro que o motivou); só voltar a propor se aparecer um 3.º erro do mesmo tipo que os testes não apanhem.

### D-042 · Especialistas pela regra do dono antes de cada jogo · Aceite · 2026-10-12
Nas últimas 4 h antes de cada jogo, o bot compara os especialistas com a regra (`THEORY.md` §4) e corrige só os papéis diferentes (`PUT …/specialists`, um lugar do onze por papel; 1.ª gravação feita pelo Claude com o OK do dono: livres de um clube para o titular com mais ataque, 200). A checklist do quadro mostra "Especialistas" a amarelo quando não seguem a regra. Um jogador pode ter vários papéis. Passa a "autónomo com o bot ativo" (regra 5). Versão 0.11.7.
**Porquê:** o dono (2026-10-12): "Sim, faz isso"; "se os especialistas não estiverem corretos, não deverá aparecer o certo, e sim a amarelo".

### D-041 · Registo de todos os jogos das ligas · Aceite · 2026-10-12
Depois de cada jornada (o `weekNr` da liga avança), o bot regista **todos os jogos de liga e de taça** das ligas onde o dono tem clubes, uma linha por jogo em `logs/<PC>/jogos/AAAA-MM.jsonl`: resultado, vencedor, prolongamento/penáltis, **árbitro e rigor**, lugar antes e depois, valor do plantel e média do melhor onze das duas equipas, e cada jogador com ratings, **nota do jogo** e golos (os clubes dos outros só com o essencial, ~90 KB por jornada nas 2 ligas). Nos jogos do dono, também a **sua tática** lida nas últimas 4 h antes do jogo e, se o jogo a der, a **análise do adversário** (`spyresults`). As táticas dos outros clubes o jogo recusa (403): "que tática ganha a que tática" só se vê nos jogos do dono. Na primeira vez, também a **época até agora** (resultado e árbitro de cada jogo já disputado, marcados `historico`; as notas dos jogos antigos o jogo já não guarda). Só leituras; nada aparece na janela, só uma linha no registo do bot por jogo do dono. Código `game/matchlog.py`.
**Porquê:** o dono (2026-10-12): "para já, só logs. Mas quero que registes tudo."

### D-040 · 8 amigáveis durante um Intense Friendlies · Aceite · 2026-10-12
Enquanto decorre um evento **Intense Friendlies** (calendário do fórum, D-038), cada jornada leva **8 amigáveis** em vez de 4 (horas **[S]**: 16, 14, … 2 h antes do jogo; nenhum depois de 1 h antes do fim do evento). Cada amigável fica no registo `amigaveis/` com o progresso dos jogadores antes e depois e o nome do evento, para medir se compensa. Os outros eventos com amigáveis ficam com 4; no Transfer Madness o bot não faz nada (o dono vê o evento na janela). Regra em `THEORY.md` §6.
**Porquê:** o dono (2026-10-12): "nos Intense Friendlies subia-se para 8 (com logs, para ver se compensa)"; "é indiferente quando os amigáveis são feitos, desde que antes do jogo".

### D-039 · Usar os itens do inventário que vão expirar · Aceite · 2026-10-12
Substitui em parte a D-020 ("nunca se usam itens"): os itens com prazo (**treinadores universais** e **sacos**) usam-se sozinhos **4 h antes de expirar**; a janela avisa **24 h antes** junto ao ícone do inventário. O treinador universal vai para a equipa com mais a ganhar (previsão do jogo; empate → pior plantel) e treina o titular de qualquer posição com menos sessões na jornada e maior previsão (regras em `THEORY.md` §20). Trocas de posição e progressão continuam manuais. Pedidos lidos no código público da web; o 1.º uso do treinador universal foi feito pelo Claude com autorização direta do dono (2026-10-12, um defesa titular de uma das equipas): ativação e sessão aceites (200). Abrir um saco ainda não foi feito em real. Passa a "autónomo com o bot ativo" (regra 5). Versão 0.11.6.
**Porquê:** o dono (2026-10-12): "há itens que eu perco porque me esqueço"; perder = expirar sem usar.

### D-038 · Calendário de eventos lido do fórum, evento visto nas definições do jogo · Aceite · 2026-10-12
- **Fórum:** o calendário do mês é um post da staff no tópico 67089 do fórum oficial. O fórum tem uma proteção contra leitores automáticos (Anubis); o bot lê-o com o seu Firefox escondido, que passa a proteção como um browser normal, e a API do fórum (`/api/topic/67089`). **O dono escolheu isto sabendo que contorna essa proteção** (as alternativas eram copiar o calendário à mão ou só ver o evento quando começa). Limites: só quando falta um mês (o atual; o seguinte a partir do dia 25), no máximo 1 tentativa por dia, o mês seguinte a uma hora ao acaso; 1 página por tentativa. Guardado em `~/.osmbot/eventos.json` e em `logs/<PC>/eventos/`. Se o post mudar de formato, o bot avisa e não inventa datas.
- **Jogo:** de hora a hora, por liga, as `gamesettings` comparadas com os valores normais (lidos a 2026-10-12, dia sem evento) dizem o que um evento mudou; `eventnotifications` é lido também e guardado se responder (404 num dia sem evento).
- **Por fazer:** usar o calendário para agir (mais amigáveis nos eventos de amigáveis, aviso para listar os caros antes de um Transfer Madness). Não procurado noutras fontes: pesquisa web sem resultados; os cartões de eventos da Google Play expiram.
**Porquê:** o dono (2026-10-12): "não queria ter que ser eu a fazer isso manualmente"; "quero a 1 e a 2 juntas". Versão 0.11.4.

### D-037 · Treino para quem tem mais a ganhar, treinos vistos contam, registos para estudar o jogo · Aceite · 2026-10-12
- **Desempate da rotação** (`THEORY.md` §5): entre os titulares com menos treinos na jornada, o de **maior previsão do jogo**; só depois o melhor. Dados: os jogadores de 115 ganham 2–3× menos por treino do que os de 104–110. Na leitura real (2026-10-12) muda 1 de 8 escolhas (DEF 100 com previsão 47 em vez de DEF 109 com 16); os jogadores listados para venda continuam fora.
- **Treinos vistos contam:** o bot aponta em `~/.osmbot/treinos.json` todas as sessões que vê no jogo (a decorrer ou por recolher), com a jornada de cada uma, e não só as que põe. O jogo não guarda histórico (`DISCOVERY.md` §3); perdem-se só as que o outro PC pôs e recolheu antes de desligar. A sincronização entre PCs (OneDrive, Git automático, nuvem) foi posta de lado pelo dono: "para já, continuamos só com logs".
- **Registos para estudar** (JSON, uma linha por acontecimento, `logs/<PC>/<tipo>/AAAA-MM.jsonl`; só leituras a mais, nada escrito no jogo): treinos (pôr com os candidatos; recolher com ganho, bónus e rating), amigáveis (progresso antes e depois), médico e advogado (jogos de baixa antes e depois), jogadores "SALE" (quando aparecem e saem). Jogos (resultado, ratings, árbitro) ficam para a versão seguinte; eventos continuam pelo calendário do fórum.
**Porquê:** pedidos do dono (2026-10-12): "treinar primeiro o que tem mais expectativa de melhorar"; "tudo registado em logs, para tirarmos conclusões futuras". Versão 0.11.3.

### D-036 · Amigáveis ao longo do dia, analista levantado logo que acaba · Aceite · 2026-10-12
Substitui em parte a D-025: os **4 amigáveis** deixam de esperar pela janela das 4 h e espalham-se pelo dia (o k-ésimo a partir de 16, 12, 8 e 4 h antes do jogo, **[S]** horas escolhidas pelo Claude; os em atraso fazem-se logo). O **analista** continua a ser enviado só nas últimas 4 h, mas é **levantado assim que acaba**, a qualquer hora. Versão 0.11.2.
**Porquê:** o dono (2026-10-12): "podem ser distribuídos pelo dia"; "assim que ficar pronto para recolher, recolhe-se". O quadro mostrava "Análise por levantar" durante horas.

### D-035 · Rotação dos treinos, depósito antes do jogo, leitura mais lenta com a janela escondida · Aceite · 2026-10-12
Três mudanças pedidas pelo dono depois de uma revisão do bot ("o que nos pode estar a atrasar"):
- **Treinos:** o titular com menos sessões nesta jornada, o melhor primeiro, em vez de sempre o melhor da posição (`THEORY.md` §5). Registo da previsão do jogo e do 1.º/2.º/… treino da jornada em cada linha "a treinar", para medir o efeito. Sessões da jornada em `~/.osmbot/treinos.json` (por PC).
- **Poupança:** depositar tudo 5 min antes de cada jogo (janela de 15 min), primeira coisa da passagem (`THEORY.md` §13). Pedido já observado (`PUT savings/transfer`, usado pelo estádio desde 2026-10-07). Passa a "autónomo com o bot ativo" (regra 5).
- **Janela:** substitui D-027 em parte: com a janela escondida no ícone ou minimizada, lê o quadro de **15 em 15 min** (à vista continua de 3 em 3). O registo do motor de transferências (D-034) chega com isso (o motor passa a cada ~2 h).
**Porquê:** o dono quer subir mais depressa os titulares e pôr o dinheiro parado a render; ~720 pedidos/h a mais com a janela fechada era tráfego que nenhuma pessoa gera (`RISKS_AND_COMPLIANCE.md`). A regra de vender a 75 % acima de 100 M€ fica como está até haver dados fora de eventos (dono: "temos de confirmar com o tempo").
