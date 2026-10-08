# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-PT/1.1.0/); versões segundo [SemVer](https://semver.org/lang/pt-BR/) (`0.x` até haver automação estável).

Este ficheiro é o **histórico de versões, para quem lê o repo**. O diário interno de cada sessão de trabalho está em [`docs/WORKLOG.md`](docs/WORKLOG.md).

## [Por lançar]

## [0.8.3] — 2026-10-08

O registo vai para o repo sem configurar nada, e os vídeos já não ficam presos atrás da janela de experiência de manager.

### Corrigido
- **Vídeo de treino "não encontrado" (`TimeoutError`):** a janela de experiência de manager ("Won/Lost against manager…") às vezes só aparece depois de o bot verificar se havia janelas abertas, e tapava o botão TRAINING. Agora, se um botão estiver tapado, o bot fecha as janelas da ronda e tenta outra vez. Vale para os botões Shop, Watch ad, TRAINING, "-2h" e para a carteira dos vídeos de dinheiro.

### Alterado
- **A pasta do repo para o registo é encontrada sozinha** (D-023): o bot (a partir do código, portátil ou instalado) procura uma pasta `OSMbot` ao lado da sua pasta, ou na pasta pessoal, em `Documents` ou em `Desktop` (incluindo as do OneDrive). Na primeira vez, copia também o registo antigo desse PC. A opção **Pasta dos logs** sai do menu; fica o comando `osmbot pasta-logs <pasta>` para um repo noutro sítio.

## [0.8.2] — 2026-10-08

Os vídeos de treino deixam de esperar e o registo do bot passa a ir também para o repo.

### Adicionado
- **Registo no repo** (D-022): cada linha do registo vai também para `logs/<nome do PC>/AAAA-MM-DD.log` no repo, para analisar os logs de qualquer máquina depois do commit/push (o bot não mexe no git). Tokens e e-mails nunca entram. No bot instalado escolhe-se a pasta do repo uma vez: menu **Pasta dos logs** (ou `osmbot pasta-logs <pasta>`), que copia também o registo antigo desse PC.

### Alterado
- **Vídeos de treino e de dinheiro já não saltam janelas** (D-021): vêem-se sempre que o jogo deixa, logo na passagem em que ficam disponíveis. Só a loja continua a saltar ao acaso 15% das janelas (as boss coins podem esperar; o tempo de treino não).

## [0.8.1] — 2026-10-08

O bot passa a aguentar sozinho um dia inteiro: já não fica preso no vídeo de treino nem pára à primeira falha.

### Corrigido
- **Vídeo de treino "não encontrado" na fábrica:** depois do "Continue" o jogo mostra o jogo da ronda (botão **Skip**), outro "Continue" e a janela da experiência de manager (fecha com um clique fora). O bot só passava o primeiro ecrã e ficava ali até esgotar o tempo, em todas as tentativas. Agora passa a cadeia toda (também nos vídeos de dinheiro). Ensaio real sem clicar no "-2h": botão encontrado.
- **Sessão:** com vários pedidos e vídeos a correr, o bot podia renovar a sessão com tokens antigos que tinha em memória, ou o Firefox de um vídeo podia gravar tokens mais velhos por cima dos novos. Agora relê a sessão gravada antes de renovar e o browser só grava tokens mais recentes.
- **Início de sessão:** se a recompensa foi reclamada mas não foi possível gastá-la na carteira, o bot volta a tentar nas passagens seguintes (só essa, nunca outros itens).
- **Troca de posição (vídeos acumulados):** o quadro já não mostra "reabre em…" quando o limite não foi atingido.

### Alterado
- **Não pára à primeira falha (D-019):** uma escrita falhada nos treinos volta a ser vista 10 min depois, e o bot só pára ao fim de 3 passagens seguidas com falhas. Sem rede, tenta com pausas cada vez maiores (até 15 min) durante até 6 h. Um tipo de vídeo que falha sempre espera cada vez mais (10, 20, 40, 60 min) sem atrasar os outros.
- **Menos pedidos de missões:** o quadro reaproveita a leitura das missões durante 5 min, em vez de repetir o `POST weeklytrack` depois de cada vídeo ou reclamação.

## [0.8.0] — 2026-10-07

O bot passa a reclamar sozinho as **recompensas diárias**, no modo ativo (D-020), e o quadro e o menu ficam mais completos. Pedidos das recompensas observados com o dono (`inspect-writes`); **as recompensas ainda não foram corridas em real** (primeiro teste: o início de sessão e o prémio de amanhã).

### Adicionado
- **Início de sessão:** reclama quando disponível e gasta a recompensa na carteira certa, como o site faz (energia, boss coins). O saco do dia 21 fica no inventário.
- **Missões:** reclama as 3 diárias quando chegam ao objetivo e depois **o prémio do dia de hoje**, sempre **"guardar"** (fica no inventário; o bot nunca usa itens). No máximo um prémio do dia por dia; nunca o de amanhã.
- **Vídeos acumulados:** reclama a "troca de posição" (10 vídeos) para o inventário.
- Respeita os limites do inventário do jogo; o que o jogo recusar não se repete.
- **Quadro:** duas linhas novas por baixo das Boss coins (`diárias`: início de sessão, missões, prémio do dia, novo dia em…; `extra`: troca de posição com barra 7/10 e quando reabre). O bot acorda quando começa um novo dia e quando os vídeos reabrem. Atualiza logo a seguir a cada reclamação.
- Comando `osmbot recompensas` (`--simular` mostra o plano sem escrever).
- **`inspect-writes` (descoberta) mais seguro e completo:** grava cada pedido em `~/.osmbot/inspect-writes.log` à medida que acontece, mostra valores curtos dos campos (nunca de tokens, palavras-passe, cookies ou e-mails), a hora e também as leituras (GET) de missões/início de sessão/recompensas.

### Alterado
- **Linha das Boss coins:** mostra quando a loja reabre, com uma barra pequena (`loja ██████░░░░ 0h32`; a espera é de 1 h, confirmada). Enquanto há vídeos para ver não mostra nada (o bot vai vendo-os).
- **Quadro sem registo:** só aparecem os erros (a vermelho, durante 30 min). Tudo o resto fica no `bot.log`.
- `tools/build_portable.py` esvazia a pasta do dist em vez de a apagar: um terminal aberto lá dentro já não bloqueia o build.

### Corrigido
- **Vídeo de treino (e de dinheiro) "não encontrado":** depois de uma ronda o jogo mostra o ecrã "Matchday … Continue" por cima do clube, a esconder os menus; o bot não o fechava e dava erro (visto nas capturas em `~/.osmbot/failures`). Agora carrega em "Continue" (como se faz à mão; no máximo 3 vezes) assim que o jogo abre, em todas as tarefas do browser (loja, treino e dinheiro), e outra vez depois de entrar no clube. **Ainda não testado em real.**

## [0.7.1] — 2026-10-07

Acabamento do menu e do quadro da consola.

### Alterado
- **Menu com setas:** escolhe-se com ↑ ↓ e Enter (a opção escolhida fica a verde, com `»`); escrever o número ou Esc continua a funcionar.
- **Barras sempre visíveis, uma linha por jogador:** os treinos mostram a barra de 8 h e a parte que um vídeo encurtou (2 h) aparece a azul. O estádio mostra a barra (18 h) na mesma linha da peça em obras.
- **Primeira linha de cada clube a verde** (nome, classificação e liga); "Lista de Transf. 3/4" a branco, com os números a amarelo só quando há vaga. Estádio: "Treinos", "Campo", "Capacidade".
- **Cores com significado fixo:** verde = feito/bom, amarelo = pede atenção, azul = tempo que falta ou encurtado, cinzento = etiquetas e barras vazias, vermelho = erros.
- **Boss coins:** `Boss coins 2515  +18` (o ganho desde o arranque a verde). Saiu a linha dos vídeos com vistos; o resumo fica numa linha com os vídeos.
- **Mais instantâneo:** o quadro volta a ler o jogo logo a seguir a recolher/pôr a treinar, a subir o estádio, a assinar patrocinadores e a cada vídeo de dinheiro; um vídeo de treino atualiza logo a hora do treino.
- **Janela pequena:** o quadro encurta o registo e as linhas em branco, mas mantém as barras. A largura ajusta-se à janela (até 100 colunas).
- Aviso no topo: "Para parar: Ctrl+C".

### Corrigido
- **Ctrl+C não parava o bot** quando se clicava na janela do Windows: a consola entrava em modo "Selecionar" (QuickEdit), congelava o bot e o Ctrl+C só copiava. Esse modo fica desligado enquanto o quadro corre.

## [0.7.0] — 2026-10-07

Menu e quadro da consola redesenhados.

### Alterado
- **Menu** só com Iniciar, Login e Sair, centrado e com arte; o resto fica como comandos.
- **Quadro:** sem a linha "A seguir"; "Lista de transferências"; estádio com visto verde e barra (o visto é √, a fonte da consola não tem ✓); patrocinadores "n/4 escolhidos"; dinheiro em M a partir de 1000 k; cansados numa linha; barra da loja; resumo com "salto" e horas encurtadas; boss coins atualizam logo após cada vídeo.

### Corrigido
- Variável do estádio que sobrescrevia o nível de compactação do quadro.

## [0.6.1] — 2026-10-07

Correção do quadro da consola, que com a informação nova da 0.6.0 ficava mais alto do que a janela. A 0.6.0 não chegou a ser lançada como Release: o Release é esta versão e inclui tudo o que a 0.6.0 trouxe.

### Corrigido
- **Quadro da consola a empilhar cópias de si próprio:** com a informação nova o quadro ficou mais alto do que a janela, e cada redesenho deslizava o ecrã e deixava milhares de linhas no histórico. Agora o quadro encurta-se sozinho até caber na janela (avisos de condição numa linha, treinos numa linha, sem linhas em branco), usa o seu próprio ecrã (sem histórico) e escreve por cima de si próprio.

## [0.6.0] — 2026-10-07

O bot passa a **gerir o clube além dos treinos**: estádio, patrocinadores e vídeos de dinheiro, com avisos de condição física e um quadro de consola mais completo. Tudo o que é novo foi escrito com os pedidos observados com o dono, mas **ainda não foi corrido em real** (o dono testa a seguir).

### Adicionado
- **Vídeos de dinheiro** (3 por dia) no modo ativo: o bot abre o clube, a barra do dinheiro e o cartão "Free rewards" seguinte, no clube com **mais poupança** (a recompensa é uma percentagem dela). Mesmas regras dos outros vídeos (limite do jogo, janelas saltadas, pausas). O quadro mostra "dinheiro" e o bot acorda quando os cartões reabrem. Não foi testado em real.

- **Estádio automático** (`osmbot estadio`, e no modo ativo): quando o clube está livre, começa a melhoria seguinte (campo de treinos, campo, capacidade; todos os clubes). Sem dinheiro nos fundos, traz a poupança, tenta e volta a depositar o que sobra; sem dinheiro nem assim, não faz nada e só tenta de novo quando o dinheiro total sobe. Acorda quando a melhoria acaba. Não testado em real.
- **Quadro com mais informação e cor:** por clube, dinheiro (fundos e poupança), estádio (nível de cada parte, a que está a melhorar e o tempo que falta) e patrocinadores (espaços e receita por ronda); "estádio acaba" em "A seguir"; cores para valores, avisos e erros do registo.
- **Aviso de condição física:** titulares (onze) com a condição a amarelo (abaixo de 80%) aparecem no quadro (`⚠ nome posição cond. N%`) e no registo, uma vez por jogador até recuperar. Só avisa; não troca ninguém.
- **Patrocinadores automáticos** (`osmbot patrocinadores`, e no modo ativo): cada espaço livre recebe a proposta que paga mais por ronda (empate: contrato mais curto; pode repetir-se; se o jogo recusar, usa a seguinte). Não testado em real.
- **Vídeos nunca se desligam**: falham, registam e tentam de novo (10 min); só param quando o jogo diz que não há mais. Captura de ecrã em `~/.osmbot/failures/` quando um vídeo falha. Janelas saltadas: 15%.

### Alterado
- **Todos os textos da interface reescritos** (menu, quadro, registo, comandos): curtos e diretos, com acentos, sem frases de assistente. Ex.: `Loja: janela saltada`, `Treino: vídeo 2 (Clube A, GR)`, `! Clube B: 1 slot(s) de venda livre(s) (3/4)`.

## [0.5.0] — 2026-10-06

O bot passa a **trabalhar sozinho**: recolhe e treina, vê vídeos (loja e treino), avisa de slots de venda livres, tudo num quadro de consola em tempo real. Distribuição para Windows (pasta portátil e instalador). **Testado em real no Windows**; o Mac continua pelo ambiente de desenvolvimento.

### Adicionado
- **Modo ativo** (`osmbot ativo`, D-014): ciclo que recolhe e treina quando os treinos acabam. Acorda no mais próximo de: fim do próximo treino, reposição dos vídeos da loja, reposição dos vídeos de treino (máx. 30 min; mín. 30 s; +5–60 s aleatórios), por isso acompanha treinos curtos de eventos sem configuração. Pára e avisa à primeira falha de escrita, sessão perdida ou 3 erros de rede seguidos. `--simular` faz uma passagem sem escrever.
- **Anúncios** (`src/osmbot/game/ads.py`, D-012), num Firefox **sem janela**, só quando o limite do jogo está aberto, saltando ~35% das janelas e com pausas de 20–75 s. Nunca chama `videos/watched`: é a própria página que o faz, como quando o dono vê o vídeo.
  - **Loja** (1 boss coin por vídeo): até 9 seguidos.
  - **Treino (−2h):** cada vídeo vai para a sessão com **mais tempo em falta** (entre os clubes), para os treinos acabarem por volta da mesma hora; ignora sessões com menos de 2h; clica sempre em "- 2h", nunca em "Train instantly" (custa boss coins); confirma que o tempo baixou.
  - Se falharem 2 vezes seguidas, desligam-se nessa execução e os treinos continuam. `--sem-anuncios` desliga-os.
- **Aviso de slots de venda livres** (`osmbot slots`, só leitura, e verificação a cada despertar do modo ativo): avisa na consola e no registo quando passa a haver mais slots livres do que antes. O limite vem do jogo (`MaxPlayersOnTransferlist`).
- **Quadro de consola** (D-015): ecrã fixo que se redesenha de segundo a segundo, com estado, contagem decrescente, os clubes com os treinos e barras de progresso, boss coins, estado dos anúncios, aviso de slot livre, resumo desde o arranque (saldo, vídeos, treinos) e as últimas linhas do registo. Só aparece num terminal; `--sem-quadro` (ou saída redirecionada) dá linhas simples.
- **Menu na consola:** `osmbot` sem argumentos abre um menu (1 iniciar o bot, 2 sem anúncios, 3 estado, 4 ensaio, 5 login, 0 sair). Os comandos diretos continuam.
- **Registo** em `~/.osmbot/bot.log` e resumo ao parar.
- **Distribuição para Windows** (D-016), com `python tools/build_portable.py [--zip] [--installer]`:
  - **Pasta portátil** (`OSMbot.exe` na raiz: um `python.exe` oficial renomeado que abre o menu; ~500 MB, .zip ~180 MB) com Python embutido, dependências e o Firefox do Playwright.
  - **Instalador `OSMbot-Setup.exe`** (Inno Setup; ~130 MB): assistente em português, instala por utilizador sem administrador, atalhos com ícone, desinstalador; não toca na sessão.
  - **Ícone original** (`tools/make_icon.py`); `--icone` para uma cópia pessoal.
- 38 testes novos; **97 no total**. Os testes ficam isolados do jogo real, da sessão e do registo (`tests/conftest.py`).

### Alterado
- `recolher` e `treinar` escrevem por omissão; `--simular` mostra o plano sem escrever (`--confirmar` fica como alias sem efeito).
- Autonomia do Claude por níveis (D-014): leitura livre; recolher/treinar autónomos com o bot ativo; escritas novas pedem OK.
- A saída do Windows passa a UTF-8.
- **Documentação** em termos genéricos: clubes, ligas, jogadores e nomes de utilizador de terceiros substituídos em `docs/` e `tests/`, para o repo poder ser público.

### Corrigido
- O quadro ficava parado enquanto o bot trabalhava (o desenho ia para a saída redirecionada para o registo e sujava-o com códigos de ecrã).
- Os vídeos eram contados só no fim da série (parar a meio perdia a contagem): contam-se no momento em que são vistos.

### Descoberto (ver `docs/DISCOVERY.md`)
- Fluxo dos vídeos: `start` → anúncio → `watched` → recolha, com `actionId` `BusinessClub` (loja), `TrainingTimer` (treino) e `Multistep1–3` (dinheiro). O vídeo da loja e o de treino funcionam num Firefox controlado, também sem janela.
- Limite de slots de venda em `gamesettings`; limites dos vídeos em `user/caps/actions/{actionId}/0`.
- Página de treino: colunas por treinador, botões "- 2h" e "Train instantly".

### Por fazer
- Os 3 vídeos de dinheiro diários; transferências automáticas; tolerância a falhas por concorrência com o dono; histórico de estatísticas entre máquinas; teste no PC da empresa.

## [0.4.0] — 2026-10-04

Primeira automação com escrita na conta: recolher treinos e pôr a treinar. **Testado em real no Mac** (2 clubes, 8 treinos, tudo 200).

### Adicionado
- `osmbot recolher`: recolhe os treinos prontos. Só escreve com `--confirmar`; sem isso mostra o que faria.
- `osmbot treinar`: põe a treinar os slots livres pela política do dono (THEORY §5): melhor da posição, sem lesionados, sem listados para venda, sem 30+ nos jogadores de campo. Também só escreve com `--confirmar`. `--max N` limita as ações (para primeiros testes).
- `osmbot treinos` (só leitura): sessões de treino por clube (prontas / faltam) e próximo jogo.
- `osmbot inspect-writes`: observa os pedidos de escrita do site (nomes de campos, nunca valores).
- `probe` aceita `{L}`/`{T}` e `--slot`.
- Cliente: `put`/`post` além de `get`; repete os cabeçalhos do site nas escritas.
- 8 testes novos; 59 no total.

### Alterado
- Política de treino: **guarda-redes treinam sempre o melhor, independentemente da idade** (decisão do dono; `THEORY.md` §5).

### Corrigido
- `Player.from_api`: lesionado passa a ser `unavailable > 0` (o `injuryId` não é fiável).
- A renovação sem browser falhava (400): o jogo exige o cabeçalho `AppVersion`. O bot copia agora os cabeçalhos do pedido real do site e avisa quando a versão fica desatualizada.

### Descoberto (ver `docs/DISCOVERY.md`)
- Pedidos de *claim* e de *start* de treino; `trainer` = posição do jogador; `timerGameSettingId` = definição `TrainingSession` (8h), confirmado.
- Códigos de `players` (posição, `lineup`, `unavailable` = jogos de ausência); estrutura de `timers`, `trainingsessions` e `transferplayers`.

## [0.3.0] — 2026-10-03

Sessão persistente e primeiro cliente sem browser (só leitura).

### Adicionado
- Sessão guardada em `~/.osmbot/session.json` (cookies, 0600, fora do repo), restaurada no arranque: o login deixa de se repetir. Funciona no Mac; Windows por testar.
- `src/osmbot/game/client.py`: cliente HTTP sem browser (só GET) que renova o `access_token` sozinho pelo `tokenRefresh` e guarda os tokens novos. Os códigos OAuth do cliente são apanhados do pedido do próprio site para `~/.osmbot/client.json` (0600, nunca versionados).
- `osmbot status`: clubes ativos, ranking, orçamento e boss coins.
- `osmbot probe <caminho>`: GET de leitura que mostra só a estrutura da resposta (nomes e tipos, nunca valores).
- Comandos de descoberta: `inspect-session`, `token-info`, `inspect-network`.
- Dependência `certifi` (o Python do Homebrew no Mac não traz certificados).
- 7 testes novos (cliente e status); 51 no total.

### Corrigido
- O "login funciona" de 0.2.0 não guardava a sessão: os tokens do OSM são cookies de sessão e o Firefox apagava-os ao fechar. Perfil persistente abandonado.

### Descoberto (ver `docs/DISCOVERY.md`)
- `access_token` dura 20 min; `refresh_token` 7 dias com prazo deslizante; formato do `tokenRefresh` (OAuth2); autenticação por `Authorization: Bearer` confirmada.

## [0.2.0] — 2026-09-28

Primeiro contacto real com o jogo: login confirmado a funcionar.

### Decidido
- D-013 encerrada: dono deu OK explícito (regra 5) para contacto real com o jogo — login e leitura, para já.
- D-004 emendada: os testes começam já na **conta principal**, não numa conta secundária como estava previsto; fica registado que isto expõe a conta principal diretamente ao risco de ban (sem isolamento de "conta descartável").

### Adicionado
- `osmbot login`: abre uma janela real de Firefox (Playwright, perfil persistente guardado fora do repo em `~/.osmbot/firefox-profile`) para um login manual único; a sessão fica guardada e é reutilizada sozinha depois — sem copiar cookies nem guardar password. **Confirmado pelo dono a funcionar.**
- `osmbot dashboard`: abre a sessão guardada na área do clube, passo de descoberta antes de qualquer extração de dados.
- `pyproject.toml`: dependência de runtime `playwright` e entry point `osmbot`.

### Corrigido
- `choose_formation`: `similar_margin` passa a ter valor por omissão **2** (regra do dono: dentro de ±2 pontos ainda considera 4-3-3), deixando de ser obrigatório.

### Notas técnicas
- Login foi tentado primeiro em Chromium (Playwright); o popup de login do Facebook (única via de login desta conta) bloqueia o build "Chrome for Testing", mesmo com login manual por uma pessoa real. Resolvido trocando para **Firefox** (também gerido pelo Playwright, sem instalar nada como programa no Windows).

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
