# Worklog

Entradas mais recentes primeiro. Cada sessão: o que se fez · o que ficou por fazer · próximo passo.

## 2026-10-16 — Análise do mercado do FC Van (PT-LA-02-0095-N)

- **Dinheiro e lista do FC Van** (pedido do dono, só leituras): 215,8 M no saldo, 0 na poupança; 2 de 4 vagas usadas (de Gea e B. Fernandes a 2,5×, há 12,5 h); a liga compra ao máximo (várias vendas a 2,5× nas últimas 18 h). `sale_picks`: revendas A. Rossi (GR 96, 1,20×, +25,5 M), Parrott (ATA 88, 1,21×, +21,7 M), Léo Jardim, Chevalier; reforço Pacho (DEF 117, 128 M, 1,24×, sobre Chalobah 107). Nada comprado (comprar pede OK, regra 5).
- **Falha vista no `sale_picks`:** o "titular mais fraco" conta o B. Fernandes (96), que está no 11 **e à venda**, e ignora o Merino (111) no banco; por isso Gibbs-White e Paquetá aparecem como reforço. Por corrigir, se o dono quiser.
- **O dono comprou o Pacho** (127,13 M, no 11 no lugar do Chalobah). O de Gea vendeu entretanto (+97,3 M; saldo 185,95 M). O Diomande vendido (id …783, valor 44,7 M) **não** é o Diomande 116 do mercado (Ajax, valor 99,9 M): só o nome é igual.
- **Erro meu:** sugeri o Merino no 11 sem ver a condição física (75, amarelo; §16 manda descansar). O B. Fernandes (100) no 11 está certo; o risco é ele vender antes do jogo e só sobrarem médios cansados ou o enchimento.
- **Revendas ou reforço?** (pergunta do dono): com 186 M, recomendei o **Gibbs-White** (MED 118, 26 anos, 168,1 M, 1,28×, SALE) em vez das revendas: com o B. Fernandes à venda e o Merino cansado, os médios ficam abaixo da estrutura de 5 (§7.1). As revendas recomeçam quando o B. Fernandes e o Chalobah venderem (~147 M).
- **O que o dono fez** (lido a seguir): comprou o Gibbs-White (168,07 M) para o 11; 17,9 M na poupança, saldo 0; à venda as 4 vagas: Chalobah 91,26 M (75 %), Anton 83,17 M (máx.), B. Fernandes 55,77 M (máx.), Wharton 217,18 M (75 %). Banco com o lugar 15 vazio (falta um ATA). Sugeri o Wharton (115, condição 97) no 11 em vez do B. Fernandes (96): os dois estão à venda e o Fernandes deve vender primeiro.
- **Dono: MCO ≠ MC** (Wharton MCO, B. Fernandes MC): só se trocam com uma troca de posição universal, em emergência. Registado em `THEORY.md` §7.9. O `sale_picks` também compara só pela posição geral (ATA/MED/DEF/GR): a corrigir com a posição específica, se o dono quiser.
- **Qarabag** (só leituras): pré-época (semana −1), 40,8 M de saldo + 2,2 M na poupança, 1 de 4 vagas (Sawo, 4,75 M, há 37 h); a liga compra ao máximo (31 de 31 vendas). Recomendado: Saliba (DC 95, 27,2 M, 1,45×) para o lugar do Mustafazada (DC 67), e depois o Courtois (GR 89) ou o Elanga (ED 80); banco com 3 lugares vazios.
- **Os 6 jogadores do Qarabag a 1,0× eram 2 pacotes** (ouro e prata) abertos pelo dono: `type` 7 nas transferências, lotes de 3 com o mesmo segundo. Lotes iguais de outros treinadores (7–37 M) **não** são pacotes de certeza (correção do dono: especulação minha; o `type` 7 também cobre os 44 de 07/10). `DISCOVERY.md` §3. Sugerido revender os que sobram ao máximo (as 3 vagas livres).
- **Qarabag depois do dono:** 4 de 4 vagas ao máximo (Sawo, Fofana 9,44 M, Farhan 3,52 M, Kolke 3,36 M); saldo 0 e 43,0 M na poupança; Saliba não comprado; banco ainda com os lugares 14–16 vazios.
- **Dono:** na pré-época o banco vazio não importa (amigáveis não lesionam, já em §6). O Saliba fica à espera de propósito: a liga só tem 2 treinadores reais. `THEORY.md` §7.7.
- **Kolke vendido** (3,36 M, ~1 h na lista). GR no mínimo (2). Para a vaga livre recomendei listar o Mouaddib (ATA 62, ~4,25 M ao máximo), sem gastar a poupança guardada para o Saliba.
- **Janela das boss coins confirmada** na captura `20261015-160828-loja.png` deste PC: "Unclaimed Boss Coins" + Claim, o que o `UNCLAIMED` da 0.12.3 já aceita. `THEORY.md` §17 e `DISCOVERY.md` deixam de a ter como suposição.
- **Hoje ainda (lido às ~14 h):** FC Van joga às 18:36 (o B. Fernandes, titular, continua à venda; lugar 15 do banco vazio); Betis às 21:09 (Donnarumma com condição 77; van Dijk e Messi, titulares, à venda, e o Maguire, o DC do banco, também; Rice à venda há 145 h); Qarabag com o fim do dia às 23:08 (banco já cheio).
- **Preço errado do Diomande: causa encontrada.** O `~/.osmbot/sales.json` é por PC. Este PC leu pela última vez a 15/10 às 17:59 (Diomande a 104,08 M, desde 13/10); à noite, no DESKTOP-KAM70RR, o dono voltou a listá-lo a 75 % (15/10 23:15), e esse PC registou bem a venda (83,97 M, 06:52). Hoje às 11:45 este PC comparou com o estado antigo e registou uma 2.ª venda, com o preço e as horas antigos. A Konsa, listada e vendida com este PC desligado, só aparece no registo do outro. Correção possível: tirar o preço e a hora da venda das transferências da liga (`{liga}/transfers`), e não do último anúncio visto.
- **Hover do cartão de compras:** desenhado com dados reais (só leituras), com 3 reforços: cabe inteiro (665 px), "reforço (> D. Muñoz 108) · pechincha" sem corte; o corte da captura não se repete aqui. Visto de passagem: a coluna "Valor" mostra a razão ("1.23×", com ponto em vez de vírgula).
- **Os 3 pontos do `sale_picks`** (titular à venda, posição específica, abaixo da média): o dono confirma que estão certos. **Feito:** `transfers/engine.weak_spots` (titular à venda = o melhor do resto na mesma posição específica, sem ninguém = 0; média do 11 assim) e `sale_picks` por posição específica (`especifica` no `sale_rows`); só as listagens do próprio clube contam como "à venda". Com dados reais: Qarabag sem o GR 79, FC Van com o MC = Merino 111, Betis com o ED aberto (Messi à venda, sem ED no banco). `THEORY.md` §7.9, D-058.
- **Coluna do hover:** "Valor" → "× valor", com vírgula ("1,23×").
- **Vendas pelas transferências da liga:** `board/info.settle_sales`; `sales.update(transfers=..., team_id=...)` lê `{liga}/transfers` só quando há venda e tira daí o preço e a hora ("vendido às"); com outro preço, "listado de novo com o bot parado" e sem "demorou". `track_sales` guarda o id do jogador na venda. 408 testes. **O bot aberto tem de ser reiniciado** para usar o código novo.
- **0.13.2** (pedido do dono; 0.13.1 ficou só como rótulo de um commit de registos, sem release): `pyproject`, `__init__`, `CHANGELOG`, `README` (estado), `dist` reconstruído neste PC e `dist/release-notes-v0.13.2.md`. 408 testes. Commit e `gh release create v0.13.2` entregues ao dono.

## 2026-10-15/16 — `dist` 0.12.2, 0.12.3 e 0.13.0, mercado do jogo (DESKTOP-KAM70RR)

- **Pull** (pergunta do dono): sem alterações locais, 2 commits atrás, avanço direto; só a versão mudou no `pyproject`. Feito pelo dono.
- **`dist` reconstruído na 0.12.2** (pedido do dono): 403 testes; portátil 553 MB, zip 206 MB, instalador 148 MB; `status` da versão portátil testado; notas em `dist/release-notes-v0.12.2.md` (só a 0.12.2: a 0.12.0 e a 0.12.1 já saíram do outro PC).
- **Análise dos erros de hoje (registos, pedido do dono):**
  - *Vídeos "botão não encontrado" 13:04–16:31 (trabalho):* começam 7 min depois de o prémio das missões `DailyMissionsRewardBC_5` ir para o inventário (12:57) e acabam quando a 0.12.1 o passa para a carteira (16:38); o reinício das 15:51 (versão antiga) não resolveu. Os prémios `Energy_2` (13/10) e `CF_3M` (14/10) no inventário não bloquearam nada. **Hipótese:** com boss coins por reclamar, o jogo abre uma janela ("Boss Coins não reclamadas", vista pelo dono) que tapa a loja e o treino, e o `_dismiss_matchday` não a conhece. Confirmar com as capturas em `~/.osmbot/failures/` do PC do trabalho (`20261015-1…-loja.png`/`-treino.png`). A 0.12.1 já evita a causa.
  - *"string indices must be integers" (14/10 02:37 em casa, 15/10 16:47 no trabalho):* `OsmClient.get` devolve o texto da resposta quando o jogo não manda JSON e os chamadores não olham para o estado; o erro real (estado e mensagem do jogo) perde-se. Às 16:47 falharam todos os GETs em 1 s (loja, treino, quadro): resposta de erro do servidor nesse momento; o estado exato não ficou registado. A 14/10 coincidiu com 403/404 da liga nova do Qarabag.
- **Correções** (pedido do dono: "como corrigimos tudo?"; ele confirmou que a janela lhe apareceu no jogo):
  - `ads._dismiss_matchday` carrega em **Claim** também na janela das boss coins (`UNCLAIMED`: "Unclaimed Energy", "Unclaimed Boss Coins" e variantes; título em inglês **[S]**). D-055, `THEORY.md` §17, `DISCOVERY.md`.
  - `OsmClient.request`: uma **leitura** com 5xx ou 429 levanta `GameUnavailable` (um `OSError`), com "o jogo respondeu N a caminho: início da resposta"; o ciclo espera e tenta outra vez como sem rede (a parte dos vídeos e o quadro só registam o erro). As escritas e os 4xx das leituras continuam a devolver o estado como antes.
  - 406 testes. **Não está no `dist`** (0.12.2); entra na próxima versão. **Por verificar:** as capturas no PC do trabalho, e o título real da janela da próxima vez que aparecer.
- **Janela, 9 pedidos do dono** (escolhas: faixa de fundo, marca só no hover, SALE em faixa azul): tabela do campeonato e do valor do plantel com a linha do clube numa faixa da cor do clube (`tip_grid(colour)`, `blend`) e células sem quebra ("965,81 M" inteiro); certo verde / "!" amarelo junto ao objetivo, nunca na pré-época (`table_view` → `mark`); estádio 3/3, o texto e o "MAX" na cor do clube (`vivid`); hover do adversário em linhas (`opponent_tip`, `tip_pairs`); treinador universal com "Treinador universal" a cinza por cima do nome e o nome centrado (o número de jogos vazio ocupava espaço); médico/advogado sem ninguém quase a preto e branco, sem o ser (`picture(keep=0.35)`); hover do treino secreto/estágio sem repetir o nome; SALE numa faixa azul (`SaleStripe`: etiqueta SALE e marcas, jogador, preço e lucro; hover em tabela). Corrigido também o `&gt;` e o corte do hover do SALE. `THEORY.md` §19. 406 testes; prints com dados reais (só leituras, `widget.grab()`). **O dono ainda acha o SALE "feio"**: mostrado o novo para validar.
- **Versão paga (conversa, para o futuro):** venda futura com repo privado nessa altura, licença sem a qual não há boss coins, plano recomendado com a peça das boss coins vinda de um servidor do dono, teste de compra com um colega. Registado em **D-056 (Em aberto)**; nada construído.
- **Versões (pergunta do dono):** a 1.0 passa a ser a primeira versão vendida, com plano por fases: agora, congelamento, versão paga 0.20+, 1.0.0-rc com o colega, 1.0.0 (**D-057**). Atualizados `CLAUDE.md` (convenção), `CHANGELOG.md` (cabeçalho) e `PROJECT_BRIEF.md` (critérios do 1.0: os de 2026-10-09 passam a fechar o congelamento).
- **0.12.3** (pedido do dono): versão em `pyproject.toml` e `__init__.py`, `CHANGELOG`, `README` (estado), `dist` reconstruído e `dist/release-notes-v0.12.3.md`. 406 testes.
- **Para a 0.13.0 (pedidos do dono):** círculos cheios na cor do clube a 70 % em vez de verde (`soft(colour, FULL)`, `THEORY.md` §19); médico, advogado e treinador universal alinhados pelo topo (o círculo do universal subia); "Treinador universal" cortado no ecrã do dono ("Treinador universa"): o título encolhe a letra até caber (`fit`).
- **Mercado do jogo (perguntas do dono, só leituras e registos):** os anúncios do jogo descem ~4 %/dia (1,5× → 1,2× em ~6 dias, nunca sobem); compras ao jogo entre 1,20× e 1,79×. `DISCOVERY.md` §3. O dono aceitou: **pechincha até 1,25×** (`BARGAIN`) e **registo de todos os anúncios do jogo** em `transferencias/jogo/` (primeiro e último preço; `sale_changes` guarda `preco_inicial`). 406 testes. Estratégia de compra a partir dos registos (vagas sempre cheias; revenda de jogadores de 10–40 M de valor, os mais baratos face ao valor; reforços sem pressa) e **cartão com a melhor hipótese e as 3 melhores no hover** (D-058, `sale_picks` sem a vaga livre, `FLIP_VALUE`, etiqueta SALE só quando a melhor a tem). 406 testes.
- **Mercado do dono (2026-10-16, só leitura):** 12 jogadores à venda, quase todos ao máximo com revenda abaixo de 100 M (como a estratégia). A rever pelo dono: um MED à venda há 131 h (a esse preço a mediana é ~32 h), dois titulares do Betis à venda antes do jogo, um ATA de 19 anos a 75 %.
- **Hovers com o círculo verde:** cantos brancos à volta da marca (o `render` do `StepIcon` desenhava o fundo da janela); agora só `DrawChildren`.
- **0.13.0** (pedido do dono): versão, `CHANGELOG`, `README`, `PROJECT_BRIEF`, `dist` e `dist/release-notes-v0.13.0.md`. 406 testes.
- **Pesquisa web de estratégia (pedido do dono, depois da 0.13.0):** `DISCOVERY.md` §6d. Bónus de nacionalidade (6 titulares da mesma nacionalidade, ~25 % segundo um moderador) **testado em 251 jogos e não confirmado** (−0,28 ±0,17 golos depois de força, casa e treinador humano; a força do jogo também não o inclui). O resto: treino secreto antes do estágio, avançados vendem mais devagar (confirmado de leve nos registos: ~1,6×).
- **`OSMPro/` (pedido do dono, "pode ir pro repo"):** listas de vídeos de OSM de dois canais portugueses, lidas com o `yt-dlp` (só a lista): @OSMPROworld (43) e @andresantana_yt (1136 de OSM em 1445, por categoria: dicas, táticas, torneios, 17 séries do Modo Carreira…). Datas exatas em todos, exceto 3 só para membros do canal (só o ano, "~2021"). O dono explica depois para que são.
- **Próximo passo:** o dono faz commit, push e o Release da 0.13.0; confirmar na janela o hover do cartão de compras (na captura, a etiqueta "reforço (> …)" aparecia cortada) e, no PC do trabalho, o título real da janela das boss coins.

## 2026-10-15 — Pré-época e tempos em dias (PT-LA-02-0095-N)

- **Erros de rede de manhã** (pergunta do dono): `Page.goto` com timeout, boss coins que não subiram e `getaddrinfo failed` às 10:43, por o portátil andar sem rede. O bot recuperou sozinho; não foi preciso reiniciar.
- **Qarabag sem amigáveis** (pergunta do dono): está na pré-época (`weekNr` −2) e o 1.º jogo é daqui a 59 h. A regra fazia os amigáveis só nas 16 h antes do jogo.
- **Pré-época com o mesmo tratamento** (pedido do dono): depósito na poupança e 4 amigáveis em cada dia, à hora do 1.º jogo menos N dias (`prematch/policy.preseason`, `day_end`; `prematch._day_time`; `savings`, `timeline` com `club["week"]`). D-054, `THEORY.md` §6/§13, `DISCOVERY.md`. Simulação com dados reais (só leituras): o dia do Qarabag acaba às 23:08, depósito às 23:03, faria já 2 amigáveis.
- **Tempos em dias** (pedido do dono): `dashboard.span` mostra "2 dias e 10h59" a partir de 24 h (janela, registo, `treinos`).
- 399 testes. **O bot aberto tem de ser reiniciado** para usar o código novo.
- **Hover no valor do plantel** (pedido do dono, com print do jogo): a tabela por valor à volta do clube (1.º → os 2 de baixo; senão 1 acima e 1 abaixo) com valor, jogadores e média; sem pedidos novos ao jogo (os valores já eram lidos). `board/info.value_table`, `clubinfo` (`value_table`), `gui/view.squad_view` (`table_tip`), `gui/window`, `i18n`. `THEORY.md` §19. 401 testes. Visto com dados reais (só leituras): bate com o print (Betis 1032,74 M, Barcelona 939,4 M, Real Madrid 533,88 M).
- **Sem hover nos círculos da força** (pedido do dono: redundante), o do clube e o do adversário; o hover no nome do adversário deixa de dizer "Força" (o círculo já mostra) e fica só o valor do plantel. `gui/view.rating_badge`, `squad_tip`.
- **Versão 0.12.0** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (8a, 12a); `dist` reconstruído neste PC (portátil 553 MB, zip 206 MB, instalador 148 MB; versão e `status` da versão portátil confirmados); notas em `dist/release-notes-v0.12.0.md`. Commit e `gh release create v0.12.0` entregues ao dono.
- **Calendário em vez de "DIÁRIAS"** (pedido do dono): ícone desenhado por nós no estilo do relógio (`img/calendar.svg` → `gui/assets/calendar.png`, 128 px, aro prateado e topo azul); "Diárias" no hover. `gui/window`, `i18n`. Visto num print fora do ecrã.
- **"Hoje: prémio por saber"** (pergunta do dono): o início de sessão de hoje foi reclamado às 05:00 noutro PC; depois disso o jogo só mostra os dias seguintes e este PC nunca o tinha anotado. **Corrigido:** cada leitura guarda os prémios por número do dia (`~/.osmbot/inicio_sessao_dias.json`, `rewards/policy.track_seen`), e o de hoje sai daí; o hover mostra também o de amanhã (`login_tomorrow`). Sem nota: "Hoje: reclamado (prémio não visto)". 402 testes.
- **Calendário maior** (pedido do dono): 28 → 34 px.
- **"Boss Coins não reclamadas" (5) no jogo** (pergunta do dono): era a recompensa do dia das missões (`DailyMissionsRewardBC_5`, 12:57), guardada no inventário pela regra "nunca usar itens" (D-020), que eu tinha aplicado também ao dinheiro. **Corrigido (D-055):** boss coins e dinheiro do clube do inventário vão para a carteira (`claim_money`, no fim das recompensas); dinheiro do clube para o clube com menos dinheiro (escolha do dono). 403 testes. Simulação real (sem escritas): 5 boss coins + 3 M para o Qarabag (4 M, o mais pobre). Não fiz a escrita: fica para o bot ativo depois de reiniciado.
- **Textos das diárias** (pedido do dono): "Prémio do dia" → "Prémio diário" (barra, por reclamar, consola); hover sem prémio: "Sem prémio do dia" e o de amanhã por baixo. 403 testes.
- **Versão 0.12.1** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`; `dist` reconstruído neste PC; notas em `dist/release-notes-v0.12.1.md`. Commit e `gh release create v0.12.1` entregues ao dono.
- **Calendário sem hover** (pedido do dono, depois do `dist` 0.12.1): sai o "Diárias" ao passar o rato. Só no código; entra na próxima versão.
- **Hover do campeonato "horrível"** (dono): o título ficava colado à 1.ª linha e nada alinhava. O dono escolheu a tabela "como a do jogo" (entre 3 maquetes): # · Clube · J · DG · Pts (jogos e diferença de golos de `standings`) e o objetivo por baixo; o hover do valor do plantel passou ao mesmo formato (# · Clube · Valor · Jogadores · Média). `board/info.league_summary`, `gui/view` (`table_view`, `squad_view` devolvem a tabela), `gui/window.tip_grid`, `i18n`. 403 testes; print com dados reais. Só no código (depois do `dist` 0.12.1).
- **Versão 0.12.2** (pedido do dono, depois de publicar a 0.12.1): hovers em tabela e calendário sem hover. `pyproject`, `__init__`, `CHANGELOG`, `README`; `dist` reconstruído; notas em `dist/release-notes-v0.12.2.md`. Commit e `gh release create v0.12.2` entregues ao dono.
- **Por verificar:** se o juro é mesmo pago na pré-época (comparar a poupança do Qarabag antes e depois das 23:08) e a que hora muda a jornada.

## 2026-10-14 (noite) — Pull e `dist` 0.11.12 (DESKTOP-KAM70RR)

- **Pull bloqueado** (pergunta do dono): `DISCOVERY.md` e `WORKLOG.md` alterados aqui e no trabalho. Resolvido pelo dono com `stash` → `pull` → `stash pop`, sem conflitos.
- **`dist` reconstruído na 0.11.12** (pedido do dono): 387 testes; portátil 553 MB, zip 206 MB, instalador 148 MB; `status` da versão portátil testado (3 clubes); notas em `dist/release-notes-v0.11.12.md`.
- **Bot no servidor?** (pergunta do dono, só explicação): possível, mas login do Facebook, vídeos (IP de centro de dados, [H]) e risco de ban complicam; recomendado um Pi/PC velho em casa. Nada decidido.
- **Médico de 8 h no Super Staff** (pergunta do dono): o bot mandava o `timerGameSettingId` 48 fixo e o jogo deu o temporizador normal (`DISCOVERY.md`). O mesmo no advogado (45) e no analista (60). **Corrigido (pedido do dono: "corrige tudo o que é passível de dar erro desse género"):** `game/timers.py` procura o id e a duração pelo nome nas definições da liga (como os treinos); `medical` e `prematch` usam-no, e o registo, a hora de levantar e o círculo da janela usam a duração lida ("(3 h)", "(15 min)"; `i18n` genérico). Círculos do médico/advogado e duração do estádio pela definição da liga (`clubinfo.timer_minutes`, `dashboard.session_length`/`upgrade_length`; acabou o palpite fixo de 4 h no estádio); barra do estádio na consola idem. 390 testes. Leitura real (só GETs): o Super Staff acabou entre as 22:59 e as 23:10, as 3 ligas já dão 48/480; o D. Muñoz fica com as 8 h (posto antes da correção). **Não está no `dist`**: entra na próxima versão; a janela aberta tem de ser reiniciada.
- **Erro do VS Code "Error acquiring .NET!"** (print do dono): a extensão C# pedia o .NET 10 e o download dava timeout. O dono instalou `Microsoft.DotNet.AspNetCore.10` e `Microsoft.DotNet.Runtime.10` (winget). Nada a ver com o bot.
- **4-4-2 B sem extremos em forma** (dono: os 2 extremos do Betis cansados, trocou para 4-4-2 B e o bot dava "devia ser 4-3-3 A"). Regra do dono (`THEORY.md` §1): o 4-3-3 A precisa de 1 EE e 1 ED em forma (≥ 80 %, sem lesão/castigo, plantel todo); senão o **4-4-2 B** conta como certo (só esse). O passo "Onze" fica verde com "ⓘ" e a nota no hover ("Aceite"); com outro aviso no mesmo passo (o desarme), a nota vem a seguir. `theory/lineup` (`tactic_notes`, `_no_wingers`), `clubinfo`, `gui/view`, `gui/window`, `i18n`. 393 testes. Leitura real: Betis 4-4-2 B (Díaz 77 %, Messi 78 %) sem o aviso da formação; fica o do desarme (árbitro muito brando → Extremo).
- **Desarme com árbitro muito brando** (dono: "pode ser agressivo, não precisa ser extremo"): o aviso aceita Agressivo ou Extremo, como no brando (`THEORY.md` §3, `lineup.ACCEPTED`). 393 testes.
- **Versão 0.11.13** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (9d); `dist` reconstruído neste PC (portátil 553 MB, zip 206 MB, instalador 148 MB; `status` da versão portátil testado); notas em `dist/release-notes-v0.11.13.md`. Commit e `gh release create v0.11.13` entregues ao dono.
- **Rival do Qarabag** (pergunta do dono): o outro humano da liga vendeu a ~2,5× como o dono, mas comprou 4 de 6 jogadores **ao valor** (1,00×; 1,13× no total) contra 1,48–1,78× do dono (1,67×): com o mesmo dinheiro trouxe quase o dobro do valor. Começaram juntos (02:37/02:45; corrigi um "21 h antes" errado). Como apanhou jogadores ao valor: por apurar ([H] anúncios curtos ao valor).
- **SALE no cartão do clube** (OK do dono, `THEORY.md` §7.7): os 3 SALE que cabem em conta + poupança, pelo lucro estimado de revenda (máximo ≈ 2,5× o valor [H], 75 % acima de 100 M); "reforço" quando bate o titular mais baixo da posição geral (aparece sem vaga de venda), "pechincha" ≤ 1,1×, negócio só com vaga livre; "?" no lucro quando a liga não vendeu a ≥ 2,4× nos últimos 3 dias. `transfers/engine` (`sale_picks`, `resale`, `sells_at_max`), `clubinfo.league_sells_at_max` (transferências da liga, 10 min), `dashboard`, `gui/view.sale_view`, `gui/window`, `i18n`. 396 testes. Leitura real: Betis sem vaga → 3 reforços DEF sobre o Bartra 69 (titular no lugar do Guéhi cansado); FC Van e Qarabag sem linha. D-053.
- **Versão 0.11.14** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (item 11 feito, 9d); `DECISIONS` D-051 (temporizadores pelo nome), D-052 (4-4-2 B e desarme), D-053 (SALE no cartão); `dist` reconstruído neste PC (portátil 553 MB, zip 206 MB, instalador 148 MB; `status` da versão portátil testado); notas em `dist/release-notes-v0.11.14.md`. Commit e `gh release create v0.11.14` entregues ao dono.

## 2026-10-14 (tarde) — Super Staff: círculos dos treinos e duração do universal (PT-LA-02-0095-N)

- **Pull com conflito** no `WORKLOG` (stash local): resolvido; a nota do Inno Setup deste PC ficou numa linha própria.
- **Super Staff confirmado** nas 3 ligas (treinos 120 min, universal 90, analista 15, médico/advogado 180, olheiro 240): visto às 06:49–06:58 no DESKTOP-KAM70RR e às 09:08 aqui. Início exato por apurar (a leitura é de hora a hora).
- **Treinos postos antes do evento** (03:40–05:18) acabaram 09:40–11:40 (~6 h, não 8 h; causa por verificar: vídeos ou o evento a encurtar). Os postos no evento duram 2 h.
- **Atrasos a recolher** (perguntado pelo dono): ~1 h no Betis (acabou ~11:18, recolhido 12:16). O bot esteve nos vídeos da loja (11:20–11:42) e depois sem rede até às 12:15 (`getaddrinfo failed`). **Proposta, sem OK:** interromper os vídeos da loja quando há um treino pronto.
- **Especialistas no FC Van:** Marmoush e Trossard empatados (ataque 111, rating 111); ganha o id mais baixo (desempate [S] do `THEORY.md` §4). Perguntado ao dono que desempate quer (recomendado: manter quem já lá está). **À espera.**
- **Círculos dos treinos na janela** (OK do dono): eram sempre desenhados contra 8 h (com 1h39 por fazer de 2 h apareciam ~80 % cheios). Agora usam a duração da liga (`gamesettings` `TrainingSession`/`TrainingUniversalSession`, `clubinfo.session_minutes`); um treino com mais tempo por fazer do que isso começou antes do evento e fica com 8 h (`dashboard.session_length`, decidido a 1.ª vez que se vê). Também na barra da consola e no círculo do universal.
- **Frase do universal** (OK do dono): "a treinar (6 h)" era fixo; agora diz a duração das definições ("1h30" no Super Staff).
- 381 testes. Leitura real (só GETs): círculos a 20 % com 1h35 de 2 h. **A janela aberta tem de ser reiniciada** para usar o código novo.
- **Causa real do atraso das 11:43–12:15:** o PC adormeceu ("Modern Standby", registos do Windows), não foi a rede. **PC acordado com o bot ligado** (escolha do dono: ecrã sempre ligado; `osmbot/awake.py`, chamado no início e no fim do `run_active`; o registo diz "Bot ligado · o PC não adormece"). D-048, `DISCOVERY.md`.
- **Treinos antes dos vídeos** (OK do dono): a série da loja pára entre vídeos com um treino pronto ("Loja: pausa, há treinos para recolher"); os vídeos de treino e de dinheiro também esperam (`ads.run_shop_ads(training_ready=)`, `loop._training_ready`, `loop._all_ads`). `THEORY.md` §12.2.
- **Treino secreto e estágio no pré-jogo** (pedido do dono): no fim da lista, ícones do jogo tirados do CSS do site (`gui/assets/camp.png`, `secret.png`); marcado = verde com anel verde, não marcado ou sem jogo = cinzento com ícone a cinzento, razão no hover. `clubinfo` (`BOOSTS`, passos 8 e 9 do `matchpreparation`), `gui/view` (`prep["boosts"]`), `gui/window` (`BoostIcon`, `BoostList`; `picture(alpha=)`), `i18n`. Print fora do ecrã com dados reais (um "marcado" simulado). `THEORY.md` §21, D-033, D-048.
- **Desempate dos especialistas (dono):** ataque igual → ganha quem tiver o resto das stats melhor (overall + defesa); só depois rating e id. Marmoush 65+19 contra Trossard 73+36 → Trossard (o que já estava no jogo). `theory/specialists._attack`, `THEORY.md` §4. 386 testes.
- **Hora de início dos eventos** (escolha do dono, ponto 3): definições lidas de 10 em 10 min entre as 05:30 e as 07:00; o registo diz "(mudou entre HH:MM e HH:MM)" (também em inglês). `events.check_every`, `THEORY.md` §14, `DISCOVERY.md`. A resolução real depende de quem lê o quadro: 3 min com a janela à vista, 15 min escondida. Próximo teste: Golden Oldies, 17/10. 387 testes.
- **Análise (ponto 4):** o evento não encurta os treinos já a correr; os "~6 h" eram 8 h menos 2 h de um vídeo de treino (bate sessão a sessão; `DISCOVERY.md`). Ideia, sem OK: não pôr treinos de 8 h pouco antes de um evento de treinos.
- **Versão 0.11.11** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`; `dist` reconstruído neste PC (portátil 553 MB, zip 206 MB, instalador 148 MB; `status` da versão portátil testado); notas em `dist/release-notes-v0.11.11.md`. 387 testes.
- **Ideia do dono, para ver em breve:** gastar umas boss coins para acabar um treino de 8 h que ainda tem horas pela frente quando começa um evento de treinos de 2 h (liberta o lugar para ~3 treinos de 2 h; ~25–35 treinos a mais no dia). O dono (2026-10-14): o preço em boss coins depende do tempo que falta para acabar; não sabe quanto. Por saber: o preço exato (só visto o "boost" do estádio), se o progresso é o mesmo e a hora de início (17/10). Alternativas grátis: vídeos de treino nesses treinos; não pôr treinos de 8 h 2–3 h antes. Primeiro passo: ler o preço no jogo (só leitura).
- **Pontos 1 e 2 da lista** (aviso de estágio em jogos perigosos, formação do adversário): o dono diz que não são precisos para já.
- **À espera do dono:** ver no jogo um treino secreto/estágio marcado para confirmar o verde.
- **Aviso "Formação 5-2-3: devia ser 4-3-3 A" no FC Van** (pergunta do dono; leitura real às 17:24, só GETs): a tática no jogo é mesmo `formation` 523 A (5 DEF, 2 MC, EE-PL-ED; "Posições" verde, todos no sítio). Próximo jogo: fora, contra o Shirak (2.º, jogo perigoso); força 109 contra 107 (FC Van +2 %; com ~5 % da casa, Shirak ~+3 %). Pela regra (§1) dá 4-3-3 A nos dois casos; o 5-2-3 não está no `THEORY.md` e não há dados dele. O aviso está certo; perguntado ao dono se o 5-2-3 foi de propósito.
- **Regra da formação mudada (dono: 5-2-3 de propósito, "vario entre as taticas de 5 defesas"; D-049):** adversário mais forte por qualquer margem → 5 defesas, qualquer uma; aviso "devia ser de 5 defesas (adversário mais forte)" (+ inglês). `theory/tactics`, `theory/lineup`, `i18n`, `THEORY.md` §1 e §21. 386 testes. Neste jogo (109 contra 107, sem casa/fora na regra) o aviso continua: o FC Van é mais forte.
- **Pergunta do dono: o "mais forte" conta os +3 % da sequência de logins e os +5 % de casa?** Não: compara só o rating dos dois planteis. `GET user/dailylogin` dá `matchBoost: 3` (23 dias seguidos; leitura às ~17:40). Com os dois: FC Van 109 × 1,03 ≈ 112,3 contra Shirak 107 × 1,05 ≈ 112,4 (quase igual; o boost de login do adversário não se sabe). Proposto incluir os dois, à espera do OK.
- **Bónus de logins do adversário (pedido do dono, com print: "+3 %" nos dois lados):** no código do site é `GET user/dailylogin/{userId do treinador}/matchboost`, só depois da análise e só com treinador humano (`DISCOVERY.md`). Primeira tentativa bloqueada pela verificação de permissões; com o OK do dono, lido: Shirak `matchBoost` 3, FC Van 3. Com os bónus e a casa: FC Van ≈ 112,3 contra Shirak ≈ 115,7 → 5 defesas (o 5-2-3 do dono estava certo). À espera do OK para pôr os bónus e a casa na regra.
- **Bónus e casa na regra (OK do dono, D-050):** `theory/tactics.match_strength`, `game/clubinfo._match_strengths` (logins do dono e do adversário, estágio 25 % e treino secreto 2 % marcados, +5 % em casa, nada em campo neutro: `next_match` dá `neutral`). Leitura real: FC Van sem aviso no "Onze" (5-2-3 aceite). 387 testes. Achado: o campo do estádio dá "+0/2/4/6 % home advantage" por nível; o estádio dos outros dá 403.
- **Versão 0.11.12** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (9d); `dist` reconstruído neste PC (portátil 553 MB, zip 206 MB, instalador 148 MB; `status` da versão portátil testado); notas em `dist/release-notes-v0.11.12.md`. Commit e `gh release create v0.11.12` entregues ao dono.
- **Nota (dono): voltar a medir os 5 % de casa** pelos registos dos jogos, e ver se dependem do nível do campo (`THEORY.md` §1).

## 2026-10-14 — Posições específicas, mercado sem evento, domínio mundial (0.11.10, Windows)

- **O que está mal na estratégia** (pergunta do dono): transferências parecidas com as do 1.º (FC Van +310 M em 20 revendas, ZSKA +338 M em 15); a diferença é o dinheiro dele e ~130 M deixados nas vendas a 75 % acima de 100 M em eventos; proposta (sem OK ainda): pedir o máximo nos eventos.
- **Aviso errado no Betis** ("Dembélé no banco, Messi a jogar"): comparava toda a posição geral. O dono testou no jogo: as barras não mudam, mas o jogo avisa "os jogadores rendem mais na sua posição específica". Agora o "suplente melhor que titular" só compara a mesma `specificPosition`; a ordem do banco fica pela geral (dono). `THEORY.md` §21, `DISCOVERY.md`. 376 testes; FC Van e Betis sem avisos do banco.
- **Hover das "Posições"** (OK do dono): mapa lugar → posição específica de cada formação lido no código do site e confirmado pela checklist real (Betis 9/11: Messi e Haaland trocados depois do teste do dono). `theory/lineup.places`/`position_warnings`, `clubinfo` (passo 2), `i18n`. Fechadas as suposições do rating por posição e do `statAtt` no `THEORY.md` (o site usa a mesma conta). 378 testes.
- **Transferências dos últimos dias** (pergunta do dono): 12–13/10 sem evento. Arménia vende ao máximo até 105 M€ em 7–41 h; Espanha não vendeu nada ao máximo (só os grandes, baratos, a 60–77 %) e as 4 listagens do Betis esperam 46–81 h (`DISCOVERY.md` §3). Corrige o que eu tinha dito: o Betis não está lento por culpa do dono, é o mercado da liga.
- **Teste do dono:** Guéhi listado a 80 % do máximo (124 M) na 2.ª liga, no lugar do van Dijk; o registo do motor acompanha.
- **Evento de hoje (Super Staff) ainda não começado às 00:48:** `gamesettings` normais, `eventnotifications` 404; no Transfer Madness as vendas só começaram às 13h (`DISCOVERY.md`).
- **Estágio hoje?** 7 jogos com estágio só de um lado: 18 pts contra ~11 esperados. Simulação do resto da 1.ª liga (força atual, taxas dos 282 jogos): ZSKA 82 % de ser campeão, Shirak 17 %, FC Van ~2 %. Recomendado: FC Van sim (direto, fora, forças iguais), Betis guardar para a taça.
- **Domínio mundial** (pedido do dono; pesquisa web sem nada sobre o OSM): `GET user/history` + `career.js`. Um país conta com campeonato **ou** taça **ou** objetivo; confirmado pelas percentagens do servidor (épocas só com objetivo contam). Os desafios contam para o país. Objetivo do FC Van: 7.º, garantido com mais 6 pontos. `DISCOVERY.md`, `THEORY.md` (o [?] fechado; a regra do dono "só feito quando não falta nada" fica por rever com ele).
- **Objetivo vs força** nas 2 ligas: o objetivo não segue a força (`DISCOVERY.md`); escolha do clube "em observação" no `THEORY.md` (dono: "vamos indo vamos vendo").
- **Versão 0.11.10** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF`, D-047; `dist` reconstruído; notas em `dist/release-notes-v0.11.10.md`.
- **Erro dos vídeos na 0.11.10 instalada** (print do dono, 01:28): "Executable doesn't exist … firefox-1555". Causa: `build_portable.py` instalava o Playwright sem versão (saiu o 1.64, que pede o Firefox 1555) e copiava o Firefox deste PC (1543, do Playwright 1.63 do venv). Correção: instala `playwright==` a versão do venv e recusa construir se a revisão do `browsers.json` não bater com a pasta copiada. `dist` reconstruído (Playwright 1.63, Firefox 1543; o Firefox da pasta abre). O dono reinstala.
- **Save novo (Azerbaijão, Qarabag) às 02:37:** treinos 403, estádio e quadro com erro. Causa: o token não listava o clube novo (`DISCOVERY.md`). Renovado à mão às 02:44; às 02:47 o bot pôs os 4 treinos e os 4 patrocinadores do Qarabag. Correção para a próxima versão (`game/client.py`): um 403 de um clube que o token não lista renova o token uma vez (no máximo de 10 em 10 min por clube) e repete. 379 testes. **Não está no `dist` da 0.11.10**: entra na 0.11.11.
- **Bot no Mac (dono, 2026-10-14):** correr a partir do código (`git pull`, venv, `osmbot`), sem versão empacotada. A fazer **no Mac, com o Claude Code de lá**, porque só lá se pode testar: 1) "Pasta dos logs" e "Capturas das falhas" abrirem no Finder (`open`); 2) impedir o Mac de adormecer enquanto o bot trabalha (`caffeinate`); 3) atalho `OSMbot.command` (pull + venv + janela); 4) o dono testa a janela (ícone na barra de cima, quadro, Login) e ajusta-se o resto. Nunca o bot ligado no PC e no Mac ao mesmo tempo.
- **Próximo:** como funcionam os desafios (podem somar países mais depressa); resultado do teste do Guéhi; pendentes da sessão anterior (vender ao máximo nos eventos acima de 100 M, casa/fora na formação…).

## 2026-10-13 (noite) — Jogos reais: análise da época e registo completo (Windows)

- **`dist` 0.11.8** reconstruído neste PC (365 testes) e notas em `dist/release-notes-v0.11.8.md`.
- **Porque não ganhou o FC Van 1-1 ZSKA** (pergunta do dono): a 1.ª resposta, só com o plantel atual, estava errada (dizia que não se via o onze nem a tática). O dono mostrou Resultados → detalhe do jogo. A causa real: aos 40' lesionou-se um defesa de 108 e entrou o 1.º suplente do banco, de 51; o golo do empate foi aos 47'. A força do jogo dava 720/782 (‑8 %), e não as equipas "iguais" que eu tinha calculado.
- **Endereços do detalhe** encontrados no script do jogo e testados (`DISCOVERY.md`): `matchData` em `matches/filter`, `playergrades`, `matches/{n}/events/{jornada}`.
- **Análise de 272 jogos** das 2 ligas (todos os clubes, jornadas 1–18; dados na pasta temporária da sessão): a força do jogo decide (mais de 15 % → 82 % de vitórias; ±3 % → 42/16/42); **casa vale ~5 % de força**; 4-3-3 A/B acima do esperado, 3-3-4/4-5-1/4-4-2 B abaixo; 5-3-2 do dono +0,70 (n=13, só dele); `strictness` 1 = muitos cartões, 5 = quase nenhum (ao contrário do nome); lesões não dependem do árbitro; o mesmo suplente de 51 entrou por lesão em 2 jogos (J9 e J18). FC Van 40 pts contra 25 esperados; Betis 48 contra 40.
- **Registo completo dos jogos (D-044, pedido do dono):** `game/matchlog.py` (`match_detail`, `detailed_ids`, `log_history` com a época inteira e pausas, `log_rounds` com a jornada primeiro). 367 testes. Época guardada já neste PC (só GETs).
- **Propostas ao dono, por decidir** (nada construído): ver resposta da sessão: aviso de suplente fraco no banco, casa/fora na escolha da formação, nome do árbitro em vez do número.
- **Árbitro esclarecido** (`DISCOVERY.md`): `strictness` 1 = muito rigoroso (ícone vermelho) … 5 = muito brando (verde); 4 = brando (azul claro), como o dono descreveu.
- **Surpresas (204 jogos com a equipa pelo menos 5 % mais fraca; 15 % ganham, 11 % empatam):** quem surpreende joga em casa (77 % das vitórias, contra 41 % das derrotas), tem treinador humano contra um clube sem treinador (adversário humano em 29 % das vitórias, contra 70 % das derrotas), está menos longe (‑13 % contra ‑19 %) e sobretudo **tem a defesa menos atrás** (‑12 % contra ‑18 %; o ataque fica parecido). Formação do mais fraco: 4-3-3 A 0,91 pts, 4-3-3 B 0,74, 4-4-2 A 0,67; 4-4-2 B e 3-3-4 ~0,17. O forte é surpreendido muito mais quando joga 3-5-2, 4-5-1, 4-4-2 A ou 3-3-4 (o fraco faz 1,0–1,4 pts) do que com 4-3-3 (0,3–0,4). Fora de casa, sendo mais fraco, nenhuma formação passa dos 0,5 pts. Sliders dos outros clubes: o jogo não os dá (403); só os do dono, guardados antes de cada jogo.
- **Regra da formação mudada (OK do dono, D-045):** 4-3-3 A sempre; 5-3-2 só com o adversário mais forte por mais de 5 %; o 4-3-3 B deixa de ser a regra para jogos parecidos (`THEORY.md` §1, `theory/tactics.choose_formation(stronger_pct=5)`). 366 testes. **A seguir:** daqui a umas semanas, comparar no registo dos jogos o 4-3-3 A e o B fora de casa.
- **Nome do árbitro em vez do número:** o dono disse que não.
- **Avisos do pré-jogo, setas, força do clube, hovers (D-046, `THEORY.md` §21; perguntas feitas antes, a pedido do dono: "faz mts perguntas antes de avançares"):** `theory/lineup.py` (`bench_warnings`, `tactic_warnings`), `board/info.team_rating(formation=)` e `next_match` com `referee_id`, `game/clubinfo.py` (teamtactics, árbitros, `prep["why"]`, vendas só com slots livres), `game/specialists.check` com o texto, `gui/view.py` e `gui/window.py` (`tip_text`, `tip_html(title=)`, QToolTip novo), `i18n`. Campos da tática lidos no código do site (`enums.js`): `style` = desarme (0 Cuidadoso … 3 Extremo), `overallMatchTactics` = estilo de jogo (0 bola longa, 1 passe, 2 alas, 3 contra-ataque, 4 rematar), `marking` true = homem a homem, `attack`/`midfield`/`defense` = papéis das linhas. Leitura real: FC Van força 108 (antes sem círculo), setas fora (slots cheios), avisos: desarme Normal com árbitro normal, 4-3-3 B, Akanni antes de Ndicka, Lweendo antes de Cherki, Marmoush no banco; Betis: desarme Agressivo com árbitro muito brando, 3 suplentes melhores do que titulares. 375 testes. Correção §2: no 4-3-3 a marcação é à zona.
- **Atenção:** um teste rápido de tradução gravou `"language": "en"` em `~/.osmbot/config.json`; reposto para `"pt"` (o valor de antes, pela nota da 0.10.4).
- **Versão 0.11.9** (escolha do dono: uma versão no fim): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (9d, 9e); `dist` reconstruído; notas em `dist/release-notes-v0.11.9.md`.
- **Transferências de toda a gente** (pergunta do dono: "sou só eu que não faço transferências há demasiado tempo?"; histórico guardado pelos 3 PCs + `leagues/{L}/transfers`, que só dá as últimas 100): Arménia desde a J11 (341), Espanha desde a J5 (178). FC Van é o 2.º mais ativo (36 compras / 35 vendas; última há meio dia); Betis 23/23, última na J16 (2 dias), enquanto Barcelona e Real Madrid compram e vendem todas as jornadas (última há horas). Os humanos ativos compram quase tudo "de fora" a 130–180 % do valor; a ZSKA (1.º) investe mais do que recebe (‑434 M). Os clubes sem treinador quase não mexem. Pico de atividade na Arménia nas J14–J15.
- **O 1.º da Arménia (pergunta do dono):** 45 jogadores (17 DEF, 14 MED, 5 GR; 12 abaixo de 60 de rating). Desde a J11: 50 compras / 30 vendas; **todas as vendas a 250 % do valor** (= o máximo do jogo, como as do dono) a clubes de fora; compras de fora a ~150–165 % (os baratos de 1–2 M a ~195 %). 16 revendas com compra conhecida: **+251 M**, a maioria com 2–26 h de posse, quase todas nas J14–J16 (provável evento de transferências: J14 vendeu 9, J15 comprou 18 por 865 M). Força do jogo: 572 na J1 → 792 na J17. Hipóteses por confirmar: plantel grande como "stock" à espera de slots de venda; os baratos para os mínimos por posição.
- **Pendentes do dono:** casa/fora (~5 %) na regra; formação do adversário na janela depois da análise; pontos esperados vs reais; treino secreto e estágio na janela (ideia D); achievements; janela no Mac; modo poupança dos amigáveis; analisar os registos de treinos/amigáveis/médico/SALE; ideias 5 (fim de época com bilhete) e 6 (lista de venda na pré-época).

## 2026-10-13 — Erro do calendário de eventos e teste do ciclo com várias passagens (Windows)

- **Sintoma** (print do dono): "Calendário de eventos: erro ('list' object is not callable); tento amanhã" de passagem em passagem.
- **Causa:** em `run_active` (`game/loop.py`) a lista das horas de acordar reutilizava o nome `events`, que é a função que lê o fórum; da 2.ª passagem em diante `events()` chamava uma lista. O mesmo tipo de erro do `done` da 0.11.0. Correção: a lista passa a chamar-se `wakes`.
- **Teste novo** (pedido do dono, grupo 1): `test_every_task_runs_on_every_pass_not_only_the_first` corre 3 passagens com todas as tarefas falsas, em linhas e com a janela, e confirma que cada uma corre em todas as passagens, sem erros no registo. Falha com o código antigo (`events` 1 vez em 3). 358 testes.
- **Verificador de tipos (experiência, nada instalado no projeto):** o pyright apanha o erro antigo ("list[...] is not callable"); o mypy não. No `src/` inteiro o pyright dá 116 avisos, os que pareciam graves vistos um a um e todos falsos alarmes (dicionários sem tipo, valores já protegidos por `try` ou condição). Adotá-lo exigiria configurar só algumas regras. **Dono: fica de lado** (o teste das várias passagens cobre o caso; custo destes erros baixo). Só voltar a propor se aparecer um 3.º erro deste tipo que os testes não apanhem.
- **`.venv` recriada** (pedido do dono): a antiga tinha vindo de outro PC (utilizador `ccastro`) e apontava para um Python que aqui não existe. Nova com o Python 3.12 deste PC, `pip install -e ".[dev]"`, Firefox do Playwright (v1543) instalado; 358 testes. Neste PC `python`/`py` não estão no PATH (usar `.venv\Scripts\python.exe` ou ativar a venv). Cada PC tem a sua `.venv`; não se copia.
- **Plano de época (conversa, nada construído):** respostas do dono no `THEORY.md` §19 (domínio mundial, escolha do clube, estágios, taça, objetivo, banco 2/2/2/1, compras, torneio de campeões, 4 lugares, poupar coins com a época segura).
- **Ideias para a janela pedidas pelo dono** (por construir; só quando ele disser):
  - *Hover no lugar do campeonato* ("2.º Campeonato"): os 3 primeiros (se estivermos abaixo do 3.º: os 2 primeiros e nós) e o objetivo do início da época; quando formos matematicamente campeões, "Campeões" em vez de "1.º lugar". **Por descobrir:** onde o jogo dá o objetivo da época.
  - *Valor do plantel em círculo* (como no jogo): no cartão, à frente do nome do clube e antes do ícone do dinheiro; na faixa do adversário, à frente do "(1.º)". Símbolo do alarme um pouco maior. Hover no nome do adversário: valor do plantel e média por jogador.
  - *Treino secreto e estágio* por baixo dos 4 treinos: a cinzento por omissão, com o alarme num jogo perigoso (como o símbolo de hoje).
  - *Posição sem suplente* (ideia 4, forma aceite pelo dono depois de ver prints da fadiga): na linha amarela dos cansados (coluna PRÉ-JOGO, `⚠ Cansados: …`), quando o cansado não tem suplente na posição, acrescentar `(sem suplente DEF)`; ao passar o rato, 2–3 opções do SALE dessa posição que caibam no dinheiro do clube. Só sugestão (comprar é escrita nova).
  - *Pormenor:* na lista "Avisos e erros" as mensagens começam por "!", mas a coluna Tipo já diz "Aviso": tirar o "!" dessa lista.
  - Hoje a fadiga aparece em 2 sítios (visto em prints com dados de teste): a linha amarela no cartão (titulares abaixo de 80 %, enquanto durar) e uma linha na lista de avisos (uma vez, quando desce dos 80 %). Ideias 5 (fim da época com bilhete) e 6 (lista de venda na pré-época) ficam para depois (6: estudar primeiro os registos das transferências). Ideia 8 (mapa do domínio): pouco a automatizar. Ideia 1 (contas das conquistas): não é precisa, já se vê.
- **Por ver:** o calendário só volta a ser lido amanhã (a tentativa de hoje ficou registada).
- **Construído (pedido do dono: C, E e F), por lançar:**
  - *C:* círculo com a **força da equipa** (correção do dono: é o rating, como o "109" do jogo, não o valor em dinheiro). Fórmula conferida em 3 clubes (`DISCOVERY.md`): melhores por posição na formação atual do clube (`board/info.team_rating`); a 1.ª versão (11 melhores sem olhar à posição) dava 74 em vez de 73 num adversário em 3-5-2 e foi corrigida. O adversário **só depois da análise** (escolha do dono, opção 2: antes disso o jogo não mostra o onze dos outros), lido 1 vez por adversário e jornada, guardado 10 min. Cores [S]: o nosso azul; o do adversário verde/amarelo/vermelho comparado com o nosso (diferença de 2). `gui/window.ValueBadge`, `gui/view.rating_badge`, `squad_tip`. No cartão entre o nome e o dinheiro, e na faixa do jogo logo a seguir ao "(N.º)" (`board/info.next_match` dá `opponent_id`). Hover no círculo e no nome do adversário: força, valor do plantel, jogadores e média por jogador.
  - *B (pedido do dono, construído a seguir):* hover no "N.º Campeonato" com os 3 primeiros e os pontos (abaixo do 3.º: os 2 primeiros e nós, marcados com ▸) e o objetivo da época; "Campeões" no cabeçalho com o título matematicamente garantido [S]. Pontos de `GET leagues/{L}/standings` (descoberto hoje, guardado 10 min), objetivo do campo `goal` (confirmado pelo dono: 4 e 7). `board/info.league_summary`, `gui/view.table_view`. Regras no `THEORY.md` §19 ("Na janela"). Alarme do confronto direto maior (⚠ a amarelo, 15 pt, à parte do texto). Coluna do clube de 345 para 380 px, para o nome caber com o círculo.
  - *E:* `theory/fitness.uncovered` (posição de um cansado sem suplente), `transfers/engine.sale_options` (SALE dessa posição que cabem no dinheiro, melhor rating primeiro, até 3); `dashboard` junta `club["cover"]` (lista de transferências já lida, sem pedidos novos); `gui/view.tired_view` acrescenta `(sem suplente DEF)` e o hover com as opções. Regras no `THEORY.md` §16 (suposições [S]: o que conta como suplente; dinheiro = conta + poupança).
  - *F:* já estava feito: o ciclo tira o "!" antes da lista de avisos (`loop._log`); nos prints de há pouco aparecia porque os dados de teste o traziam.
  - Traduções para inglês (`i18n`: "no cover", "Strength …", "Goal: 4th or better", "Champions", "SALE … you can afford"). 365 testes. Prints com a janela real fora do ecrã: dados reais do jogo (uma leitura, só GETs) e um caso de teste (cansado sem suplente, confronto direto).
- **Versão 0.11.8** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (9, 9c), D-043 (com o pyright posto de lado), `GLOSSARY` (força, objetivo, domínio mundial, torneio de campeões); `dist` reconstruído; notas em `dist/release-notes-v0.11.8.md`. `RISKS_AND_COMPLIANCE` sem mudanças (só leituras novas, nenhuma escrita).
- **DESKTOP-KAM70RR, depois do pull:** 365 testes; `dist` 0.11.8 reconstruído (portátil 552 MB, zip 206 MB, instalador 148 MB); notas em `dist/release-notes-v0.11.8.md` (o `dist` não vai no git).
- **PT-LA-02-0095-N:** `dist` 0.11.8 reconstruído (portátil 552 MB, zip 206 MB, instalador 148 MB); Inno Setup 6.7.3 instalado neste PC por utilizador, com `winget`, a pedido do dono.
- **Modo poupança dos amigáveis: em aberto** por decisão do dono, para discutir no futuro (de preferência com números de uma liga criada por ele). Classificação e valor dos planteis das 2 ligas lidos (só GETs) e registados no `THEORY.md` §19; `ranking` = posição na liga confirmado (`DISCOVERY.md`).
- **Próximo passo (ordem sugerida, à espera do dono):** 1) [modo poupança: em aberto]; 2–3) [feitos: B, C, E, F; o dono vê os prints]; 4) descobrir, só com leituras, o treino secreto e o estágio (ideia D), e os achievements; 5) janela no Mac. A versão 0.11.8 (correção do calendário) fica para quando o dono quiser.

## 2026-10-12 — Pendentes por ordem: 1) calendário para agir

- **Versão 0.11.7** (pedido do dono): ajuste do inventário, D-040, D-041, D-042; `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF` (8b, 9a, 9b), `RISKS_AND_COMPLIANCE`, regra 5 do `CLAUDE.md`; `dist` reconstruído; notas em `dist/release-notes-v0.11.7.md`. **A seguir:** ponto 4 (janela no Mac) e 5 (plano de época, só conversa), com mais calma (o dono: "tás a ir mt rápido").

- **Lista acordada com o dono** (por ordem): 1) usar o calendário para agir; 2) registo dos jogos; 3) especialistas; 4) janela no Mac; 5) plano de época (só discussão).
- **3) Feito (D-042):** especialistas pela regra nas últimas 4 h antes de cada jogo (`theory/specialists.wanted_slots`/`wrong_roles`, `game/specialists.py`, ligado em `prematch.prepare_club`); checklist a amarelo quando fora da regra (`clubinfo`, `view`). 1.ª gravação com OK do dono: livres de um clube corrigidos (200). Respostas do dono: vários papéis por jogador; lesionado sai do onze. 356 testes.
- **2) Histórico:** a época até agora gravada de verdade (só leituras): 280 linhas em `logs/DESKTOP-KAM70RR/jogos/` (167 + 101 jogos com resultado e árbitro, `historico`; mais a última jornada completa, 12 jogos com notas).
- **2) Feito (D-041):** registo de todos os jogos de liga e taça das ligas do dono, uma vez por jornada (`game/matchlog.py`: `note_prematch` nas últimas 4 h e ao levantar o analista guarda a tática e o relatório; `log_rounds` no ciclo, depois das transferências). Táticas dos outros clubes: 403 no jogo. Ensaio real com o registo desviado: 12 jogos (10 de liga numa liga, 2 de taça na outra), ~90 KB por jornada; as 2 linhas do dono no registo. 351 testes. **Por ver:** se `spyresults` responde antes do jogo (próxima jornada).
- **1) Feito (D-040):** 8 amigáveis durante um Intense Friendlies, com o evento no registo `amigaveis/` (`prematch/policy.friendly_deadlines`, `friendly_event`; `game/prematch.prepare_club` lê o calendário; linha do tempo com as mesmas horas). Transfer Madness: nada, por decisão do dono. Os eventos de tempos curtos e de "mais progressão ao recolher" já são aproveitados (o bot lê os tempos do jogo e recolhe logo). Testes isolados do calendário verdadeiro (`conftest.py`). 348 testes. Primeiro caso real: Intense Friendlies a 24–25/10.

## 2026-10-12 — Ajuste do inventário na janela (depois da 0.11.6)

- **Pedido do dono:** ícone à direita, junto ao estado do bot, um pouco maior (28 px), sem número; ao passar o rato só os itens que expiram, com o tempo em dias e horas ("1 dia e 13 horas"). `gui/view.time_left`, `inventory_view`, `gui/window.InventoryBadge`; `THEORY.md` §20. 347 testes; print visto.
- **Por lançar:** na próxima versão.

## 2026-10-12 — Inventário: usar o que vai expirar (Windows, depois da 0.11.5)

- **Problema do dono:** itens que expiram sem serem usados. Lido no jogo: treinadores universais (24/48 h) e sacos expiram 7 dias depois de entrarem; trocas de posição e progressão não expiram.
- **Pedidos descobertos sem o dono:** código público da web (`inventory.js`, `training.js`, `loggedInLayout.js`) e a página do inventário aberta com a sessão do bot só para ler (POSTs bloqueados). `DISCOVERY.md` §3.
- **1.º uso real** (autorização direta do dono; o classificador de permissões bloqueou a 1.ª tentativa): treinador universal de 24 h (expirava às 00:06) ativado numa equipa (200, disponível até 13/10 21:36) e um defesa titular posto no treinador 5 (200, sessão de 6 h até 03:36). A outra equipa não tinha titular possível.
- **Regras do dono** em `THEORY.md` §20 e D-039: usar 4 h antes de expirar, avisar 24 h antes; treinador universal para a equipa com mais a ganhar (empate → pior plantel), treina o titular de qualquer posição pela rotação; sacos abertos, boss coins para a carteira; trocas e progressão manuais.
- **Código:** `inventory/policy.py` (puro), `game/inventory.py` (`run_inventory`, ligado no `loop.py` depois do médico; só lê os plantéis quando há treinador ativo ou item a usar), `dashboard` (sessão do treinador 5 fora da linha dos treinos, `club["universal"]`, `snapshot["inventory"]`, acordar para a recolher), `ads.pick_session` (vídeos de treino nunca na sessão do treinador 5), linha do tempo, `gui/view` (`universal_ring`, `inventory_view`), `gui/window` (`InventoryBadge` com o ícone do jogo `icon_inventory.png`, ponto amarelo a menos de 24 h; círculo do treinador universal ao lado do médico e do advogado, com a imagem do jogo `cons_universaltrainer.png` recortada em círculo), traduções. Simulação real (só leitura): nada a fazer agora; acorda a 14/10 09:14 para o treinador de 48 h. 346 testes.
- **Atenção:** a 0.11.5 que está a correr não conhece o treinador 5: pode tentar pôr um vídeo de treino na sessão dele e falhar (só um erro no registo, volta a tentar). Fica resolvido com a próxima versão.
- **Por ver em real:** abrir um saco (19/10, ou antes se o dono quiser); o jogo deixar dois treinadores universais na mesma equipa (o bot assume que não).
- **Versão 0.11.6** (pedido do dono depois dos prints): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF`, `RISKS_AND_COMPLIANCE`, D-033 (ícones novos), D-039; `dist` reconstruído; notas em `dist/release-notes-v0.11.6.md`.
- **Próximo passo:** o dono faz commit, release e atualiza o bot instalado (a 0.11.5 a correr não conhece o treinador 5). A 14/10 ~09:14 ver o treinador de 48 h ativado sozinho; a 19/10 o 1.º saco.

## 2026-10-12 — Calendário na janela e informação das diárias ao passar o rato (Windows)

- **Revisão dos logs de hoje** (pedido do dono): a paragem das 03:06 no DESKTOP-KAM70RR foi o bug da 0.11.0 (já corrigido); ganhos 4–5× acima da previsão em alguns treinos (um GR +63 com previsão 13, um ATA +67 com previsão 14) por explicar até haver `treinos/`; as vendas a 100% do máximo demoram 22–28 h. O PC da empresa (DESKTOP-8OFGOB3) deixou de ser usado; o novo de lá ainda não passou logs.
- **Release 0.11.4:** o `dist` deste PC tinha a 0.11.0; reconstruído com a 0.11.4 e notas em `dist/release-notes-v0.11.4.md`. Falta ao dono: `gh release create v0.11.4 …` (tag e release; a 0.11.1 também não tem).
- **Calendário na barra de cima** (dono, 2.ª versão depois de ver prints): à frente das diárias, "Próximo evento: Super Staff · 14/10" (ou "Evento agora: … · até …"); ao passar o rato abre o mês inteiro como calendário (7 colunas Seg–Dom, uma linha por semana), o nome do evento no quadrado do dia a laranja (esbatido depois de passar), hoje com borda branca, sem legenda; os efeitos ao passar o rato no dia, em português por regras (`events/calendar.effect_text`) ou no original em inglês. `gui/view.calendar_view`, `game/events.calendar_months`, `snapshot["calendar"]`, `gui/window` (`MonthGrid`, `EventPopup`, `EventLabel`).
- **Hover nas diárias** (dono): início de sessão = só o prémio de hoje, com ícone (boss coins, fundos…); depois de reclamado o jogo já não o mostra, por isso o bot guarda-o ao reclamar (`~/.osmbot/inicio_sessao.json`) e, sem isso, procura um item de início de sessão entrado hoje no inventário (`policy.login_today`). Missões = as 3 de hoje com o certo verde ou o círculo amarelo e o progresso. Prémio do dia = o de hoje e o de amanhã. `rewards/texts.py` (missões em português por regras, prémios por tipo), `policy.prize_index`/`mission_details`, `gui/view.daily_tips`, `gui/window.tip_html`. Prints feitos com a janela real fora do ecrã (uma leitura, só GETs). **Incidente:** um teste escreveu no `~/.osmbot/inicio_sessao.json` verdadeiro; apagado e isolado no `conftest.py`. 336 testes.
- **Versão 0.11.5** (pedido do dono, depois de aprovar os prints): `pyproject`, `__init__`, `CHANGELOG`, `README`, `PROJECT_BRIEF`; `dist` reconstruído; notas em `dist/release-notes-v0.11.5.md`.
- **Próximo passo:** o dono faz commit e o release; vê o calendário e os hovers ao vivo. Por ver: amanhã (dia 2 da semana) o prémio do dia aparece e é reclamado.

## 2026-10-12 — Bot parado de noite (0.11.0, Windows)

- **Sintoma** (screenshot do dono, DESKTOP-KAM70RR): "Parou: erro (unsupported operand type(s) for +=: 'dict' and 'int')"; o registo acaba às 03:06:01, logo a seguir ao 1.º treino posto com a 0.11.0 (Marmoush).
- **Causa:** em `run_train` a contagem da rotação (`round_sessions`) reutilizou o nome `done`, que já era o contador de treinos postos; o `done += 1` depois do 1.º POST com sucesso rebentava. Os testes não corriam `run_train` em modo real.
- **Correção:** dicionário renomeado para `rotation` (`game/trainings.py`); teste novo com cliente falso (2 treinos postos e gravados), que falha com o código antigo. A janela passa a escrever a paragem no registo, com ficheiro:linha (antes só aparecia na janela; a lista "Avisos e erros" ficava vazia). 310 testes.
- **Próximo passo:** o dono fez commit da correção como 0.11.1 (a versão no código ficou 0.11.0; acertada na 0.11.2). No DESKTOP-KAM70RR: pull e `dist` reconstruído com o bot fechado.
- **Rotação dos treinos entre PCs:** no FC Van repetiu Wharton, Dalot, D. Henderson e Marmoush ("1.º treino na jornada"), porque a conta é por PC e os treinos recolhidos desaparecem do jogo. Verificado que o jogo não dá histórico (`DISCOVERY.md` §3). Proposta ao dono, à espera: apontar também os treinos que o bot **vê** (por recolher), não só os que põe.
- **Amigáveis e analista (pedido do dono):** amigáveis distribuídos pelo dia (16/12/8/4 h antes do jogo, [S]) e analista levantado logo que acaba, a qualquer hora; enviar o analista continua nas 4 h (`THEORY.md` §6). `prematch/policy.py` (`friendlies_due`, `next_friendly_at`), `game/prematch.py` (`prepare_club`), linha do tempo. 314 testes; simulação real (só leitura) correta. Lançado na **0.11.2** (D-036; versão, `CHANGELOG`, `README`, `PROJECT_BRIEF` atualizados; `dist` reconstruído, notas em `dist/release-notes-v0.11.2.md`).
- **Plano de época (dono):** `THEORY.md` §19 (criar a liga ~350 coins, escolher o clube de maior valor, até 3 estágios).
- **Calendário de eventos (D-038, 0.11.4):** o dono não quer copiar o calendário à mão; escolheu ler o fórum com o Firefox do bot (contorna o Anubis, registado em `RISKS_AND_COMPLIANCE.md`) e ver o evento em curso nas definições do jogo. `events/calendar.py` (puro: `parse_schedule`, `upcoming`, `active_changes`, `months_needed`), `game/events.py` (`read_forum_post` com repetição por causa da corrida com o Anubis, `refresh` 1×/dia só quando falta um mês, `check_league` de hora a hora com `eventnotifications`), ligado no `loop.py` (depois das transferências), no `dashboard.collect` (`events` e `club["event"]`) e na linha do tempo; traduções. Ensaio real: 14 s, os 10 eventos de outubro lidos e guardados. Também: vender é probabilidade, não limite (dono; `THEORY.md` §7.5). 330 testes. **Próximo:** a 14/10 (Super Staff) ver se `eventnotifications` responde e se as definições mudam como o fórum diz; depois usar o calendário para agir.
- **Versão 0.11.3 (D-037):** desempate da rotação pela previsão do jogo (`training/policy.py`; `THEORY.md` §5); `game/trainings.py` aponta as sessões vistas (`note_seen`, ignora jornadas passadas) e grava registos `treinos/`; `logs.record` (JSON por mês, segredos limpos campo a campo); registos `amigaveis/` (`prematch._progress`), `medico/` (`medical._state`), `transferencias/sale/` (`transfers/engine.sale_rows`/`sale_changes`, ligado em `market.watch`, linha "SALE novos" traduzida). Leitura real: a regra nova muda 1 de 8 escolhas (a 1.ª conta, que dizia 3, não tirava os listados para venda). Sincronização entre PCs posta de lado pelo dono ("só logs"). 321 testes; `dist` reconstruído. **Próximo:** em 1–2 semanas, analisar `logs/*/treinos` (desconto por repetição, previsão vs ganho), `amigaveis` (quanto rende cada um), `medico`, `sale` (horas a que aparecem). Depois: registo dos jogos (resultado, ratings, árbitro) e o aviso "SALE" comparado com os titulares fracos.

## 2026-10-12 — Boss coins por dia, revisão do que nos atrasa (0.11.0, Mac)

- **Boss coins por dia** (pergunta do dono, contado nos logs): 05/10 7 · 06/10 24 · 07/10 121 · 08/10 178 · 09/10 198 · 10/10 195 · 11/10 105 (meio dia); 828 no total, ~190/dia com o bot o dia inteiro. Contas de sustentabilidade feitas com o dono (liga ~350, 3 estágios = 80, 4 amigáveis/dia ≈ 28 coins/dia por equipa): dá para 4 equipas.
- **Vídeos do telemóvel (médico, advogado, estádio):** opções explicadas (proxy para observar a app; Android ligado ao PC por USB; emulador desaconselhado; o Mac é Intel, não corre apps de iPhone). Nada construído; o dono decide.
- **Revisão do bot → D-035:** dados dos logs (progresso por recolha) e `trainingforecasts` lidos (só leitura): o rating pesa mais; repetir o jogador na jornada rende ~2–3× menos (não 5–8×, como se disse primeiro: os +100–150 que apareciam eram bónus ao acaso). A previsão do jogo não mostra a quebra por repetição.
- **Código:** `Player.lineup`/`starter`; `training/policy.py` (rotação, `round_sessions`); `game/trainings.py` (jornada da liga, `~/.osmbot/treinos.json`, previsão e "N.º treino na jornada" no log); `savings/policy.py` + `game/savings.py` (depósito, 2 PUTs no máximo se o dinheiro estiver repartido), ligado no início de cada passagem do `loop.py` e na linha do tempo/tradução; `gui/window.py` (`READ_HIDDEN_EVERY` = 15 min). 309 testes (PySide6 instalado no `.venv` do Mac).
- **Ensaio real (só leitura):** com os treinadores livres, a regra nova trocaria o Haaland (no banco) pelo Díaz no Real Betis, e no FC Van o Marmoush e o Dalot (já treinados nesta jornada) pelo Zirkzee e o N'Dicka.
- **Versão 0.11.0** (pedido do dono). **Por ver em real:** o 1.º depósito (linha "Poupança: … depositou …") e se um PUT com dinheiro nos dois lados deposita ou levanta (o código trata os dois casos). **Próximo passo:** o dono faz commit/push no Mac, pull no Windows, reconstrói o `dist` e corre a 0.11.0; com 3–4 dias de linhas "a treinar … previsão" e "recolhido (+N)", medir se a rotação compensa.
- **Windows, depois do pull:** 309 testes; `dist` 0.11.0 reconstruído (portátil 552 MB, zip 206 MB, instalador 148 MB); notas em `dist/release-notes-v0.11.0.md`.

## 2026-10-11 — Revisão dos logs para o 1.0

- **Versão 0.10.4** (pedido do dono): 4 amigáveis e registo do motor (D-034); `pyproject`, `__init__`, `CHANGELOG`, `README`; notas em `dist/release-notes-v0.10.4.md`; `dist` reconstruído. 298 testes.
- **Eventos especiais (pergunta do dono):** 12 GETs prováveis (`events`, `campaigns`, `promotions`, …) dão 404 e o jogo não mostra o calendário; só o fórum o publica (ver `DISCOVERY.md` §6b). O jogo só deixa ver um evento ativo pelos efeitos (p. ex. `gamesettings`). Proposto um ficheiro de calendário mensal; à espera do dono.
- **Médico confirmado em real** (pergunta do dono): no DESKTOP-KAM70RR o bot pôs no médico 3 vezes (09/10 21:08, 10/10 18:43, 11/10 02:43) e levantou 2 vezes (10/10 05:09, 11/10 02:43). Os 404 são todos de 09/10, antes da correção para `v1`; o DESKTOP-8OFGOB3 não tem logs depois de 09/10.
- Também vistos nos logs: analista levantado ×2 (11/10), amigável ×1 (11/10), início de sessão e missões. Por ver: advogado (só 400 com suspenso de 1 jogo). **Envio do analista confirmado** (pedido do dono): `_send_analyst` corrido à mão, fora da janela das 4 h, para o FC Van → 200, e a releitura já não pede análise; o bot levanta-o quando abrir a janela das 4 h antes do jogo. "Deteção de vendas" sai da lista (dono): é só leitura das vendas que o dono faz à mão, o bot não vende. Renovação da sessão: sem erros nos logs (corridas até 9 h seguidas, token renovado a cada ~20 min); expiração por 7+ dias parado nunca aconteceu. `PROJECT_BRIEF.md` atualizado.
- **Documentação revista** (pedido do dono): `README.md` (estado 0.10.3, janela D-030, menus Ver/Idioma/Ajuda), `PROJECT_BRIEF.md` (linhas 8, 12a, 12b e 13 com o que já foi visto em real), D-030 com as revisões de 10/10.
- **Transferências (pergunta do dono):** a gravação de hoje já tem vendas acima de 100 M€ de máximo: 3 do dono a 75 % vendidas, outra a 100 % de 104 M€; e as vendas acontecem em lotes (`DISCOVERY.md` §3). 10 listagens do dono acima de ~70 M€ ainda à venda; a partir da 0.10.3 o registo dá a hora de cada venda.
- **Transferências, 21:25 (pergunta do dono):** leitura ao vivo: numa liga vende-se ao máximo até 167 M€ (6 vendas acima de 100 M€ hoje), lotes a cada ~2 h, cada lote leva só uma parte; as listagens a 75 % do dono não venderam mais depressa que as a 100 % (`DISCOVERY.md` §3).
- **Pesquisa no fórum oficial** (pedido do dono: mais dicas): `DISCOVERY.md` §6c. Staff: venda = sorte com probabilidade por preço e taxa de subida, o preço absoluto pesa mais; motor 8×/dia a intervalos aleatórios; 100+ quase não vende fora de eventos; pior perto do fim da liga. Treino: idade, rating, repetições na jornada, campo de treino +50 % no nível 3.
- **Registo do motor de transferências (D-034, pedido do dono):** `transfers/engine.py` (puro) + `game/market.py`, ligado em `clubinfo.club_extra`; registos em `logs/<PC>/transferencias/motor/<liga>.jsonl` e uma linha no registo do bot (traduzida). Leitura real do quadro sem erros (2 ligas, estado inicial guardado). 297 testes. Por lançar (lançado na 0.10.4). **Próximo:** com 1–2 dias de registos, confirmar se as descidas de preço do jogo coincidem com as vendas.
- **4 amigáveis por jogo (dono):** regra em `THEORY.md` §6 (pressupostos [S]: contam os do dono, janela das 4 h, faz os que as coins derem), nota em D-025. `prematch/policy.py` (`friendlies_played`/`friendlies_missing`), `game/prematch.py` (`_play_friendlies`: até 4, clubes ao acaso, pausa de alguns segundos entre eles, até 3 recusas por passagem), `clubinfo` ("Amigáveis (N)", verde a partir do 1.º, correção do dono; fixtures relidos depois de cada amigável), linha do tempo e tradução. 298 testes; leitura real mostra "Amigáveis (0)" nos dois clubes. Lançado na 0.10.4. Nota: o teste da tradução gravou `"language": "pt"` em `~/.osmbot/config.json`.
- **Versão 0.10.3** (pedido do dono): hora das vendas no registo; `pyproject`, `__init__`, `CHANGELOG`; notas em `dist/release-notes-v0.10.3.md`; `dist` reconstruído. 293 testes.

## 2026-10-10 — Correções à janela

- **Faixa do próximo jogo (pedido do dono):** deixa de ser verde em casa / vermelha fora; passa a ter a cor do clube, tirada do logótipo (a mesma da bolinha na linha do tempo), escurecida para o texto branco se ler. "CASA"/"FORA" fica só como etiqueta. Até o logótipo chegar, usa o roxo da janela. `gui/window.py` (`MatchStripe.set_colour`), D-030 atualizada. 287 testes.
- **Tipo de letra:** maquetes com 12 letras (janela real, dados de teste, fora do repo); o dono escolheu a **Sora** (OFL). Vai dentro do programa: `gui/assets/Sora.ttf` + `Sora-OFL.txt`; `load_font()` em `run_gui`, Segoe UI se falhar.
- **Cartão com as cores do clube:** 4 maquetes (A brilho de cima · B duas cores · C discreto · D forte); o dono escolheu a **C**: risca de 3 px no topo na cor do clube, brilho leve até 1/4 do cartão e contorno na cor (`ClubCard.set_colour`). A cor é lida só no interior do escudo (todos os logótipos do OSM têm a mesma moldura dourada, que ganhava) e é a mesma no cartão, na faixa do jogo e na bolinha da linha do tempo. Linha da venda em letra 8, para caber numa linha com a Sora. Visto numa captura da janela real com dados de teste.
- **Versão 0.9.7** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`; `dist` reconstruído (portátil, zip, instalador); notas em `dist/release-notes-v0.9.7.md`.
- **2.ª ronda de correções (dono):**
  - barra das diárias a toda a largura (boss coins ao nível do 1.º clube; coluna da direita sem margem);
  - valor do plantel: lugar a cores (1.º–2.º verde, 3 últimos vermelho, resto amarelo; `squad_view`) + total a branco; dica com jogadores e média. `squad_value` passa a dar também jogadores e n.º de equipas (leituras antigas com 3 valores aceites, nunca a vermelho);
  - patrocinadores: só "X/ronda"; com vaga vazia, ⚠ e dica "N vaga(s) vazia(s) nos patrocinadores" (`sponsor_view`);
  - estádio: o círculo não enchia porque a duração ficava "desconhecida" quando a obra era vista pela 1.ª vez com menos de 4 h (janela aberta a meio, vídeo −2h). O temporizador do jogo não tem início (`probe` a `timers`: só `currentTimestamp`/`finishedTimestamp`). Agora: 3h45–4h = evento (4 h), resto até 18 h = normal (18 h). Dica "Faltam X".
  - 289 testes; captura da janela real conferida.
- **Versão 0.10.0** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`; `dist` reconstruído; notas em `dist/release-notes-v0.10.0.md`.
- **3.ª ronda de correções (dono), por lançar (sem versão nem commit, pedido do dono):**
  - mensagens de hover no estilo da janela (`QToolTip` em `STYLE`) e quase instantâneas (`QuickTips`: 60 ms);
  - valor do plantel e patrocinadores a negrito; mais espaço entre "1.º" e o total; patrocinadores completos a branco (já não a verde);
  - dinheiro sai das linhas e vai para a linha do nome, encostado à direita, com o ícone `clubfunds.png`; sem "Dinheiro";
  - venda: seta verde animada (`SaleArrow`) ao lado do dinheiro enquanto a venda está no cartão; quem e quanto no hover (resposta do dono: "Só a seta, texto no hover");
  - vaga livre na lista de transferências: por baixo dos patrocinadores, a amarelo, com ⚠;
  - boss coins: +X centrado na altura do número; `bosscoin.png` grande à direita (D-033);
  - todos os temporizadores (anéis de treinos, médico/advogado, estádio a subir, bolinhas do futuro na linha do tempo) na cor do clube meio apagada (`soft`: média com o cinzento `MUTED`); verde só quando acaba (resposta do dono: "Anéis e linha do tempo");
  - estádio: só o nome por baixo; ao meio o nível; no hover "MAX" a verde (cheio) ou o tempo que falta (a subir); parado cinzento, sem hover; células de largura fixa (espaçamento igual);
  - faixa do jogo: "em 18h11" na mesma linha que "vs Clube";
  - 289 testes; captura da janela real conferida (o hover não aparece nas capturas).
- **4.ª ronda (dono), também por lançar:**
  - dinheiro maior (15 pt) e ícone maior (28 px);
  - treinos: o cone (`training.png`) dentro do anel; o tempo só no hover (ou "pronto"); colunas de largura fixa (`TRAINING_WIDTH`) e alinhadas à esquerda, com médico e advogado por baixo nas mesmas colunas;
  - médico e advogado (`CareCell`): a figura recortada em círculo (o maior possível, resposta do dono) dentro do anel; desbotada sem ninguém ou com suspensão de 1 jogo; por baixo o jogador + cruz vermelha / cartão vermelho (`Mark`) + só o número de jogos (resposta do dono); sem "Médico"/"Advogado" por baixo (vai no hover, com o resto); no hover do anel, o tempo que falta / "pronto" / "à espera" / "não dá". Saem os emojis 🩺 e ⚖️;
  - pré-jogo: uma linha por passo com ícone desenhado do mesmo tamanho (`StepIcon`: verde com visto, azul com relógio, amarelo com "!", anel cinzento) e mais espaço entre linhas; a vista passa a dar `(tipo, nome, extra)`;
  - 289 testes; capturas conferidas.
- **5.ª ronda (dono), por lançar:**
  - pré-jogo em letra 10 (com 8 passos, "Análise por levantar" ficava cortado); `StepList` serve o pré-jogo e as diárias;
  - diárias com os mesmos ícones (anel amarelo = missões a meio) e maiúscula inicial ("Início de sessão (dia 12)", "Missões 2/3", "Prémio do dia"); sem "✓" no texto;
  - linha do tempo com ícones no lugar das bolinhas (`icon_of`, `PAST_ICONS`): moedas (vídeos da loja), cone (treinos e vídeo de treino), dinheiro (vídeos de dinheiro, patrocinador), missões (diárias, reward cumulativo, novo dia), estádio, cruz (médico), cartão (advogado); amigável/análise/jogo mantêm a bolinha; eventos de um clube com um aro leve na cor dele;
  - 290 testes; captura conferida.
- **Versão 0.10.1** (pedido do dono: commit e release): rondas 3–5 juntas; `pyproject`, `__init__`, `CHANGELOG`; notas em `dist/release-notes-v0.10.1.md`.
- **Evento "Loucura das transferências"** (fim de semana, visto pelo dono): `slots` (só leitura) dá limite **6** nos dois clubes, 1 listado em cada. Hipótese do DISCOVERY passa a [V]. A janela lê o limite com cache de 10 min, por isso o aviso "⚠ vagas vazias" já conta 5. O bot continua sem vender (escrita nova, precisa de OK, D-014).
- **Valor do plantel não atualizava** (dono: "carrego em Atualizar mas não muda" no FC Van): os valores da liga ficavam em cache 1 h e o Atualizar não a limpava. Agora o clube próprio conta sempre com o plantel acabado de ler, e Ver → Atualizar chama `clubinfo.forget()` (relê valores, jogos e limite de vendas). Leitura automática de 3 min mantém a cache. 291 testes.
- **Cartões acabavam antes da linha do tempo** (dono: "cortado abruptamente"): a coluna dos clubes tinha um espaço vazio no fim. Agora os cartões dividem a altura que sobra e o último acaba ao nível da coluna da direita; com 3–4 clubes que não cabem, continua a deslizar. Captura conferida.
- **Cone do treino tapava o anel** (dono: "por dentro, não por cima"): a imagem cabia num quadrado e os cantos da base saíam do círculo. Agora `reach()` mede até onde vai a parte desenhada da imagem e o `Ring` escala-a para caber no círculo de dentro (com recorte redondo); médico e advogado (já redondos) ficam do mesmo tamanho. Captura conferida.
- **Linha do tempo:** ícones maiores (26 px; cruz e cartão ×1,8), sem aro à volta. O aro na cor do clube saiu (dono não gostou); das 4 maquetes (mini-emblema, risca lateral, nome na cor, fundo suave) escolheu **A**: o emblema do clube, pequeno (14 px), antes do nome na linha de baixo dos eventos futuros de um clube. `Timeline.set(..., logos)`. Captura conferida.
- **Cartões cortados à direita em janela estreita** (dono: o cartão devia ter o canto direito arredondado): o cartão precisa de ~950 px e a lista não tem barra horizontal, por isso abaixo de ~1340 px de janela o lado direito (e parte do pré-jogo) desaparecia. Escolha do dono (1 de 2): largura mínima. `_fit_width` (depois de os cartões estarem dispostos) dá à lista a largura do cartão mais largo + barra de deslizar e à janela essa largura + margens + coluna da direita (`GAP`, `SIDE`); uma janela mais estreita cresce. Teste a 1180 px: passa a 1340, cartões inteiros.
- **Hora das vendas no registo** (pedido do dono, para o estudo dos 100 M€): a lista de transferências traz `timeStampForSale` (hora em que foi posto à venda; `DISCOVERY.md` §3). `track_sales` guarda `since`/`value` por jogador listado e `sold` (a leitura que o viu sair) por venda, em `~/.osmbot/sales.json`; o registo ganha `Lista de transferências: Nome (Clube) à venda por X (N% do máximo ≈ Y)` e `Venda: Nome (Clube) vendido por X (…); à venda desde dd/mm hh:mm, vendido até dd/mm hh:mm, demorou XhYY` (com tradução para inglês). Máximo estimado como 2,5 × valor (`THEORY.md` §7.5). Precisão da hora de venda: o intervalo entre leituras (3 min).
- **Estudo dos 100 M€** (pedido do dono): só 204 transferências guardadas (2 ligas, jornadas 5–15), nenhuma venda acima de 68 M€ de máximo; resultado em `DISCOVERY.md` §3. As 2 listagens do dono acima de 100 M€ (em `~/.osmbot/sales.json`) serão o 1.º dado quando venderem.
- **0.10.2** (pedido do dono): versão em `pyproject.toml`/`__init__.py`, `CHANGELOG.md`, notas em `dist/release-notes-v0.10.2.md`, dist reconstruído.
- **Ícones na linha do tempo** (pedido do dono): "à espera" em AGORA mostra o temporizador em vez do ponto; o jogo de cada equipa mostra uma bola de futebol (desenhada por nós). Fontes em `img/timer.svg` e `img/ball.svg`, convertidas para `gui/assets/*.png` a 128 px: o dist corta o suporte de SVG do Qt (a 1.ª versão com `QtSvg` rebentou no portátil). Sem PySide6 e sem consola (OSMbot.exe), o erro mostra-se direto em vez de tentar abrir o menu. Teste: o jogo tem o ícone `ball`.
- **Pesquisa sobre amigáveis** (pedido do dono): fórum oficial (no Chrome, só leitura, sem sessão), guias, lojas; Reddit sem nada. Resultado em `DISCOVERY.md` §6b: progressão desce a cada amigável na mesma jornada e repõe-se com o jogo (staff), o mesmo nos treinos do mesmo jogador; acima de 100 progride-se pouco; só o evento Trainingcamp Terror faz subir por amigável; amigáveis não contam para missões; calendário oficial de eventos de outubro (Intense Friendlies 24–25, Extreme Training 31). Nada mudado em `THEORY.md` (é do dono).

## 2026-10-09 (cont. 3) — Casa: médico corrigido, transferências guardadas, janela nova

- **Médico (pergunta do dono):** o bot nunca levantou o médico; 3 tentativas com 404 (09:13, 17:26, 19:31). Com `inspect-writes`, o dono levantou à mão: o pedido é `PUT api/v1/…/doctortreatments/{id}/claim` (o bot usava `v1.1`). Corrigido em `game/medical.py`; `DISCOVERY.md` §3 passa a *Verificado*. Advogado: mesma base, ainda por confirmar.
- **Porque o lesionado não voltava ao médico:** o tratamento acabado, por levantar, conta como "ainda no médico", por isso o bot não o mandava de novo; com o levantamento a falhar, ficava à espera para sempre.
- **Histórico de transferências:** `GET leagues/{L}/transfers` (últimas 100 por liga; `DISCOVERY.md` §3). 1.ª análise: 82 de 94 vendas de utilizadores aos bots foram a 100% do máximo; um utilizador vende sempre a 52–81%; nenhuma venda com máximo acima de ~68 M€ (Espanha cobre ~10 dias, Arménia ~2,5).
- **D-029:** o bot guarda as transferências 1 vez por dia em `logs/<PC>/transferencias/<liga>.json` (`transfers/history.py` puro, `game/transfers.py`, ligado ao ciclo). 1.ª gravação feita (100 + 100). 269 testes.
- `THEORY.md` §7.5: "75% do seu valor" → "75% do preço máximo" (pedido do dono).
- **Não em uso ainda:** a correção do médico e a gravação diária só entram com uma versão nova / o bot reiniciado a partir do código.
- **Janela nova (D-030)** a partir de uma maquete do dono: fundo (`gui/assets/fundo.jpg`, a imagem do dono reduzida para 2560 px; no repo por escolha dele), barra de cima com diárias e "A trabalhar desde", cartões de 3 colunas com anéis de treino, coluna da direita com boss coins e linha do tempo. Código: `board/timeline.py` (puro: ações do bot tiradas das linhas do registo, juntando as seguidas; eventos futuros do snapshot), `loop.py` manda `history` à janela, `view.py` (faixa do jogo, "PRÉ-JOGO · N/8", diárias, timeline), `window.py` (`Ring`, `MatchStripe`, `Backdrop`, `Timeline`; saem o painel de baixo e a barra de estado). 273 testes. Vista com dados reais (só leitura; o passado era de exemplo).
- **Revisão do dono à janela:** estádio em 3 círculos, médico e advogado em círculos por baixo dos treinos (`stadium_rings`, `care_ring` em `view.py`; `Ring`/`RingCell` em `window.py`), só ⚠ no confronto direto, caixas mais opacas (D-030). 2.ª revisão: "2.º Campeonato" + "🏆 taça", rodapé CASA/FORA na faixa (`ElidedLabel`, sem quebra de linha), venda por baixo do dinheiro, estádio centrado, médico/advogado à esquerda com 🩺/⚖️, pré-jogo maior. 276 testes.
- **Janela em inglês (D-031, escolha do dono: janela e avisos):** `src/osmbot/i18n.py` (puro: `WORDS` + `PATTERNS` PT→EN; escolha em `~/.osmbot/config.json`); a janela passa todo o texto por `tr()`; menu "Idioma / Language" reconstrói páginas e menus na hora. O bot e os logs continuam em português. Textos sem tradução ficam em português (ex.: a posição em "FC Van GR" no passado). 280 testes.
- **Regra das recusas (D-032):** `game/refusals.py` (anotações em `~/.osmbot/recusas.json`, por jornada / dia de jogo / momento / dinheiro; apagam-se com a versão); ligada a médico, advogado, analista, amigável, patrocinadores, estádio, início de sessão e missões. Treinos e vídeos sem mudança. Avisos novos traduzidos. 287 testes.
- **Versão 0.9.6** (pedido do dono): `pyproject`, `__init__`, `CHANGELOG`; `dist` reconstruído; notas em `dist/release-notes-v0.9.6.md`.
- **Rumo ao 1.0 (conversa com o dono):** critérios registados em `PROJECT_BRIEF.md` (validar em real todas as escritas, nunca repetir pedidos recusados, 7 dias sem intervenção, sessão expirada). Instalador **verificado pelo dono** no PC pessoal e no da fábrica. Fora do 1.0: transferências automáticas (próxima grande funcionalidade; o dono dá a teoria primeiro), Mac à mão (mais tarde), README público. **Amigáveis em quantidade postos de lado** (10 amigáveis = 40 coins → ~1,5–2 M de valor; `THEORY.md` §6).
- **Advogado:** o bot tentava a cada passagem um suspenso de 1 jogo e o jogo dava 400; o dono explica que com 1 jogo não dá. `LAWYER_MIN_GAMES = 2` (`THEORY.md` §18, `DISCOVERY.md` §3). O pedido de envio do advogado continua por observar (precisa de um suspenso de 2+ jogos).
- **Confirmado:** às 21:08 o bot pôs o Rice no médico (0.9.5), depois de o dono levantar o tratamento à mão.
- **Próximo passo:** o dono vê a janela nova a correr e diz o que mudar; decide quando lançar a versão; quando houver vendas caras guardadas, fazer o estudo dos 100 M€.

## 2026-10-09 (cont. 2) — Fábrica: quadro com "agora · a seguir", estádio com barra, loja

- **Boss coins (pergunta do dono):** o saldo do bot bate com o do jogo (2651 via API, 2646 no topo do site às 14:00); o atraso era a 0.9.3 ler só no fim das passagens. Dono confirmou com Ver → Atualizar. O "-42" era saldo menos o saldo inicial.
- **Pedidos do dono (D-026, correções 0.9.5):** "+X" só da loja; estádio "Campo 1/3" + barra + tempo; pré-jogo sem %; barra de baixo "agora · a seguir" no singular.
- **Código:**
  - `loop.py`: `_doing` / `_now()` em cada fase e em cada vídeo (loja N/9, treino com jogador e clube, dinheiro com clube), vai no payload da janela; `shop_coins` somado a cada vídeo da loja (`coins0` saiu).
  - `view.py`: `doing_view` (pura): mais do mesmo vídeo, o próximo tipo aberto (loja, treino, dinheiro), ou o próximo evento pelo nome.
  - `dashboard.py`: `upgrade_length` (18 h; 4 h se visto a começar; senão só o tempo), `stadium["lengths"]`; `coin_jump` = `shop_coins`.
  - `ads.py`: loja desliza até "Watch ad", devolve os coins ganhos, captura 5 s depois do clique (só guardada se falhar), `watch_with_retry`.
- **Verificado:** 265 testes; no jogo real (só leitura) o "Watch ad" estava em x = 3591 e ficou em x = 602 depois de deslizar.
- **Não verificado em real:** as linhas novas da janela com o bot a trabalhar; a 2.ª tentativa da loja.
- **Versão 0.9.5** (pedido do dono); `dist` reconstruído.

## 2026-10-09 (cont.) — Fábrica: quadro que se atualiza sozinho, vídeos que não se perdem (0.9.4)

- **Pergunta do dono:** o quadro não mostrava o que ele mudou à mão (lista de transferências, banco) passados 10 min. Causa: só o bot lia o jogo, no fim de cada passagem, e "Atualizar quadro" só funcionava com o bot parado.
- **Vídeo de treino a falhar** (09:03, 09:19, 11:51, 12:03; capturas): o resultado do jogo da taça (o dono: aparece **sempre** na 1.ª abertura de cada sessão) surgia tarde, e o "Continue" devolvia à página inicial; depois de as missões guardarem energia, a janela **"Unclaimed Energy"** bloqueou todos os vídeos (14:00).
- **Medido:** uma leitura do quadro = 36 pedidos (77 com a cache vazia), ~9 s, mas **~25 s de CPU**: cada pedido criava um contexto SSL novo (certifi, ~0,35 s de CPU cada).
- **Código:**
  - `client.py`: contexto SSL criado uma vez; cadeado de renovação único no programa (`_RENEW_LOCK`); num 401, relê o ficheiro antes de renovar.
  - `sales.py`: cadeado no ler-e-escrever de `sales.json` (os clubes já eram lidos em paralelo).
  - `ads.py`: `_open_club` confirma o clube (nome no topo à esquerda, sem "Continue", fora da página inicial) e repete até 3 vezes; o treino espera a coluna do treinador; `_dismiss_matchday` carrega em Claim na "Unclaimed Energy" (D-028).
  - Janela (D-027): lê o jogo de 3 em 3 min e em Ver → Atualizar (1.ª opção), com o bot a trabalhar ou não; fica a leitura mais recente (`read_at` no snapshot).
- **Verificado:** 256 testes; ensaio no jogo real (só navegação, sem carregar em "-2h") nos dois clubes: OK. Com isso a janela de energia foi reclamada (autorizado pelo dono).
- **CPU depois da correção (medido):** leitura do quadro com 0,27 s de CPU (antes ~25 s), 1,5 s no total.
- **Verificado pelo dono (0.9.4):** gastou boss coins e o saldo atualizou com Ver → Atualizar. **Ainda por ver:** a leitura automática de 3 em 3 min com o bot a trabalhar.
- `.venv` criado nesta máquina para os testes. **Versão 0.9.4**; `dist` reconstruído.

## 2026-10-09 — Quadro novo (0.9.3), médico e advogado, levantar o analista

- **Observado com o dono (`inspect-writes`):** levantar o analista (`PUT v1.1/…/spyinstructions/{id}/claim` → checklist 1/1) e pôr no médico (`POST …/doctortreatments`, 8 h, sem vídeo). Levantar o médico e todo o advogado por analogia, aceite pelo dono (`DISCOVERY.md` §3). Regras em `THEORY.md` §18.
- **Maquetas** (3 rondas, dados reais, fora do repo) → correções do dono em D-026 (Aceite).
- **Código:**
  - `board/info.py` (puro: próximo jogo e confronto direto, fase da taça, valor do plantel, vendas);
  - `game/clubinfo.py` (leituras do cartão);
  - `game/sales.py` (`~/.osmbot/sales.json`);
  - `medical/policy.py` + `game/medical.py`;
  - levantar o analista em `game/prematch.py`;
  - janela: `ClubCard`, grelha 2×2 com scroll, logótipos em `~/.osmbot/logos`, cor da faixa tirada do logótipo, painel de baixo com contadores.
- **Velocidade:** o quadro lê o jogo em ~4 s (antes ~15 s): pedidos em paralelo (no máximo 6), calendário guardado 10 min, valor dos planteis 1 h; cadeado na renovação da sessão (`client.py`).
- **Verificado:** 244 testes; snapshot real sem erros nos dois clubes; simulação do médico (o lesionado já está no médico → nada; acorda quando acaba) e do pré-jogo; `ativo --simular --sem-anuncios` do início ao fim.
- **Não corrido em real:** levantar o médico (o primeiro acaba cerca das 08:12), advogado, levantar o analista pelo bot, deteção de vendas.
- **Versão 0.9.3** (pedido do dono); `dist` reconstruído.
- **Ideias do dono para o futuro** (registadas em `PROJECT_BRIEF.md` 13 e 14, não construir já): estudar o preço máximo de venda dos jogadores caros pelo histórico de transferências; medir quanto a equipa melhora com os amigáveis, para subir o número por equipa.

## 2026-10-08 (cont. 5) — Casa: `dist` 0.9.1

- PC de casa estava em `64bc921` (0.8.2), 4 commits atrás; o dono fez pull para `1c84296` (0.9.1).
- `.venv` sem `PySide6` → `pip install -e .`; 217 testes a passar.
- `dist` reconstruído (portátil 552 MB, zip 205 MB, instalador 147 MB); verificado com o Python da pasta: `__version__` 0.9.1, `PySide6` 6.12.0, `osmbot.gui.window` importa.
- **Vídeos sem som** (pedido do dono): o Firefox dos vídeos (`ads._launch`, loja/treino/dinheiro) arranca com `media.volume_scale = 0.0`. Corta o som à saída; a página continua a ver o vídeo a tocar (não usa `video.muted`). Teste novo; 218 testes. `dist` reconstruído com isto. **Não verificado em real** que fica mudo (falta o dono ouvir um vídeo).
- **Consola aberta ao lado da janela** (dono, casa): no Windows 11 a consola por omissão é o Windows Terminal; `hide_own_console` (`ShowWindow`) não o esconde, e fechá-lo matava o bot. **Correção** (`build_portable.py`): `OSMbot.exe` passa a ser o `pythonw.exe` (sem consola); `OSMbot-consola.exe` (o `python.exe`) fica para `menu` e comandos. Sem consola, `stdout` vai para `devnull` e um erro fatal abre uma caixa e fica em `~/.osmbot/erro.txt`. O Playwright já esconde o processo dele com `pythonw`. Teste novo (o lançador compila); 219 testes. `dist` reconstruído; verificado: `OSMbot.exe` é GUI (subsystem 2), `status` corre nos dois. **Por verificar pelo dono:** abrir a janela com duplo clique, sem consola.
- **Amigável e análise à última hora** (pedido do dono): regra em `THEORY.md` §6 (4 h antes do jogo, se ainda não houver; adversário indiferente; todas as equipas). Observação com `inspect-writes` (dono: 2 amigáveis, 1 análise) → pedidos e checklist `matchpreparation` em `DISCOVERY.md` §3. **Por fazer:** confirmar se a análise passa a 1/1 sozinha quando o timer de 1 h acaba; OK do dono para construir (escritas novas, regra 5).
- **Construído (D-025):** o dono confirma que a análise passa a 1/1 sozinha e dá o OK. `prematch/policy.py` (puro) e `game/prematch.py`; no ciclo como os outros extras (falha não para os treinos); o bot acorda 4 h antes de cada jogo. Quadro: "pré-jogo: amigáveis N, análises N" no resumo; janela: caixa "Pré-jogo" (10 caixas, 891 px, cabe nos 1060 do quadro). 11 testes novos; 230 a passar. Simulação contra o jogo real (sem escrever): uma equipa já tinha tudo feito pelo dono → nada; a outra → 1 amigável e analista ao adversário da jornada seguinte. **Ainda não corrido em real.**
- **Versão 0.9.2** (pedido do dono): `pyproject`, `__version__`, `CHANGELOG`, README; `dist` reconstruído (portátil, zip, instalador).
- **Próximo passo:** o dono troca a pasta portátil, confirma a janela sem consola e os vídeos sem som, e vê o primeiro pré-jogo real nos logs ("Amigável: …", "Análise: …").
- **Quadro 0.9.3 (D-026):** 20 respostas do dono registadas; confronto direto (±2 lugares) em `THEORY.md` §1. Maquetas com dados reais (janela Qt à parte, fora do repo): 2 clubes e 4 clubes (2×2). Dados confirmados (GET): logótipo (`assets`, URL), `ranking` = posição na liga, `cuprounds` + jogos `matchType` 1 → fase da taça, preço de venda no `transferplayers` (`price`). Valor do plantel por soma (a tabela do jogo está por observar). **Código ainda não mexido.**
- **Achado:** a análise **não** passa a 1/1 sozinha (`DISCOVERY.md` §3). Observado a 2026-10-09 (o dono levantou o analista com `inspect-writes`): `PUT …/spyinstructions/{id}/claim` → checklist 1/1.

## 2026-10-08 (cont. 4) — Fábrica: pull, noite do bot, logs sem escolher pasta

- **Git (`DESKTOP-8OFGOB3`):** o pull tinha feito merge com um commit local antigo (`0.8.1 - Debug`); o dono repôs `main` igual a `origin/main` (comandos dados, regra 9).
- **Noite de 2026-10-08 (casa, 7h44):** sem erros; 55 vídeos da loja, 12 de treino, 3 de dinheiro. "+27 boss coins" no resumo é saldo final − inicial: inclui o que o dono gastou (amigáveis); ganho bruto ~60. *Hipótese* (não verificada): o limite da loja é uma janela móvel de 1 h por vídeo → o bot acorda várias vezes seguidas para 1 vídeo. O dono não quer mexer.
- **Erro 09:26 (fábrica):** "os boss coins não subiram" no 7.º vídeo; captura mostra a loja sem vídeo a correr → provável falta de anúncio; pontual, o bot seguiu.
- **Logs:** o portátil (`Documents\osmbot-portable`, código igual à 0.8.2) não escrevia em `logs/` porque não sabia onde estava o repo. **D-023:** o bot procura-o sozinho (ao lado da pasta do bot, home, Documents, Desktop, OneDrive) e copia o `bot.log` antigo na 1.ª linha; "Pasta dos logs" sai do menu (fica o comando `osmbot pasta-logs`). 202 testes.
- **Estádio −2h (telemóvel):** no código público da web não há vídeo do estádio (só `boost` com boss coins e recolha); ver `DISCOVERY.md`. A app pode ter o pedido, mas é *Hipótese*; e sem página web onde ver o anúncio, usá-lo seria forjar (regra 8).
- **Erro 09:51 (vídeo de treino, `TimeoutError`):** captura = janela de XP de manager ("Lost against manager 2-0") por cima do mosaico TRAINING; apareceu **depois** da verificação das janelas. `ads.py`: `_click_past_windows` (1.ª tentativa 15 s; se falhar, passa as janelas da jornada e tenta de novo) no Shop, Watch ad, TRAINING, −2h e carteira do dinheiro. 204 testes.
- **Versão 0.8.3** (pedido do dono): `pyproject`, `CHANGELOG`, `dist` reconstruído (portátil, zip, instalador).
- **Interface (D-024):** PySide6, só Windows, sem telemóvel, ícone na bandeja. Maquetes (capturas de janelas Qt reais, fora do repo): 1.ª "página web AI slop" rejeitada; 2.ª estilo programa de Windows aprovada; abre logo no quadro (parado → Iniciar), clubes lado a lado, avisos pequenos, redimensionável; X esconde e o bot continua; ícone = logótipo + bolinha verde/cinzenta, sem vermelho, sem notificações. Para a 0.9.0; ainda nada no código.
- **Versão 0.9.0: a janela (D-024)**
  - **Pedido do dono:** "atualizar o dist e toda a documentação".
  - **Código:**
    - `gui/view.py`, puro: snapshot → textos, cores e barras.
    - `gui/window.py`: QMainWindow, ícone na bandeja (bolinha verde-lima com contorno branco ou cinzenta), lock de uma janela por utilizador, consola escondida quando aberta por duplo clique.
    - `loop.run_active(board=...)`, `request_stop()`, `_notices` (erros e avisos para a janela).
    - `osmbot` → janela; `osmbot menu` → consola.
    - `__version__` com teste igual ao `pyproject`.
    - 214 testes, incluindo um de fumo da janela sem ecrã.
  - **Build:** `PySide6-Essentials` cortado a QtCore, QtGui e QtWidgets (49 MB). Portátil 552 MB, zip 205 MB, instalador 147 MB. Verificado: a janela abre com o Qt cortado, a partir do Python da pasta portátil, sem sessão (não leu o jogo).
  - **Não testado em real:** Iniciar/Parar contra o jogo, porque em modo de desenvolvimento não se escreve na conta (regra 5). Fica para o dono.
  - **Nota:** uma captura com `grabWindow` apanhou o ecrã do dono (o browser) em vez da janela; foi apagada logo. A partir daí só se usou `widget.grab()`.
- **0.9.0 publicada pelo dono** (`f236630`, release v0.9.0).
- **Haaland não recolhido (fábrica, 14:11):** às 14:04:58 o bot acordou pela loja (0h05), antes do fim do treino (0h06); viu "0 para recolher" às 14:11:31 e depois fez 15 min de vídeos. Às 14:26 o treino acabado saiu de `wake_events` (só contava `finish > now`), e a verificação seguinte ficou para dali a 46 min. **Correção:** evento "treino por recolher" (agora) → acorda em ~30 s; com recolha falhada espera sempre `WRITE_RETRY` (10 min; antes `min(wait, 10 min)`, que com o evento novo daria 30 s). Teste novo. O "treino novo a decorrer" que o dono viu não aparece nos logs (nenhum treino de ATA iniciado depois das 08:11): *por esclarecer*.
- **0.9.1, janela revista pelo dono:**
  - ecrã inicial pequeno (Abrir · Login · Sair). Abrir → símbolo a rodar → bot a trabalhar → a janela cresce para o quadro (`QStackedWidget`, 3 faces);
  - sem barra de botões; avisos e erros em Ver (janela à parte);
  - resumo em fila de números (`view.session_view`);
  - X com o bot parado fecha o programa;
  - 217 testes.
- **Incidente (Claude):** o rebuild da 0.9.1 esvaziou `dist/osmbot-portable` enquanto o dono corria a 0.9.0 **a partir dessa pasta**. Foram apagados `app/` e `browsers/` (Firefox) antes de o Windows bloquear um `.pyd` em uso. Consequência: os vídeos desse bot falham até ele ser reaberto com a pasta completa. **Prevenção:** o `build_portable.py` recusa construir se houver um `OSMbot.exe` a correr dessa pasta (`running_from`).
- **`dist` 0.9.1 reconstruído** depois de o dono fechar o bot: completo (`app/`, `browsers/`, LEIA-ME); janela verificada com o Python da pasta portátil.
- **Próximo passo:** o dono testa em real (Abrir → carrega → quadro; Parar/Iniciar no menu; X; ícone), faz commit/push e o release.

## 2026-10-08 (cont. 3) — Registo do bot no repo (0.8.2)

- **Pedido do dono:** todos os logs no repo, para analisar de qualquer máquina. Perguntado: repo público → o dono quer-os **completos** ("não estou preocupado com isso"); tem o repo clonado em todos os PCs. **D-022** aceite (exceção a D-016 só para `logs/`); `CLAUDE.md`, `README`, `RISKS_AND_COMPLIANCE` atualizados.
- **Código:** `src/osmbot/logs.py` (`logs/<PC>/AAAA-MM-DD.log`, apaga tokens/e-mails, nunca falha), ligado ao `_log` do ciclo; menu **Pasta dos logs** e `osmbot pasta-logs`; `config.json` em `~/.osmbot`; testes nunca escrevem no repo verdadeiro (`conftest`). 198 testes.
- **Este PC (`DESKTOP-KAM70RR`):** pasta escolhida; 4 dias do `bot.log` antigo copiados para `logs/` (nenhuma linha com aspeto de segredo). As linhas do bot que está a correr (versão antiga) só entram a partir do reinício com a 0.8.2.
- **Ficou de fora:** capturas de ecrã das falhas (`~/.osmbot/failures`, ~1 MB cada) e o `inspect-writes.log` (é quase um dump de pedidos; regra 6).
- **Próximo passo:** em cada PC, depois de instalar a 0.8.2, menu → Pasta dos logs (uma vez).

## 2026-10-08 (cont. 2) — Diagnóstico do bot a correr; só a loja salta janelas

- **Diagnóstico (00:19, só leitura):** sem falhas desde as 00:09; 9 vídeos da loja; 0 treinos porque os 8 treinadores estavam ocupados (Real Betis acaba ~01:44, FC Van ~07:48). Vídeo de treino: "janela saltada" (15% ao acaso) → os −2h do FC Van ficavam para a passagem seguinte (~00:59).
- **Pedido do dono → D-021:** o salto ao acaso fica só na loja; treino e dinheiro vêem-se sempre. `ads.py` (`run_training_ads`, `run_money_ads`), testes: 190 a passar. Versão **0.8.2** (pedido do dono); docs revistos (`PROJECT_BRIEF`, `RISKS_AND_COMPLIANCE` também tinha "~35%" e "parar à primeira falha", anteriores a D-019/D-021; README). `dist` reconstruído. O bot instalado só apanha isto depois de reinstalar.

## 2026-10-08 (cont.) — Boss coins por dia e ideia dos amigáveis

- **Release v0.8.1:** notas em `dist/release-notes-v0.8.1.md`; o dono publica (regra 9).
- **Estimativa:** `bot.log` da noite de 2026-10-07 = 55 vídeos da loja em 7 h (~8/h, 1 coin cada) → **~140 boss coins por 18 h** (máximo 162). Limite diário da loja por verificar (nunca correu 18 h seguidas).
- **Ideia do dono:** gastar as coins em amigáveis (sobem as stats). Regras dele registadas em `THEORY.md` §6 (1 por adversário por jornada, ~25 por equipa, não cansam). **Não construir:** o dono quer ver o ganho real de coins durante uns dias primeiro.
- **Próximo passo:** o dono corre o bot uns dias e vê `Boss coins +X` no quadro / `Resumo` no `bot.log`; depois decide os amigáveis (quantos, que clube, reserva) e faz-se a observação com `inspect-writes`.

## 2026-10-08 — Vídeo de treino preso, bot que não pára à 1.ª falha (0.8.1)

- **Análise do repo a pedido do dono** (fábrica: "dá erro dos treinos… fica a bloquear tudo"). Achados: bot parava à 1.ª falha de escrita / 3 min sem rede; sessão em memória podia ficar velha; `THEORY` §17 desatualizado; estádio vs §15; `POST weeklytrack` repetido; "reabre" da troca de posição sem verificar o limite; início de sessão não gasto nunca se repetia.
- **Causa do vídeo de treino (reproduzida aqui, sem janela):** depois do "Continue" vêm "Skip", outro "Continue" e a janela da experiência (fecha com clique fora). Registado em `DISCOVERY.md` §3. `_dismiss_matchday` passa a cadeia toda; ensaio real `watch_training_video(dry_run=True)` encontrou o "-2h" em 33 s. Nota: as sondagens fecharam a cadeia do FC Van, por isso o ensaio final já não a viu; a cadeia está coberta pelos testes.
- **D-019 aceite** (pedido do dono): falhas nos treinos → volta a ver em 10 min, pára só ao fim de 3 passagens seguidas; rede: pausas de 1 a 15 min até 6 h; vídeos que falham sempre: 10/20/40/60 min por tipo.
- **Sessão:** `OsmClient` relê `session.json` antes de renovar (e com `force` depois de um 401); o browser dos vídeos só grava tokens mais recentes (`save_browser_session`).
- **Estádio (ponto 3):** comportamento **não mudado**; o jogo não dá o preço. O dono confirmou: fundos a 0 nunca são problema. Registado em `THEORY.md` §15.
- **Testes:** 189 a passar. Versão **0.8.1**; `dist` reconstruído.
- **Próximo passo:** o dono corre a 0.8.1 na fábrica e vê o vídeo de treino depois de uma ronda. (Os treinos do FC Van postos a 2026-10-07 ~13h30 foram o dono, à mão; o PC da fábrica estava desligado.)

## 2026-10-07 (cont. 5) — Recompensas diárias automáticas (0.8.0, por testar em real)

- **Observação feita pelo dono** (`inspect-writes`, 6 reclamações à mão) → pedidos exatos em `DISCOVERY.md` §3. Regras do dono em `THEORY.md` §17; decisão **D-020** (reclamar e guardar; nunca usar itens). Energia do início de sessão: o bot gasta-a (o site também o faz; o inventário tem limite); boss coins: para a carteira ("não há nada a ver", dono).
- **Código:** `src/osmbot/rewards/policy.py` (puro: o que reclamar, dia da semana, limites do inventário) e `src/osmbot/game/rewards.py` (pedidos). `loop.py`: passo novo "extra" no ciclo (falha não pára os treinos), acorda no novo dia e quando os vídeos reabrem, atualiza o quadro após reclamar. `osmbot recompensas [--simular]`. Quadro: linhas `diárias` e `extra`.
- **Risco apanhado em simulação real:** o bot ia reclamar o prémio do **dia 4** hoje (a lista mostra os prémios de todos os dias). Corrigido: só se reclama o prémio cujo `sourceType` é o dia de hoje, calculado a partir de `endDateTime` (semana de 7 dias, mudança às 04:00 UTC), e no máximo um por dia.
- **[S]** Dias com boss coins: o pedido que as gasta depois do login nunca foi observado (usa-se o `bosscoinwallet/consumereward` dos vídeos, com verificação de que o saldo sobe). Saco do dia 21: reclamado e deixado no inventário. Prémios de recompensa de dias 4 a 7 (boss coins, energia, cone, pack 85+): reclamados com "guardar".
- **Testes:** 179 a passar. Simulação contra a conta real (só leituras + `POST weeklytrack`): hoje não há nada por reclamar.

## 2026-10-07 (cont. 4) — Início de sessão e missões: o que se sabe e preparação da observação

- **Pedido do dono:** automatizar (1) a recompensa de início de sessão e (2) as recompensas das missões (3 cartões de treino + a recompensa do "dia" da faixa semanal, que só abre depois de reclamar os 3).
- **Lido (GET, só leitura):** `user/dailylogin` → `consecutiveLoginCount`, `isClaimable`, `countdownTimer` (tipo 19, ~16,5 h até ao reinício), `matchBoost`, `rewardTrackDays` (5 dias: `dayNumber`, `actionId` como `DailyLoginEnergy_1` / `DailyLoginBossCoin_5`, `isClaimable`, `isMilestone`). `missions` → **catálogo** de 324 definições (`id`, `threshold`, `progressType`, `actionId`), **sem** o progresso do utilizador. `POST usermissions/weeklytrack` é só o site a registar progresso.
- **Por saber [?]:** os pedidos de "Reclamar" (início de sessão, cartões, recompensa do dia) e o endpoint do estado das missões do utilizador. Nunca observados (regra 7).
- **Preparado:** `inspect-writes` grava em `~/.osmbot/inspect-writes.log` em tempo real, com valores curtos e as leituras. A observação é de uma só tentativa (depois de reclamar não se repete hoje; renova-se amanhã), por isso primeiro faz-se um ensaio sem reclamar nada.
- **Nota:** a espera da loja depois de esgotar é de **1 h, confirmada pelo dono** (acima); `SHOP_BAR_SECONDS` não é suposição.
- **Testes:** 151 a passar.

## 2026-10-07 (cont. 3) — Vídeo de treino que falhava e quadro só com erros (0.7.2, por testar em real)

- **Falha do vídeo de treino:** `bot.log` mostrava "botão do vídeo de treino não encontrado (TimeoutError)" a cada passagem. As capturas de `~/.osmbot/failures` mostram a causa: o ecrã "Matchday … Continue" fica por cima do clube e esconde o menu e o botão. Todas as tarefas do browser (loja, treino, dinheiro) passam por `_open_game`, que carrega em "Continue" (máx. 3) depois de abrir o jogo; `_open_club` volta a fazê-lo depois de entrar no clube. O dono confirmou que o ecrã aparece muitas vezes depois de um jogo, seja qual for a tarefa. **[S]** Clique novo, não observado antes em real; o dono testa.
- **Quadro:** linha das Boss coins com a loja (barra pequena + tempo, só quando a loja esgota; com vídeos disponíveis não mostra nada), atualizada após cada vídeo da loja; registo só com erros (30 min).
- **[S]** Barra da loja assume 1 h (`SHOP_BAR_SECONDS`); a API só dá o tempo que falta (visto: máx. 49 min no `bot.log`).
- **Testes:** 147 a passar.

## 2026-10-07 (cont. 2) — Acabamento do menu e do quadro (0.7.1, por testar em real)

- **Pedidos do dono (2 rondas):** menu com setas; barra no estádio (na mesma linha) e nos treinos (2 h encurtadas a azul), 1 jogador por linha; clube a verde; "Lista de Transf." a branco com números amarelos só se houver vaga; linha dos vídeos apagada; `Boss coins N +X`; aviso de como parar; mais atualizações instantâneas.
- **Cores (regra fixa, no topo de `dashboard.py`):** verde feito/bom · amarelo atenção · azul tempo que falta/encurtado · cinzento etiquetas e vazio · vermelho erros. O segundo clube aparecia a verde porque o nome mudava de cor consoante as vagas; agora todos os clubes têm a mesma cor.
- **Janela pequena:** em vez de tirar barras ou juntar treinos, o quadro encurta o registo e as linhas em branco. Largura até 100 colunas, ajustada à janela.
- **Instantâneo:** `loop.py` volta a ler o jogo (`refresh_board`) depois de recolher/treinar, estádio, patrocinadores e cada vídeo de dinheiro (antes só no fim da passagem, que inclui os vídeos); um vídeo de treino atualiza logo a hora e a parte azul da barra.
- **Menu:** setas ↑ ↓ + Enter (`read_key`: `msvcrt` no Windows, `termios` no macOS/Linux); fora de um terminal (testes, pipes) continua a pedir o número.
- **Ctrl+C:** a causa provável era o modo "Selecionar" (QuickEdit) da consola do Windows, que congela o bot quando se clica na janela. Fica desligado enquanto o quadro corre. **[S]** Se continuar a falhar durante um vídeo (Firefox aberto), falta uma tecla alternativa para parar.
- **Testes:** 141 a passar (Python temporário fora do repo).

## 2026-10-07 (cont.) — Menu novo e quadro redesenhado (por testar)

- **Menu:** só Iniciar, Login e Sair; centrado, com arte ANSI, título e introdução. Estado, simulação e "sem vídeos" saem do menu e ficam só como comandos (`status`, `treinos`, `slots`, `ativo --simular`, `ativo --sem-anuncios`).
- **Quadro:** sai a linha "A seguir"; "Lista de transferências 4/4"; estádio com ✓ verde (feito) e azul + barra (a construir, 18 h); patrocinadores "4/4 escolhidos"; dinheiro de 1000 k para cima passa a "1 M"; cansados numa linha por clube; `▶`, `⚠` e `✓` trocados por `»`, `!` e `√` (causa do `[?]`: a fonte da consola não os tem); loja com barra no fundo; resumo só com "salto +X" (verde) e vídeos (treino com "encurtadas X h", 2 h por vídeo); boss coins atualizam logo após cada vídeo da loja. Largura 66 → 76.
- **Bug corrigido:** a variável `level` do estádio sobrescrevia o nível de compactação do quadro.
- **Suposição [S]:** a barra da loja usa 3 h como duração da espera (`SHOP_BAR_SECONDS`); falta confirmar com os dados reais.
- **Por testar:** nesta máquina não há Python (só o atalho da Loja), por isso os testes **não foram corridos**.

## 2026-10-05 — Windows operacional; D-014 (autonomia); `--simular`

- **Autonomia (D-014):** regra 5 reescrita em 3 níveis (leitura livre; `recolher`/`treinar` autónomos só com o bot "ativo", sem teto; escritas novas pedem OK). Em desenvolvimento o Claude não escreve na conta. Criado `.claude/settings.json` (permissões do projeto) — a inversão do padrão foi bloqueada antes dele e passou depois.
- **Código:** `recolher`/`treinar` escrevem por omissão; `--simular` = ensaio (`--confirmar` alias escondido). Saída UTF-8 no Windows. `*.egg-info/` no `.gitignore`. 59 testes.
- **Windows:** venv sem `certifi` (corrigido com `pip install -e ".[dev]"`); `osmbot login` feito; `status`/`treinos`/`--simular` OK. **Sessões Windows e Mac independentes** (testado nos dois sentidos, `DISCOVERY.md` §3).
- **Estado do jogo:** 8 treinos prontos há ~15h (nada recolhido nesta sessão); GR de 31 anos treina (regra nova, caso do Clube B fechado).
- **Modo ativo construído:** `src/osmbot/game/loop.py`, `osmbot ativo` (`--simular` = 1 passagem). Dorme até ao fim do próximo treino (+jitter), por isso se adapta a treinos curtos. Pára à 1.ª falha de escrita / sessão perdida / 3 erros de rede; log em `~/.osmbot/bot.log`. 66 testes. Ensaio em simulação OK; **ainda não ligado em real**.
- **Treinos tratados em real (dono: "bot ativo", 1 passagem):** `recolher` + `treinar`, 8/8 com estado 200, ciclo não ficou ligado.
- **Aviso de slots de venda livres:** `osmbot slots` + verificação no modo ativo; aviso só na consola e no `bot.log` (escolha do dono, por agora). Limite lido de `gamesettings` (`DISCOVERY.md` §3). 71 testes.
- **Anúncios (A4), prioridades do dono:** 1.º **loja** (boss coins), 2.º **treino** "quando der" (encurta o treino, o bot de treino volta a agir mais cedo), 3.º os **3 de dinheiro diários**, "eventualmente". Passo seguinte: observar os pedidos (`inspect-writes`) com o dono a ver um anúncio de cada tipo; só depois construir. Regras: limites do jogo respeitados, janelas saltadas ao acaso, nunca forjar recompensas (D-012, regra 8).
- **Anúncios da loja (A4) feitos:** observação dos 3 tipos de vídeo (loja `BusinessClub`, treino `TrainingTimer`, dinheiro `Multistep1-3`); teste com browser controlado (visível e sem janela) OK; `ads.py` integrado no `osmbot ativo`. Dono aceitou que ~metade dos anúncios nem carregam e a recompensa vem na mesma (comportamento do site). Permissões: o dono acrescentou `Bash(.venv/Scripts/python.exe:*)` por `/permissions`; o sistema continua a pedir ao dono para testes que ganham coins. 78 testes. **Falta:** vídeo de treino (−2h, `TrainingTimer`) e os 3 de dinheiro; ligar o `ativo` em contínuo.
- **Vídeo de treino construído (`ads.py`, `loop.py`):** regra "uniformizar" do dono (THEORY §12.1); ensaio sem clicar, sem janela, no Clube B: encontrou o botão "- 2h" da coluna certa. Clique real feito pelo dono: GR do Clube B 5h58 → 3h06 (−2h). OK. 82 testes. **Falta:** os 3 vídeos de dinheiro e ligar o `ativo` em contínuo.
- **UI de consola (D-015):** desenho em browser feito e descartado a pedido do dono ("pode ser de consola"); construído `dashboard.py` + integração no `loop.py` (quadro que se redesenha por segundo, `--sem-quadro`). Despertar mais fino: acorda também quando a loja / o vídeo de treino reabrem. Verificado em real com `ativo --simular` (só leitura). 88 testes. **Ainda não corrido em contínuo.** Nota: a ferramenta de publicar Artifacts falhou por regra de leitura (mesmo com a regra do dono), por isso o desenho foi gerado como HTML local e apagado depois.
- **Versão portátil Windows (D-016):** `tools/build_portable.py`; pasta de 495 MB / zip de 183 MB em `dist/` (fora do git). Verificada em local com o Python dela (status, slots, ativo --simular, Firefox 155). **Ainda não testada noutro PC.** Mac fica como está.
- **Menu na consola (pedido do dono: "tudo na consola, com as opções"):** `src/osmbot/menu.py`; `osmbot` sem argumentos abre o menu; o portable passou a ter só `OSMbot.bat`. Testado com o Python do portable (opção 3). 93 testes. **Falta o primeiro teste no PC da empresa.**
- **Resumo de ganhos:** o quadro mostra, desde o arranque: variação do saldo de boss coins, vídeos (loja/treino) e treinos recolhidos/postos; o mesmo no registo ao parar. O saldo conta também o que o dono gastar à mão. 94 testes. Dono perguntou se o bot corre sem o VS Code: sim, via `OSMbot.bat` ou o terminal normal; fechar a consola pára o bot.
- **Primeiro arranque real do `ativo` (2026-10-05 23:40, dono, janela própria):** recolher/treinar (0 prontos) e 1.º vídeo da loja OK. Defeito visto na captura do dono: o quadro ficava parado e sem dados durante a passagem (que pode durar minutos com os vídeos). Corrigido: estado inicial lido logo ao arrancar e redesenho durante as pausas e a cada linha de registo. 95 testes. Portable ainda por reconstruir com isto (não se pode enquanto o bot corre da pasta dist).
- **2.º defeito (visto no registo do 1.º arranque):** o bot viu 2 vídeos da loja (saldo 2452 → 2454) mas o resumo dizia 0, porque contava no fim da série e o dono parou a meio. Corrigido (`_counted`); portable reconstruído (183 MB). 96 testes.
- **`OSMbot.exe` em vez de `.bat` (pedido do dono):** `python.exe` oficial renomeado + `sitecustomize` que abre o menu / passa os comandos; testado de outra pasta (menu, `slots`, `status`, `ativo --simular`). Portable reconstruído (183 MB). **Falta testar no PC da empresa e o arranque real com o quadro novo.**
- **3.º defeito do quadro (captura do dono, 23:49):** o redesenho ia para o stdout redirecionado enquanto o bot trabalhava, por isso o ecrã ficava parado e o registo ficava com lixo (`[90m…`). Corrigido (`Screen` guarda o terminal real) + teste de regressão; 97 testes.
- **Instalador:** Inno Setup 6.7.3 instalado por `winget` (só para o utilizador); `tools/installer.iss`; ícone do OSM convertido para `tools/local/osmbot.ico` (fora do git). `dist/OSMbot-Setup.exe` 134 MB; instalar/correr/desinstalar testado numa pasta temporária.
- **Publicação (dono: "C", repo e Release públicos):** varredura de segredos limpa (nenhum token, ID, email ou nome de manager). Substituídos por termos genéricos os clubes, ligas, o plantel do dono e os **nomes de utilizador de outros jogadores** (dados de terceiros que estavam em `THEORY.md`). Ícone original; instalador reconstruído sem arte do jogo (127 MB). **Aviso dado ao dono:** o histórico já enviado ainda contém os nomes antigos (2 commits); reescrevê-lo (filter-repo + force push) é dele.
- **Próximo passo (antigo):** o dono diz "bot ativo" e corre-se `osmbot ativo` (começa por recolher os 8 treinos parados). Depois: notificação de SALE (só leitura); D-006 a reescrever. Duas máquinas ativas ao mesmo tempo não é suportado.

## 2026-10-07 — Estádio, vídeos persistentes

- **Vídeos de dinheiro/loja/treino:** o dono teve o bot um dia inteiro no PC da empresa e só recolheu 20 coins: causa provável = os vídeos desligavam-se de vez após 2 falhas. Agora nunca se desligam (tentam de novo em ≤10 min), `ENGAGE_CHANCE` 0.85, capturas de ecrã das falhas, limite de página 60 s.
- **Observado com o dono (`inspect-writes`/`inspect-network`):** escolher patrocinador (`POST sponsors`), melhorar estádio (`POST stadiumparts`), poupança (`PUT savings/transfer`, sem corpo, mesmo pedido nos dois sentidos), propostas de patrocinador (`GET sponsors/offers`). Ver `DISCOVERY.md` §3. Regras do dono em `THEORY.md` §15.
- **Construído:** `stadium/policy.py` (puro) e `game/stadium.py`, comando `osmbot estadio`, integrado no modo ativo (acorda no fim da melhoria). 108 testes; `estadio --simular` lido em real. **Escritas não executadas na conta** (regra 5: escrita nova pede OK).
- **Patrocinadores construídos** (`sponsors/policy.py`, `game/sponsors.py`, `osmbot patrocinadores`, no modo ativo). 114 testes; `--simular` em real propõe preencher 2 espaços livres num clube e 3 no outro. Escrita não executada.
- **Aviso de condição física** (`theory/fitness.py`, quadro e registo): amarelo = abaixo de 80 (dono: Mendes 79 amarelo, Koné 80 verde); titulares = `lineup` 1-11 (`THEORY.md` §16, `DISCOVERY.md`). 118 testes; lido em real. Médico/advogado: ainda sem pedidos observados.
- Dono: "sempre a melhor para cada espaço" (repetir permitido; recusa → a seguinte). 115 testes.
- **Por fazer:** 1.ª execução real do estádio pelo dono; o que o jogo responde ao recusar por falta de dinheiro (assumido 4xx).

## 2026-10-06 (cont.) — Linguagem da interface e vídeos de dinheiro

- Dono quer ritmo mais rápido e menos testes ("vou depurando entre versões"), e que a interface não soe a assistente. Reescritos todos os textos visíveis (menu, quadro, registo, comandos).
- **Vídeos de dinheiro** implementados (`ads.py`, `loop.py`, `dashboard.py`): janela Savings > "Free rewards" (`.clubfunds-wallet` abre; `.multistep-block-container.step-available` é o cartão por ver; `.step-reached` os vistos); clube com mais `savings` (`GET .../finances`). Não testado em real. 100 testes.
- **Para a recolha de recompensas eventuais, médico, advogado e outros timers** é preciso ver os pedidos reais (os endpoints que tentei dão 404; regra 7): o dono faz cada ação uma vez com `osmbot inspect-writes`. Timers vistos em `timers`: tipo 7 *Stadium training*, tipo 8 *Data Analyst*.

## 2026-10-06 — Versão 0.5.0 e documentação em dia

- **Versão 0.5.0** fechada (`pyproject.toml`, `CHANGELOG.md`): modo ativo, vídeos da loja e de treino, aviso de slots, quadro de consola, menu, pasta portátil e instalador para Windows. 97 testes. Mensagem de commit entregue ao dono (git é dele).
- **Documentação revista de ponta a ponta:** `CLAUDE.md` (estado, mapa do código), `README.md` (utilização, Windows), `PROJECT_BRIEF.md` (estado de cada automação), `RISKS_AND_COMPLIANCE.md` (postura decidida e publicação pública), `OPTIONS.md`, `GLOSSARY.md`, `DISCOVERY.md` §7, `DECISIONS.md` (D-017 a D-019 em aberto).
- **Publicada (2026-10-06):** o dono fez o commit e o push (`462de4d`); o Claude, com a autorização dele, instalou o `gh` e criou o Release **v0.5.0** público (`OSMbot-Setup.exe` e `osmbot-portable.zip`) com as notas do CHANGELOG. **D-017 aceite:** o histórico fica como está.
- **Pendente:** teste no PC da empresa e arranque real prolongado com o quadro novo; vídeos de dinheiro; transferências; D-018 (estatísticas), D-019 (concorrência com o dono).

## 2026-10-04 — Renovação real corrigida (AppVersion)

- A 1.ª renovação a sério falhou (400, "must update the app"): faltava o cabeçalho `AppVersion`. Agora `browser.py` guarda os cabeçalhos do pedido real em `~/.osmbot/client.json` e o cliente repete-os; aviso claro se a versão ficar velha. Renovação sem browser confirmada. 53 testes.
- Códigos do plantel confirmados pelo dono (posições, `unavailable` = jogos de ausência, `lineup`); timers têm título legível. Ver `DISCOVERY.md`.
- Dono confirmou: treinos terminados = tempo negativo no timer (pronto a recolher). Criado `osmbot treinos` (só leitura): por clube, cada sessão (jogador, posição, pronto/faltam) e próximo jogo. 55 testes.
- Tentativa de verificar o ecrã sem janela (Firefox headless, só leitura): funciona para ver a página inicial; navegar pelos menus (hover) falhou. Chrome extension não estava ligada. O dono carregou-se uma vez em *Continue* do jogo (autorizado); nada foi recolhido nem alterado.
- **Feito:** `osmbot inspect-writes` (observador de pedidos de escrita, sem valores). O dono recolheu 1 treino e pôs 1 a treinar com o browser aberto: pedidos de *claim* e de *start* observados e registados em `DISCOVERY.md` §3. `trainer` = posição do jogador.
- **Construído (ainda não executado em real):** `osmbot recolher` e `osmbot treinar`, ambos com pré-visualização por omissão e `--confirmar` / `--max N` para escrever. `treinar` usa `plan_training` (THEORY §5), exclui listados para venda (lidos de `transferplayers/0`) e procura o id da duração em `gamesettings` pelo nome. Corrigido `Player.from_api`: lesionado = `unavailable > 0` (não `injuryId`). 57 testes.
- **Primeiro uso real (2026-10-04, dono correu):** `recolher --confirmar --max 1` → 200 (Jogador 24 recolhido); `treinar --confirmar --max 1` → 200 (Jogador 24 a treinar, ~8h). `timerGameSettingId` confirmado. Dono não quer escrever `--confirmar` sempre; inverter o padrão foi bloqueado pelo sistema de permissões → fica `--confirmar` até haver modo automático (decisão do dono pendente).
- **Próximo passo (antigo):** primeiro uso real com `--max 1` (dono corre); confirmar que o `timerGameSettingId` está certo e que o jogo aceita os pedidos do bot; depois alargar. Pendente: rever o caso do GR do Clube B (política escolhe um GR de rating 50 porque o melhor tem 30+).

## 2026-10-03 — Formato do `tokenRefresh` observado (Mac)

- Dono deu OK explícito para contacto real nesta sessão (regra 5). Correu `osmbot inspect-network` com a sessão de 3 dias: o site renovou os tokens sozinho. Formato registado em `DISCOVERY.md` §3 (OAuth2 `refresh_token`, pedido form-urlencoded, resposta JSON). Só leitura; nada foi escrito na conta por nós.
- **Cuidado:** o pedido leva `client_id`/`client_secret`; tratar como segredo, nunca versionar.
- **Feito (cont.):** `src/osmbot/game/client.py` (cliente sem browser, renova o token, só GET, `urllib` + `certifi`), `osmbot probe <caminho>` (mostra só a estrutura da resposta) e `osmbot status` (clubes + boss coins). Códigos do cliente apanhados do browser para `~/.osmbot/client.json`. 51 testes a passar. Bearer confirmado (200).
- **Pendente:** testar no Windows (sessão + `certifi`); confirmar que `ranking` é a posição na liga; testar se login numa máquina desliga a outra.
- **Feito (cont. 2):** `probe` aceita `{L}`/`{T}` (preenche com a equipa do slot, `--slot`). Estrutura de `players`, `trainingsessions/ongoing`, `timers`, `teamtrainings` registada em `DISCOVERY.md` §3.
- **Próximo passo:** decifrar os códigos numéricos (posição, estado, tipo de timer) cruzando com o ecrã do jogo, só valores, sem nomes; depois desenhar o leitor de treinos (sessões a acabar, slots livres).

## 2026-09-30 — Sessão persistente: causa encontrada e solução (Mac)

- **Correção:** o "login funciona" de 2026-09-28 só queria dizer que o Firefox abria e dava para fazer login; a sessão **nunca** ficou guardada (o dono tinha de repetir o login, também no Windows e no Firefox normal).
- **Causa (Verificado, `inspect-session`):** `access_token` e `refresh_token` do OSM são cookies de sessão, apagados quando o Firefox fecha; só a sessão do Facebook dura (1 ano) — daí o botão "Continuar como Carlos". Ver `DISCOVERY.md` §3.
- **Solução:** `browser.py` exporta os cookies (`context.cookies()`) para `~/.osmbot/session.json` (0600, fora do repo) ao fechar a janela e restaura-os no arranque. **Testado pelo dono no Mac:** `login` → `dashboard` entrou direto no jogo. Perfil persistente abandonado.
- **Armadilhas:** `input()` falha com EOF quando corrido via `!` no Claude Code → o fecho da janela é o sinal. `context.storage_state()` em ciclo abre janelas brancas e parte o popup do Facebook → usar só `cookies()`.
- **Novo comando:** `osmbot inspect-session` (descoberta: só nomes/tamanhos, nada em disco).
- **Ambiente Mac:** venv em `.venv/bin`, Playwright/Firefox instalados; README/CLAUDE.md com instruções Windows+macOS e `.gitattributes` (eol=lf).
- **Cont.: tokens e renovação descobertos** (`token-info`, `inspect-network`): ver `DISCOVERY.md` §3. Resumo: access 20 min, refresh 7 dias com prazo deslizante, `POST /api/tokenRefresh`. Não escrever IDs de ligas/equipas nos docs (repo público).
- **Próximo passo:** observar só o **formato** (nomes de campos, não valores) do corpo e da resposta do `tokenRefresh`; depois cliente HTTP com renovação automática, depois `status`.
- ~~**Por fazer:** (1) repetir `osmbot dashboard` horas/dia depois para medir a validade do `access_token`; ~~(feito acima)~~ Resta: testar no Windows.

## 2026-09-28 (cont.) — Login funciona; mudança para Firefox

- **Problema:** o popup de login do Facebook (única via de login desta conta, não há email/password) ficava preso em branco no Chromium do Playwright. Causa: o build "Chrome for Testing" que o Playwright usa é detetado e bloqueado pelo Facebook, independentemente de o login ser feito à mão por uma pessoa real.
- **Tentativa 1 (chumbou):** `channel="chrome"` (Chrome instalado a sério) — não estava instalado na máquina, e o dono preferiu não instalar.
- **Solução:** trocar Chromium por **Firefox** (também trazido pelo Playwright, sem instalar nada como programa no Windows — fica só na cache dele, tal como o Chromium). `src/osmbot/game/browser.py` atualizado para `playwright.firefox.launch_persistent_context`; perfil movido para `~/.osmbot/firefox-profile` (o antigo `browser-profile` do Chromium, vazio/sem login, foi apagado). `README.md` atualizado.
- **Confirmado pelo dono: login deu certo.** Primeiro contacto real com o jogo funcional.
- **Próximo passo:** construir o comando de leitura (listar clubes ativos, dinheiro, posição na liga) para validar a sessão sem mexer em nada, antes de qualquer automação de treinos.

## 2026-09-28 — Primeiro contacto real: `osmbot login`

- **Discussão de arquitetura de execução** (como o bot deve correr no dia-a-dia): esclarecido que só uma máquina (fixo/portátil/MacBook) está ativa de cada vez, e o bot só corre quando o dono o ativa manualmente — não há arranque automático ao ligar (isto substitui a ideia inicial da D-006 de arranque automático por Task Scheduler/LaunchAgent; D-006 ainda não foi formalmente reescrita, fica para quando a interface de consola/tray estiver a ser construída a sério). Consola visível, minimiza para o tray em vez de fechar. Histórico de estatísticas (boss coins, horas pupadas) deve ser **unificado** entre as 3 máquinas (implica pasta sincronizada tipo OneDrive/Dropbox, por implementar).
- **Conta:** o dono confirma até **4 slots de equipas/campeonatos** por conta, atualmente **2 ativos**; o bot deve automatizar todas as que estiverem ativas.
- **D-004 emendada:** o dono decide começar já pela **conta principal**, não por uma conta secundária como o plano original prometia. Risco fica mais exposto (sem "conta descartável" a isolar). Registado como emenda, não reescrita silenciosa.
- **D-013 encerrada:** o dono deu **OK explícito nesta sessão** (regra 5 do `CLAUDE.md`) para contacto real com o jogo — login e leitura, para já.
- **Login:** decidido usar um **perfil de browser persistente** (Playwright, `launch_persistent_context`) guardado em `~/.osmbot/browser-profile` (fora do repo). Primeira vez, o dono faz login à mão numa janela real; sessão fica guardada e reutilizada sozinha depois — sem copiar cookies, sem guardar password.
- **Código novo:** `src/osmbot/game/browser.py` (`open_login_session`), `src/osmbot/cli.py` (comando `osmbot login`), `pyproject.toml` com `playwright` como dependência de runtime e entry point `osmbot`. Instalado no `.venv` e o Chromium do Playwright. `README.md` atualizado com instruções de instalação/login. Nada disto tem testes automáticos (é a camada de contacto real, ao contrário de `theory`/`training`, que continuam puras e testadas).
- **Ainda por fazer, na ordem discutida:** (1) o dono corre `osmbot login` e confirma que funciona; (2) comando de leitura só (lista clubes ativos, dinheiro, posição na liga), para validar a ligação sem mexer em nada; (3) só depois, automação de treinos a sério.
- **Próximo passo:** esperar o dono confirmar que o login funcionou, depois construir o comando de leitura.

## 2026-09-27 (cont. 23) — Taxa de juro confirmada (2%); lista de dúvidas observáveis esgotada

- Dono deu mais 2 exemplos (Clube A 26,6M→534k = 2,01%; Clube B 3,8M→76k = 2,00%), juntando ao exemplo anterior (2,00%) para **3 pontos de dados, todos ~2%** → taxa de juro confirmada em `THEORY.md` §13.
- **Isto fecha toda a lista de dúvidas observáveis** que vínhamos a trabalhar desde cont. 14: formação/titular fraco (teoria), mínimos por posição (ATT/MID/DEF/GK), multiplicador de preço máximo, estádio, moedas de patrocinadores/médico/advogado, vídeos de treino e da loja, e agora o juro.
- **Ficam só 4 pontos menores em `[?]`, sem urgência:** (1) nome do campo `statAtt`/preço máximo na API — precisa de inspeção de rede, fica para quando houver OK de contacto com o jogo (regra 5); (2) valor exato do skip do médico/advogado em boss coins; (3) se os 9 vídeos da loja ainda dão recompensa extra (era descrito para o antigo "10").
- **Próximo passo:** não há mais dúvidas teóricas bloqueadoras. O dono decide se quer resolver os 4 pontos menores, ou avançar para código (treinos/transferências, A3).

## 2026-09-27 (cont. 22) — Vídeos da loja: 9, não 10; espera de 1h confirmada

- Dono confirma: são **9 vídeos** (não 10, corrige palpite antigo e leitura do prior art) e a espera ao esgotar é **1 hora**, confirmada. `THEORY.md` §12.2 atualizado. Fica por reconfirmar se a recompensa extra existe com 9 (era descrita para o antigo "10").
- **Próximo passo:** só falta a taxa de juro da poupança (segundo exemplo, para confirmar os 2%).

## 2026-09-27 (cont. 21) — Renovação dos vídeos de treino: 3 horas, não 1

- Captura de ecrã do dono: ao esgotar os 4 vídeos, o jogo diz para regressar **dentro de 3 horas**, não 1h como os vídeos da loja. `THEORY.md` §12.1 corrigido: o ciclo é **4 vídeos por 3 horas**, não "4 por hora" como estava escrito antes (título antigo era só uma forma de falar, agora com o valor real confirmado).
- **Próximo passo:** tempo de espera dos vídeos da loja (1h fixa ou desde o último visto), e taxa de juro da poupança (segundo exemplo).

## 2026-09-27 (cont. 20) — Mínimo de DEF confirmado; §7.2 e §7.8 fechados

- Dono vendeu 1 defesa (ficou com 7) e o jogo bloqueou listar 4 → **mínimo DEF = 4** confirmado.
- `THEORY.md` §7.2 fica com os 4 mínimos confirmados (ATT 3, MID 4, DEF 4, GK 2 = 13, exatamente o palpite inicial); o jogo confirma-se que **bloqueia listar** quando isso desceria abaixo do mínimo.
- §7.8 (motivo do "jogador fraco") também fechado: a análise de que MID/GK ficam sem margem para lesões sem o jogador fraco já não é hipótese, é consequência dos mínimos agora confirmados.
- **Próximo passo:** renovação dos vídeos de treino, tempo de espera dos vídeos da loja, taxa de juro.

## 2026-09-27 (cont. 19) — Patrocinadores corrigidos; médico/advogado esclarecidos

- **Correção:** patrocinadores (§9) são **dinheiro do clube**, não boss coins — más-entendido meu ("é coins" foi lido como "boss coins"; o dono corrigiu). `THEORY.md` já reflete a versão certa.
- **Médico/advogado (§10) resolvido:** usar **não custa nada**; ambos demoram **8 horas** de graça, e **boss coins só servem para saltar a espera** (skip), tal como os vídeos de treino. Valor exato do skip por confirmar se um dia interessar.
- **Próximo passo:** renovação dos vídeos de treino, tempo de espera dos vídeos da loja, taxa de juro, e o teste do mínimo de DEF.

## 2026-09-27 (cont. 18) — Estádio fechado: número exato de melhoramentos não é necessário

- Dono decide que o número exato de melhoramentos por nível (que varia por clube/liga, provavelmente pelo nível da liga) é **irrelevante para a automação** — a regra que importa é a ordem de prioridade (Treinos → Campo → Capacidade), já registada. `THEORY.md` §8 fechado.
- **Próximo passo:** moeda dos patrocinadores/médico/advogado, renovação de vídeos, taxa de juro, e o teste do mínimo de DEF.

## 2026-09-27 (cont. 17) — Estádio: 0→1 confirmado (1 melhoramento); número por nível varia por clube, sem fonte online fiável

- Dono deu 2 exemplos de 2→3: Clube A 11 melhoramentos, clube pequeno na outra liga 7 — logo **não é fixo**, varia por clube/liga.
- Pesquisa web (`DISCOVERY.md` §6): fórum oficial bloqueado pelo Anubis (mesmo problema já conhecido); outras fontes arriscavam confundir com o jogo diferente "Soccer Manager" (`soccermanager.com`, não é o nosso `onlinesoccermanager.com`) — não usámos esses números. Sem resposta fiável online.
- `THEORY.md` §8 atualizado: 0→1 = 1 melhoramento (confirmado); 1→2 sem exemplo; 2→3 varia (11 vs 7), padrão desconhecido.
- **Próximo passo:** se o dono conseguir mais exemplos (clube, liga, nível de transição, número de melhoramentos), tentamos ver o padrão. Continuar as outras dúvidas: moeda dos patrocinadores/médico/advogado, renovação de vídeos, taxa de juro, e o teste do mínimo de DEF.

## 2026-09-27 (cont. 16) — Multiplicador de preço máximo confirmado (~2,5×)

- Dono deu 3 exemplos novos (Jogador 18, Jogador 5, Jogador 2) que, com o Jogador 1 já registado, dão 4 pontos de dados entre 2,51× e 2,53× → **multiplicador = 2,5×** confirmado em `THEORY.md` §7.5. Sem código a alterar (ainda não há lógica de transferências implementada).
- **Próximo passo:** continuar a lista de dúvidas — melhoramentos por nível do estádio, moedas dos patrocinadores/médico/advogado, renovação de vídeos, taxa de juro; e o teste do mínimo de DEF quando o dono vender um defesa.

## 2026-09-27 (cont. 15) — Mínimos por posição: ATT, MID e GK confirmados no jogo

- Dono testou no jogo (§7.2 `THEORY.md`): **ATT = 3** (bloqueou listar 2 de 4) e **MID = 4** (só deixou listar 1 de 5) confirmados; **GK = 2** confirmado por ele com certeza (sem precisar de testar).
- **DEF fica pendente:** os dois plantéis testados tinham 8 defesas e só 4 slots de venda disponíveis, por isso o bloqueio em 4 pode ter sido o **limite de slots** (§7.3), não o mínimo da posição — teste inconclusivo. Palpite de 4 mantém-se, dono confiante. Plano: vender 1 defesa (ficar com 7) e tentar listar 4; se bloquear, confirma.
- Total dos mínimos confirmados até agora: ATT 3 + MID 4 + GK 2 = 9; falta confirmar DEF (palpite 4, total esperado 13).
- **Próximo passo:** dono faz o teste do DEF quando vender um defesa; continuar depois pela lista de dúvidas observáveis (multiplicador de preço máximo, níveis do estádio, moedas, vídeos, juro).

## 2026-09-27 (cont. 14) — Três dúvidas teóricas fechadas (formação e titular fraco)

- **`similar_margin` = 2 pontos** (§1 `THEORY.md`): dentro de ±2 ainda joga 433 (A ou B, "depende do plantel"); fora disso, 5-3-2. Código (`choose_formation`) e testes atualizados: `similar_margin` passa a ter valor por omissão 2 em vez de ser obrigatório.
- **"Fora de casa" não alarga a margem** — fica confirmado que o local do jogo é ignorado, e que isto é pouco relevante porque o dono faz as táticas manualmente (só a teoria fica registada, não se automatiza escolha de tática).
- **Titular "fraco"** (§7.7, para o aviso de "SALE" novos): conta como fraco quem for o mais baixo da posição **ou** quem estiver abaixo da média do 11 (os dois critérios valem, não é preciso cumprir os dois ao mesmo tempo).
- 44 testes a passar depois da alteração.
- Dono vai tentar verificar o ponto (4) da lista de dúvidas observáveis (mínimo de jogadores por posição) e outros pontos de teoria/observação continuam em aberto (multiplicador de preço máximo, níveis do estádio, moedas de patrocinadores/médico/advogado, renovação de vídeos, taxa de juro).
- **Próximo passo:** continuar a lista de dúvidas por partes, à medida que o dono for verificando no jogo.

## 2026-09-27 (cont. 13) — D-007 fechada; todas as decisões em aberto resolvidas

- **D-007 aceite:** sem licença (todos os direitos reservados) — visível mas não reutilizável por terceiros; coerente com D-002 (uso só pessoal). MIT foi considerada e descartada.
- `README.md` atualizado: estado corrigido (já há código de lógica pura, não é "sem código ainda") e disclaimer reforçado com a nota de licença/risco.
- Com isto, `DECISIONS.md` fica sem itens "Em aberto" exceto D-008, que não é bem uma decisão pendente — é a regra fixa de que git/GitHub são só do dono.
- **Próximo passo:** não há mais decisões de alcance/risco a bloquear trabalho. Pode avançar-se para código de A3 (treinos, transferências) — o dono decide se quer começar por aí, ou por outra coisa.

## 2026-09-27 (cont. 12) — D-012 e D-006 fechadas

- Discussão sobre risco dos anúncios: corrigida a leitura do precedente de junho — é sobre **exceder** limites via bug, não sobre automatizar **dentro** dos limites (isso fica desconhecido, não confirmado nem afastado). `DISCOVERY.md` §5 e `RISKS_AND_COMPLIANCE.md` corrigidos.
- Dono propôs mitigação: respeitar sempre os limites do jogo, capar a fração de janelas apanhadas (~60-70%, por afinar) com timings aleatórios, correr só nas horas em que as máquinas estão ligadas (sem horário fixo, varia dia a dia).
- **D-012 aceite:** anúncios (A4) sem servidor dedicado — corre em PC pessoal, MacBook e PC da empresa (dono é o IT da empresa, sem risco de política de TI de terceiros).
- **D-006 aceite:** CLI fina + biblioteca, arranque automático por máquina (Task Scheduler/LaunchAgent), sem horário fixo.
- Descartada a ideia de usar um iPhone antigo (6s/8) como "servidor": iOS não corre automação em background sem jailbreak, e mesmo com jailbreak não é viável correr um browser real para ver o anúncio sem forjar a confirmação.
- Sem código novo.
- **Próximo passo:** só falta **D-007** (licença do repo) para fechar todas as decisões em aberto. Depois disso, pode começar-se código (treinos/transferências, A3, não depende de mais nada).

## 2026-09-27 (cont. 11) — D-004 e D-002 fechadas

- Pesquisa web nova em `DISCOVERY.md` §5: OSM tem "device ban"; precedente de junho 2026 em que contas foram banidas por ver vídeos ilimitados (bug do jogo, não bot) e a sanção foi mantida — sinal de que a deteção olha para o padrão/volume, não só para a intenção. Refletido também em `RISKS_AND_COMPLIANCE.md`.
- **D-004 aceite:** dono aceita risco A3 já, A4 quando D-012 estiver resolvida; testes começam em conta secundária "a seu tempo"; registado que a conta secundária não isola 100% (device ban).
- **D-002 aceite:** alcance = A3 (treinos, transferências automáticos). A4 (anúncios) fica preso a D-012, que passou a depender só de **infraestrutura** (onde correr algo 24/7 sem gastar dinheiro — servidor vs. Raspberry Pi), não de risco.
- Sem código novo.
- **Próximo passo:** decidir D-006 (interface) e D-007 (licença), agora destravadas; D-012 fica para quando o dono resolver a questão de infraestrutura.

## 2026-09-27 (cont. 10) — Teoria fechada, incluindo vídeos e finanças

- Acrescentados em `THEORY.md`: análise do adversário e objetivo de época (§11); vídeos de treino, loja e finanças (§12); poupança e juros (§13, ≈2% por dia de jogo).
- Correções relevantes: o critério de "mais forte/mais fraco" é a **média do plantel 0–100 mostrada antes do jogo** (não o preço); a duração dos treinos **varia** (8 h normal, 2 h em eventos) e nunca deve ser fixada no código.
- Dono confirma **"é tudo"**. A recolha de teoria está terminada.
- **Por confirmar** (só observando o jogo): mínimos por posição; multiplicador do preço máximo; desconto do "SALE"; taxa do juro (só 1 exemplo); horas de renovação do mercado; melhoramentos por nível do estádio; se os "4 vídeos/hora" e os "10 vídeos" se renovam de hora a hora.
- **Próximo passo:** decidir o que automatizar, por que ordem (D-002) e a postura de risco (D-004). Sem código novo.

## 2026-09-27 (cont. 9) — Teoria do jogo completa (segundo o dono)

- Registados: guarda-redes/moedas/jogador fraco (§7.8; palpite do dono: evitar dinheiro parado), **estádio** (§8), **patrocinadores** (§9), **médico e advogado** (§10), Legend e Inform players (§7.6). Glossário atualizado.
- O dono diz que **"passámos tudo do jogo"**.
- **Próximo passo:** decidir o que automatizar e por que ordem (D-002), e a postura de risco (D-004), antes de qualquer contacto com o jogo. Sem código novo.

## 2026-09-27 (cont. 8) — Transferências e plantel: fechado

- Dono explicou a estratégia de transferências e gestão de plantel; registada em `THEORY.md` §7 (7.1–7.7, com resumo no topo) e **fechada por ele**.
- Usadas 4 capturas de ecrã (plantel em 3 imagens, lista de transferências numa): confirmam colunas, ícones (em treino, na lista de transferências, cartão amarelo), etiqueta "SALE" e como distinguir vendedores utilizadores.
- Pedidos de automação, não urgentes: **treinos** (recolher e recolocar), **coins via anúncios** (para os amigáveis, ver §6), **notificação de "SALE" novos** (§7.7). Ver `PROJECT_BRIEF.md`.
- **Por confirmar** (todos marcados [?] em `THEORY.md`): mínimo de jogadores por posição; número de slots atual (4 ou 6); multiplicador do preço máximo (~2,5×?); horas de renovação do mercado; desconto do "SALE".
- Sem código novo. **Próximo passo:** o dono diz se ainda tem teoria para juntar (ponto (c) dele) ou se passamos ao que automatizar (D-002, D-004).

## 2026-09-27 (cont. 7) — Checklist de preparação do jogo registada

- *(Acrescento)* Amigáveis sobem stats de jogadores; o dono faz ≥1/dia, às vezes mais (4 boss coins cada). É o motivo principal para querer farmar coins com automação.

- Dono descreveu a checklist pré-jogo (10 pontos: 8 que faz quase sempre, incluindo o amigável que faz SEMPRE; 2 que custam muitas coins e usa por vezes — treino secreto e estágio). Registada em `THEORY.md` §6.
- Treinos automáticos confirmados como automação desejada, não urgente (`PROJECT_BRIEF.md`). Ligação notada: 4 sessões concluídas **no dia do jogo**.
- Sem código novo. Dono ainda pode acrescentar mais teoria/metodologia.

## 2026-09-27 (cont. 6) — Correção de rumo

- O dono disse que a parte tática/especialistas **gere ele sozinho**; só a explicou para ficar registada e para o Claude perceber a sua forma de jogar. O Claude tinha ido construir código e testes sem isso ser pedido → regra 10 no `CLAUDE.md` (registar antes de construir).
- Respostas registadas em `THEORY.md`: árbitro/desarme é contextual (véspera de jogo duro → não arriscar vermelhos; jogo difícil → talvez Agressivo); treino: nunca listados para venda, 30+ treina outros; treinador universal fora de âmbito.
- **Git/GitHub é do dono** (regra 9, D-008). Retirada a proposta de `git init`.
- O dono **ainda tem mais teoria e metodologia para juntar**. Aguardar.
- O código de `src/` e `tests/` fica (é pequeno e o dono pode apagá-lo), mas **não é para expandir** sem o dono pedir. Ponto pendente sobre "rating parecido" (`similar_margin`) só interessa se um dia se automatizar a escolha de formação.
- **Próximo passo:** o dono continua a explicar a teoria/metodologia; ao terminar, decide-se o que automatizar (coins/treinos/transferências) e D-004.

## 2026-09-27 (cont. 5) — Primeiro código: lógica pura

- Dono respondeu aos [?] de `THEORY.md` e à política de treino; linguagem = Python (D-001).
- Criado o projeto Python (`pyproject.toml`, `src/osmbot/`, `tests/`, `.venv/` ignorado): `models.py`, `theory/specialists.py`, `theory/tactics.py`, `training/policy.py`. **44 testes a passar** (dados sintéticos; nada tocou no jogo).
- `THEORY.md` reescrito com as respostas; ficam poucos [?] (ver abaixo) e várias suposições marcadas [S].
- **Por confirmar (dono):** `similar_margin` (o que é rating "parecido"); Rigoroso → Agressivo?; limite exato de "30+"; uso do treinador universal; listados para venda excluídos do treino?
- **Próximo passo:** ou (a) `git init` + primeiro commit, ou (b) cliente de API offline (parsing de respostas com fixtures) e agendamento inteligente dos treinos, ou (c) decidir D-004 para começar a verificar endpoints. Aguardar escolha do dono.

## 2026-09-27 (cont. 4) — Teoria tática registada

- D-011 aceite (construir de raiz); D-013 registada (contacto com o jogo adiado).
- Dono explicou a teoria: formações vs força do adversário, sliders, desarme por árbitro, especialistas (capitão, penáltis, livres, cantos). Registada em `docs/THEORY.md`, com pontos **[?]** por confirmar.
- Ainda por responder: linguagem (recomendado Python) e política de seleção de treinos.
- **Próximo passo:** dono responde aos [?] de `THEORY.md`; depois estrutura do projeto + `specialists` (função pura mais simples e sem ambiguidade) + gestor de treinos.

## 2026-09-27 (cont. 3) — Análise do `osm-ad-bot`

- Lido o código completo (clone em scratchpad, fora do projeto). Resultado em `docs/PRIOR_ART.md`.
- Achados-chave: API interna mapeada (host `web-api.onlinesoccermanager.com`, `/api/v1/leagues/{L}/teams/{T}/...`); treinos são **HTTP puro**; anúncios exigem browser e o repo **forja callbacks de recompensa**; sem endpoints de compra/venda; sem LICENSE.
- Recomendação: construir de raiz (D-011), começar pelos treinos, depois transferências; anúncios em separado (D-012).
- **Próximo passo:** dono decide D-004/D-011/D-012. Depois, verificação read-only dos endpoints com OK explícito.

## 2026-09-27 (cont. 2) — Pivot do propósito

- Dono esclarece: teoria tática já é dele, nada a testar, pouco a automatizar. Quer automatizar **coins via vídeos, encurtar treinos, cortar vídeos promocionais e possivelmente transferências** (D-010; D-009 substituída).
- Alcance passa a A3/A4. Prior art relevante: `nsozturk/osm-ad-bot` faz exatamente ads + treinos (ver `DISCOVERY.md`).
- **Bloqueio:** D-004 (postura de risco / que conta) tem de ser decidida antes de qualquer contacto com o jogo.
- **Próximo passo possível sem tocar no jogo:** ler o código-fonte público de `nsozturk/osm-ad-bot` para perceber como ads/treinos funcionam (auth, endpoints reportados, rate limits).

## 2026-09-27 (cont.) — Propósito definido (substituído acima)

- Dono afirma ter uma teoria de jogo com resultados comprovados; o bot deve codificá-la (D-009).
- Domínios indicados: táticas vs mais forte, táticas vs mais fraca, política de transferências, capitães/roles, etc.
- **Próximo passo:** extrair a teoria em formato estruturado (regras, inputs, outputs) e recolher os resultados que a sustentam. Só depois fechar alcance (D-002) e risco (D-004).

## 2026-09-27 — Sessão 1: arranque e descoberta inicial

**Feito**
- Esclarecido que OSM = Online Soccer Manager (D-000).
- Pesquisa web sobre viabilidade: sem API pública oficial encontrada; 4 repos de prior art (todos automação de browser; foco em farm de moedas); ToS proíbem bots e scraping sem autorização escrita.
- Criada a estrutura: `CLAUDE.md`, `docs/*`, `.gitignore`, `README.md`.

**Por fazer / bloqueios**
- Tópico do fórum "Osm API" e artigo de suporte "What's considered cheating" não puderam ser lidos automaticamente (Anubis / 403).
- Nada foi testado contra o jogo real.

**Próximo passo**
- Utilizador responde às perguntas de `OPTIONS.md` §E e decide D-004 (postura de risco) e D-002 (alcance).
- Depois: decidir se se faz observação de rede na web app (só com OK explícito), e só então stack.
