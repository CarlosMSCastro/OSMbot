# Teoria de jogo do dono

*Fonte: o dono, 2026-09-27 (2 rondas). Tratada como verdade do projeto; **não validada por nós** (o dono afirma resultados comprovados).*
*Regra: este ficheiro só muda quando o dono o disser. Não "otimizar" nem corrigir a teoria.*
*Implementação: `src/osmbot/theory/` e `src/osmbot/training/`. Pontos ainda por confirmar: **[?]**. Suposições nossas: **[S]**.*

## 1. Escolha de formação

**Regra atual (dono, 2026-10-13, depois da análise de 272 jogos das 2 ligas; substitui a de 2026-09-27):**

| Formação | Meio-campo | Quando |
|---|---|---|
| **4-3-3 A** | Leva **MCO** (médio centro ofensivo) | **Sempre**, exceto contra um adversário claramente mais forte. Com os melhores planteis da liga, é quase sempre |
| **5 defesas** (5-3-2, 5-2-3, 5-4-1) | O dono escolhe a que serve aos jogadores | Adversário **mais forte**, por qualquer margem (dono, 2026-10-14; antes: mais de 5 %) |
| 4-3-3 B | Leva **MCD** (médio centro defensivo) | Já não é a regra para jogos parecidos. O dono pode experimentá-lo (por ex. fora de casa); o registo dos jogos diz depois se compensa |

**Porquê (os números, `WORKLOG.md` 2026-10-13):** pontos por jogo com a mesma diferença de força e o mesmo local: o 4-3-3 A foi o melhor em casa e fora, sendo mais forte (2,78 casa / 2,25 fora) ou parecido (2,41 / 1,33). O 4-3-3 B fora sendo mais forte deu 2,75, mas em 12 jogos quase todos de um clube do dono muito mais forte: não chega para concluir. O 5-3-2 sendo mais fraco: 3 vitórias em 3 jogos, só jogos do dono (os outros clubes quase não o usam). A força pesa muito mais do que a formação; e o banco também (um suplente fraco a entrar por lesão custou um empate).

Implementado em `choose_formation(my_rating, opp_rating, *, stronger_pct=0)`: adversário mais forte → 5 defesas; igual ou mais fraco → 4-3-3 A. O aviso do pré-jogo aceita qualquer formação de 5 defesas.

**Sem extremos em forma → 4-4-2 B (dono, 2026-10-14):** o 4-3-3 A precisa de **1 EE e 1 ED** (posição específica) em forma: condição ≥ 80 % (§16), sem lesão nem castigo, no plantel todo (titulares ou banco). Se faltar um dos lados, o **4-4-2 B** (2 PL, sem extremos) conta como certo em vez do 4-3-3 A; outra formação continua a dar aviso. Na janela o passo "Onze" fica **verde** com uma nota ao passar o rato ("4-4-2 B aceite: sem ED em forma (…)"). Só quando a regra da força diz 4-3-3 A; contra um mais forte continuam as 5 defesas.

**"Mais forte" conta os bónus do jogo e a casa (dono, 2026-10-14; `match_strength`):** força = rating da equipa × (1 + bónus %) × 1,05 para quem joga em casa.
- **Bónus:** os de cada lado somam-se, como o jogo os mostra no círculo ao lado do emblema ("+3 %"). Do dono: sequência de logins (`matchBoost`) + estágio (`CampBoostPercentage`, 25 %) e treino secreto (`SecretBoostPercentage`, 2 %) quando marcados. Do adversário: só os logins, depois da análise e só com treinador humano (como o site); o estágio e o treino secreto dele não se veem.
- **Casa:** +5 % para quem joga em casa; nada em campo neutro.
- **[S] Os 5 % de casa** são a média medida nos 272 jogos (2026-10-13), com o campo de cada estádio lá dentro sem o separar. O campo dá "+X % home advantage" por nível (0/2/4/6 %; FC Van nível 2 = +4 %), mas o estádio dos outros não se lê (403). **Nota para mais tarde:** voltar a medir a vantagem de casa pelos registos dos jogos (`logs/*/jogos`), e ver se bate com os 5 % ou se depende do nível do campo (pelo menos nos jogos do dono, cujo campo se conhece).

- *Histórico:* de 2026-10-13 a 2026-10-14 a margem era **mais de 5 %** (medida na força do jogo dos 272 jogos) e só o 5-3-2 contava. O dono mudou para "só mais forte" porque varia entre as táticas de 5 defesas consoante os jogadores (D-049).
- *Histórico:* até 2026-10-13 a regra era: mais forte → 4-3-3 A; parecido (±2 pontos de rating) ou fora em jogos equilibrados → 4-3-3 B; adversário mais forte por mais de 2 → 5-3-2.
- **Casa e fora:** o local do jogo continua a não entrar na regra. Os dados mostram que jogar em casa vale ~5 % de força (proposta ao dono, por decidir: tratar o adversário como 5 % mais forte fora de casa). **Pouco relevante na prática:** o dono faz as táticas manualmente (não é para automatizar, ver §6 do histórico/cont. 6).
- **Rating da equipa (resolvido):** vem da **média do plantel de 0 a 100 em rating** que o jogo mostra **antes de cada jogo** (não é o preço). Ver §11. Na API: a média do `statAtt`/`statOvr`/`statDef` (o principal de cada posição) dos melhores por posição na formação (`DISCOVERY.md`, 2026-10-13; é a mesma conta do código do site, `getAverageLineupStrength`).

**Confronto direto (dono, 2026-10-08):** um jogo contra um clube que está **a 1 ou 2 lugares** do do dono na classificação, acima ou abaixo. São os jogos que o dono gosta de ver ele próprio nas últimas horas (§6). O quadro marca-os com um símbolo de perigo (D-026).

## 2. Instruções por formação

| | **4-3-3** (A e B) | **5-3-2** |
|---|---|---|
| Fora de jogo (offside trap) | Não | Não |
| Marcação à zona | **Sim** *(corrigido pelo dono, 2026-10-13; antes estava "Não")* | Sim |
| Estilo de jogo | Jogo de passe **ou** pelas alas (ver abaixo) | Contra-ataque |
| Slider Pressão | 60–80, perto de **75** | 20–40, perto de **30** |
| Slider Estilo | 60–80, perto de **75** | Defensivo: 20–40 **[S: 30]** |
| Slider Temporização | 60–80, perto de **75** | 60–80, perto de **75** |
| Avançados | Apoiar o meio-campo | Só atacar |
| Médios | Manter posições | Ajudar a defesa |
| Defesa | Defender atrás | Defender atrás |

**Regra dos sliders:** o jogo pede valores fixos; o dono **nunca sai da banda** que define o estilo, mas pode "brincar" dentro dela. O código valida que o valor fica na banda (`Slider`).

**Bandas dos sliders (as três, 0–100):**

| Banda | Pressão | Estilo | Temporização |
|---|---|---|---|
| 0–20 | Não pressionar | Super defensivo | Jogar atrás |
| 20–40 | Equilibrado | Defensivo | Construir de trás para a frente |
| 40–60 | Equilibrado | Neutro | Fazer posse |
| 60–80 | Chegar perto do adversário | Ofensivo | Passes rápidos |
| 80+ | Pressão alta | Tudo ao ataque | Futebol ao primeiro toque |

**Estilo no 4-3-3:** "meio indiferente"; se os **extremos forem muito melhores que o PL** (ponta de lança), joga pelas alas, senão jogo de passe. Implementado como parâmetro `prefer_wings` decidido por quem chama (o código ainda não sabe quem são os extremos).

**[S]** Nas fronteiras entre bandas (20, 40, 60, 80) o dono não especificou a que banda pertence o valor. Os valores por omissão ficam afastados das fronteiras, por isso não afeta.

## 3. Desarme (tackling) — ambas as formações

Sempre o máximo tolerável pelo árbitro. A severidade do árbitro aparece **antes de cada jogo**.

Árbitro: *Muito Rigoroso · Rigoroso · Normal · Brando · Muito Brando*.
Desarme: *Cuidadoso · Normal · Agressivo · Extremo*.

| Árbitro | Desarme |
|---|---|
| Muito Rigoroso | Normal |
| Rigoroso, Normal, Brando | Agressivo *(regra base; ver "Contexto" abaixo)* |
| Muito Brando | Extremo |

- **Aposta do dono:** com árbitro **Brando**, às vezes arrisca **Extremo** quando **precisa de ganhar** e os plantéis são parecidos. A agressividade parece ajudar a equipa a jogar melhor, mas é um risco. Implementado como `risk_extreme=True`, decidido por quem chama.
- **Contexto (2.ª ronda):** a tabela acima é só a regra base. Num **jogo tranquilo na véspera de um jogo duro**, o dono **não arrisca levar vermelhos** (fica abaixo do máximo). Num **jogo difícil**, talvez use Agressivo. Ou seja, a escolha real depende do jogo seguinte e da dificuldade, não só do árbitro. `choose_tackling` só implementa a regra base; o dono gere isto sozinho.
- *Cuidadoso* nunca é usado.
- **No jogo (verificado no código do site, 2026-10-13):** o desarme é o campo `style` da tática (0 Cuidadoso, 1 Normal, 2 Agressivo, 3 Extremo); o árbitro do próximo jogo já vem no calendário (`refereeId`) com o seu `strictness` (1 muito rigoroso … 5 muito brando, `DISCOVERY.md`).
- **O que o aviso aceita como certo** (dono, 2026-10-13, §21): muito rigoroso → Normal; rigoroso e normal → Agressivo; brando e muito brando → Agressivo **ou** Extremo (muito brando: dono, 2026-10-14, "pode ser agressivo, não precisa ser extremo"; antes só Extremo).

## 4. Especialistas (só entre os **titulares**)

| Papel | Regra |
|---|---|
| **Capitão** | O mais **velho**, independentemente do rating. Empate de idade → maior rating |
| **Penáltis** | **Avançado** com mais ataque |
| **Livres** | Qualquer titular com mais ataque |
| **Cantos** | **Médio** com mais ataque |

- "Ataque" = estatística de ataque do jogador (`statAtt` no API; confirmado: é o número de ataque do ecrã do jogo, `DISCOVERY.md`).
- "Rating" (no capitão e nos desempates) = *stat principal da posição*: avançado→ataque, médio→overall, defesa e guarda-redes→defesa. **Confirmado** (2026-10-14): é o `statMain` que o próprio jogo usa na força da equipa, e a força calculada assim bate com a do jogo em 3 clubes.
- **Ataque igual (penáltis, livres, cantos; dono, 2026-10-14):** ganha quem tiver **o resto das stats melhor** (overall + defesa). Ex.: Marmoush e Trossard com 111 de ataque; Trossard 73 + 36 contra 65 + 19 → Trossard.
- **[S]** Empates que ainda sobram resolvem-se por maior rating e depois menor id de jogador, para o resultado ser sempre o mesmo.
- Sem titular elegível (ex.: sem avançado) → o código devolve `None` e o chamador decide.
- **O mesmo jogador pode ter mais de um papel** (dono, 2026-10-12).
- **Automático (dono, 2026-10-12, D-042):** nas **últimas 4 h antes de cada jogo**, em cada passagem, o bot põe certos só os papéis que estão fora da regra (segue as mudanças do onze). Um lesionado ou suspenso sai do onze e por isso dos especialistas (dono). Na checklist do quadro, "Especialistas" fica **amarelo** quando não seguem a regra, mesmo que o jogo os dê como feitos.

## 5. Política de treino

Como a política de transferências **roda o plantel inteiro** várias vezes, o dono treina quase sempre o **melhor jogador de cada posição**, exceto se tiver **30+ anos**.

Implementado em `plan_training` / `pick_trainee`:
- Melhor = maior *rating* da posição (ver §4, confirmado). Treinadores 1–4 são por posição (ATT, MID, DEF, GK).
- Exclui (confirmado pelo dono): lesionados, já em treino, **quem está na lista de transferências (nunca treinar)**, e **idade ≥ 30**: nesse caso não treina o melhor, treina outros.
- Se o melhor tem 30+, usa-se o melhor dos restantes (confirmado).
- **Exceção (dono, 2026-10-04): guarda-redes treinam sempre o melhor, independentemente da idade.** O limite de 30+ aplica-se só a jogadores de campo.
- **Exceção (dono, 2026-10-16): num evento que dá mais progressão aos jogadores velhos** (Golden Oldies: "Higher training progression, when claiming results, for old players"), os de 30+ também são **considerados**, com a mesma regra (rotação, depois a previsão, depois o melhor), enquanto o evento durar pelas datas do calendário, **em todos os eventos futuros com esse efeito** (D-060). **[H]** Não se sabe se a previsão do jogo (`trainingforecasts`) já conta o bónus do evento, nem a partir de que idade o jogo chama "velho"; os registos de cada treino (idade, previsão e ganho) vão dizê-lo.
- **[S]** Jogadores com forecast ≤ 0 (previsão do servidor: nada a ganhar) também são excluídos, quando essa informação existe.
- **Rotação entre titulares (dono, 2026-10-12):** treinar o mesmo jogador outra vez na mesma jornada rende menos e a quebra só desaparece com o jogo (fórum, `DISCOVERY.md` §6b/§6c; nos logs, o Haaland deu +38 na 1.ª sessão depois de um jogo e +11–13 nas seguintes). Por isso cada treino vai para o **titular** (onze, `lineup` 1–11) da posição com **menos sessões nesta jornada**; entre iguais, o melhor. **Desempate (dono, 2026-10-12):** entre iguais, o que tem **mais expectativa de melhorar** (a previsão do jogo, `trainingforecasts`); só depois o melhor. Nos logs, os jogadores de 115 ganham 2–3× menos por treino do que os de 104–110, e a previsão do jogo diz o mesmo (Donnarumma 115 → 13, D. Henderson 104 → 29). A previsão não conta as repetições na jornada: por isso continua primeiro a rotação. Quando todos já treinaram, volta ao melhor e assim por diante. Valem as mesmas exclusões (lesionados, listados, 30+ exceto GR). **[S]** Sem titular elegível na posição (p. ex. todos 30+), a mesma regra no resto do plantel. **[S]** A jornada é o `weekNr` da liga (a última jogada): as sessões contam-se pelas que o bot **viu** nesse PC (as que pôs e as que encontrou a decorrer ou por recolher, as do dono e as do outro PC incluídas; desde 2026-10-12) e pelas que estão a decorrer. Perdem-se só as que o outro PC pôs e recolheu antes de desligar (o jogo não guarda histórico, `DISCOVERY.md` §3). O bot regista em cada treino a previsão do jogo e o progresso ao recolher, para se medir se a rotação compensa.
- **Treinador universal (5):** só com os itens que vão expirar (§20, D-039). Comprá-lo com boss coins continua fora de âmbito.
- **Início de um evento de treinos (dono, 2026-10-16): acabar com boss coins** os treinos normais (8 h) ainda a correr, em vez de deixar o lugar parado horas ou de não pôr treinos na véspera. Um treino posto antes do evento não encurta (`DISCOVERY.md` §3). Preço do jogo (`bosscoinproducts`, `TrainingBoostCost`): **2 boss coins por hora que falta, arredondada para cima** (3h50 → 8; 20 min → 2; 8 h → 16). Todos os treinos postos antes do evento (os que o bot viu a correr antes de o evento começar, ou com mais tempo por fazer do que um treino do evento), seja qual for o tempo que falte (D-059). **[S]** Só se houver boss coins para o preço; o treinador universal também. O bot procura o evento de 10 em 10 min das 05:30 às 07:00 nos dias de evento de treinos do calendário.

## 6. Preparação do jogo (checklist)

*Fonte: o dono, 2026-09-27. O jogo tem uma checklist de preparação antes de cada jogo; o dono costuma ter **quase todos os pontos** feitos. Descrição nas palavras dele.*

**Pontos que faz quase sempre:**

| Ponto | Regra / nota do dono |
|---|---|
| **Concluir 4 sessões de treino** | Cada jogador em treino conta como 1 sessão (4 jogadores a treinar = 4 sessões). **Tem de ser feito no dia do jogo.** |
| **Fazer um 11 inicial** | Ter 11 no plantel. |
| **Selecionar os especialistas** | O jogo **não** verifica se são os melhores segundo a regra do dono (§4). Com 4 quaisquer escolhidos, o ponto fica validado. |
| **Analisar o adversário** | **Grátis**, envia-se o analista, **sem limite**. Contra adversários reais e ligas difíceis, o dono contorna: **na véspera põe a tática errada** para o adversário a analisar, e **depois troca** pela certa. |
| **Alinhar jogadores em forma** | Jogadores com pouca energia convém trocar; se o indicador **sai do verde** convém trocar. Como o dono roda os jogadores com as transferências, **normalmente não acontece**. |
| **Posicionar os jogadores** | Jogadores corretamente posicionados no 11 inicial. |
| **Preencher o banco de suplentes** | O jogo dá o ponto por cumprido **mesmo com o banco mal preenchido** (ex.: GK no lugar de PL). O dono tenta sempre pôr corretamente, mas nem sempre é possível. |
| **Fazer 1 jogo amigável** | Custa **4 boss coins**. O dono faz **SEMPRE**, e às vezes **mais de 1 por dia**. Funciona um pouco como treino: **sobe as stats de alguns jogadores**. O dono acredita que há jogadores que fazem ~10 por dia para subir o rating (ele não vai a esse extremo). É por isto que precisa de **farmar coins com automação**. |

**Pontos que só faz por vezes (custam muitas coins):**

| Ponto | Custo | Regras e notas do dono |
|---|---|---|
| **Treino secreto** | 3 coins | **6 por época**. Esconde o 11 e as táticas do adversário. Dá **+2%** de melhoria à equipa. Usa alguns por época, normalmente **junto com um estágio**. |
| **Estágio** | Progressivo: **10, 20, 50, 100, 200, 500** coins | **Limite de 6 por época.** Sem treino secreto, o adversário é alertado. Caríssimo, mas usa alguns por época. |

*Notas nossas (não são regras do dono):*
- A exigência de **4 sessões de treino concluídas no dia do jogo** liga-se diretamente à automação de treinos (§5): a recolha e a recolocação automáticas têm de garantir que as 4 sessões terminam nesse dia. O prior art viu treinos de 2 h; o dono diz que as sessões duram 8 h (§12.1), e que se podem encurtar com vídeos.
- **Amigáveis em quantidade (dono, 2026-10-08; posta de lado em 2026-10-09):** o dono fez **10 amigáveis (40 boss coins)** e o valor do plantel subiu só **~1,5–2 M**; não compensa. Fica o registo:
  - Só se pode jogar **1 amigável contra cada clube da liga por jornada**; escolhe-se o adversário. Na prática ~**25 por equipa** por jornada (depende do número de clubes da liga).
  - **Não cansam nem lesionam** jogadores.
  - Limite diário do jogo: o dono acha que **não há** (por verificar).
  - Por decidir: quantos por dia, que clube primeiro, reserva mínima de boss coins. O pedido que inicia um amigável **nunca foi observado** (regra 7; escrita nova, pede OK pela regra 5).
  - Conta: 2 equipas × ~25 × 4 coins = ~200 boss coins por jornada; o bot ganha ~140 por dia com 18 h a correr (8 vídeos/h vistos no `bot.log`).
- **Amigável e análise do adversário à última hora (dono, 2026-10-08; pedido de automação, ainda não construído):**
  - Quando faltarem **4 horas para o próximo jogo** de uma equipa, se ainda não houver **amigável feito** para esse jogo, o bot faz **1**. O mesmo para a **análise do adversário** (envia o analista; é grátis).
  - **Não fazer mais cedo:** nos confrontos diretos o dono gosta de verificar ele próprio nas últimas horas; as 4 h dão-lhe esse tempo, e o bot só cobre o que ele não fez.
  - **Adversário do amigável (dono, 2026-10-08):** é **indiferente**. O jogo sugere 1 (há 1 lugar recomendado), mas pode escolher-se qualquer clube. O que importa é haver **pelo menos 1 amigável antes de cada jogo**. Não tem nada a ver com o próximo adversário, nem com liga ou taça: serve **qualquer clube** da liga (o jogo só deixa 1 amigável contra cada clube por jornada).
  - **Só a análise** usa o próximo adversário: o analista vai ao clube do próximo jogo oficial (foi o que o site fez quando o dono analisou à mão).
  - **"Feito" (dono, 2026-10-08):** pelo menos 1 amigável **desde o último jogo dessa equipa**. Se o dono já fez um para este jogo, o bot não faz outro.
  - **Todas as equipas (dono, 2026-10-08):** vale para todas as equipas da conta, em qualquer liga, de 1 a 4 (há 4 lugares). Regra geral do projeto, não só desta: nada é fixo a clubes ou ligas.
  - **Para mais tarde (dono, 2026-10-08):** se isto funcionar bem, talvez **5 amigáveis por dia**. Não construir agora.
  - **4 amigáveis por dia (dono, 2026-10-11):** o bot passa a fazer **4 amigáveis** por equipa antes de cada jogo (em vez de 1), e a checklist da janela mostra **"Amigáveis (1)", "(2)"… até "(4)"**; o ponto fica verde **logo com o 1.º** (como no jogo), mas o bot faz os 4 na mesma. Substitui o "1 amigável" acima.
    - **[S]** Contam os amigáveis **desde o último jogo da equipa** (os do dono incluídos); o bot faz os que faltarem até 4, na mesma janela das **4 h antes do jogo**, contra clubes diferentes, ao acaso (o jogo só deixa 1 por clube por jornada), com uma pausa de alguns segundos entre eles.
    - **[S]** Sem boss coins para todos: faz os que der (4 cada) e avisa.
  - **Amigáveis distribuídos pelo dia (dono, 2026-10-12):** os 4 amigáveis **podem ser distribuídos pelo dia**; já não esperam pela janela das 4 h. **[S]** O 1.º faz-se a partir de **16 h** antes do jogo, o 2.º a partir de **12 h**, o 3.º de **8 h** e o 4.º de **4 h**; se o PC esteve desligado, faz logo os que estão em atraso. Contam os do dono. Substitui a janela das 4 h só para os amigáveis.
  - **8 amigáveis no Intense Friendlies (dono, 2026-10-12):** enquanto decorre um evento **Intense Friendlies** (calendário do fórum, D-038; "Extra Training Progression with every Friendly"), a jornada leva **8 amigáveis** em vez de 4, **com registo** de cada um (progresso dos jogadores antes e depois, e o evento) "para ver se compensa". O dono: "é indiferente quando os amigáveis são feitos, desde que antes do jogo"; a jornada acaba no jogo. **[S]** Horas: o k-ésimo a partir de 16, 14, 12, 10, 8, 6, 4 e 2 h antes do jogo; um que só caberia depois do fim do evento faz-se até 1 h antes de o evento acabar (o bónus só conta durante o evento). **[S]** Reconhece-se o evento pelo nome ("Intense Friendlies"); os outros eventos com amigáveis (Training Camp Mania, Extreme Training) ficam com 4.
  - **Pré-época (dono, 2026-10-15):** na pré-época as equipas têm o **mesmo tratamento**: os **4 amigáveis fazem-se todos os dias**, não só antes do 1.º jogo do campeonato. **[S]** O "dia" acaba à hora do 1.º jogo do campeonato (1 jogo por dia, §19), e as horas dos amigáveis contam-se a partir daí (16, 12, 8 e 4 h antes). Contam por jornada (`weekNr`), que na pré-época muda todos os dias (−3, −2, −1, 0). **[S]** A jornada muda a essa mesma hora (não verificado). O analista continua a ir só ao jogo a sério.
  - **Transfer Madness (dono, 2026-10-12):** para já nada; o dono vê o evento na janela e decide.
  - **Analista (dono, 2026-10-12):** **enviar** continua só nas últimas **4 h** antes do jogo. **Levantar:** assim que estiver pronto, **a qualquer hora**, recolhe-se.
  - **Observado e autorizado (2026-10-08, D-025):** pedidos em `DISCOVERY.md` §3. Construído em `prematch/policy.py` e `game/prematch.py`:
    - "Feito" é o que diz a checklist do jogo (`matchpreparation`). A análise só conta lá depois da hora do analista; por isso um analista já enviado nesta jornada também conta (o dono contava que passasse a 1/1 sozinha; **não passa**: é preciso **levantar o analista** quando acaba, `DISCOVERY.md` §3, observado a 2026-10-09).
    - **[S]** O adversário do amigável é **ao acaso** entre os clubes da liga ainda sem amigável nesta jornada (o dono diz que é indiferente; ao acaso evita um padrão de máquina). Se o jogo recusar, tenta outro (até 3).
    - **[S]** Sem boss coins para o amigável (4): só avisa. Se não for claro quem é o próximo adversário: a análise fica por fazer, com aviso. **O dono (2026-10-08): uma jornada nunca tem 2 jogos.** No calendário de uma equipa, a jornada 14 tinha um jogo de taça (`matchType` 1) no lugar do da liga. Por isso esta proteção não deve disparar; fica só para dados inesperados.
- Treino secreto e estágio são decisões de gasto do dono (coins, limites por época); não parecem candidatos a automatizar. O **amigável** é diferente: custa só 4 boss coins e o dono **faz sempre** — se um dia se automatizar algo da checklist, é candidato (mas só se o dono o pedir).
- Pontos onde o jogo **não valida a qualidade** (especialistas, banco) são justamente onde a regra do dono acrescenta valor: só ele sabe se estão certos.

## 7. Transferências e gestão de plantel *(fechada pelo dono em 2026-09-27)*

**Resumo (síntese nossa; o detalhe e as palavras do dono estão em 7.1–7.7):**
1. Plantel de 18: 11 titulares + banco fixo de 7 (2 ATT, 2 MID, 2 DEF, 1 GK), mais **1 jogador fraco por posição** que permite rodar os suplentes.
2. **Vende** os suplentes (sem ordem), pedindo o **preço máximo**; se o máximo passar de **100 M€**, pede **75% do máximo**. Os bots compram sempre.
3. **Compra** só jogadores do **jogo**, de preferência com a etiqueta **"SALE"**; **nunca** de utilizadores. Sem "SALE" compra só se a posição for urgente; olheiro só em emergência.
4. Muitas vezes compra vários "SALE" para suplentes e **lista-os logo ao preço máximo**. O objetivo é **ir rodando** o plantel.
5. Limites do jogo: **4 slots** de venda (6 em eventos) e um **mínimo por posição** (por confirmar).
6. Quer ser **avisado** quando aparecem "SALE" novos que melhorem posições fracas do 11 (§7.7).

*Fonte: o dono, 2026-09-27. Descreve como funciona quando tem "um plantel forte (quase sempre)".*

### 7.1 Estrutura do plantel: 18 jogadores

| Posição | Titulares | Suplentes | Total |
|---|---|---|---|
| Atacantes (ATT) | 3: **1 EE, 1 ED, 1 PL** | 2 | 5 |
| Médios (MID) | 3 | 2 | 5 |
| Defesas (DEF) | 4 | 2 | 6 |
| Guarda-redes (GK) | 1 | 1 | 2 |
| **Total** | **11** | **7** | **18** |

- Corresponde a um 4-3-3 (3+3+4+1 = 11 titulares) mais 7 suplentes.
- Também cobre o 5-3-2: 6 defesas (5 titulares), 5 médios (3), 5 atacantes (2).
- EE = extremo esquerdo, ED = extremo direito, PL = ponta de lança.
- **Banco de suplentes do jogo (confirmado pelo dono):** tem sempre a mesma estrutura, **7 lugares: 2 ATT, 2 MID, 2 DEF, 1 GK**. Isto é o que a checklist de preparação (§6) espera no banco.
- Se o plantel for **só** estes jogadores, são **18**.

### 7.2 Mínimo de jogadores por posição (regra do jogo, **confirmado**)

O jogo obriga a um **mínimo de jogadores por posição** no plantel. Confirmado no jogo, posição a posição:

| Posição | Mínimo (palpite) | Confirmado |
|---|---|---|
| ATT | 3 | **Sim (2026-09-27):** com 4 atacantes, o jogo **não deixa listar 2 ao mesmo tempo** (ficaria em 2) — confirma mínimo de **3** |
| MID | 4 | **Sim (2026-09-27):** com 5 médios, o jogo só deixa listar 1 de cada vez (2 deixaria em 3) — confirma mínimo de **4** |
| DEF | 4 | **Sim (2026-09-27):** com 7 defesas (depois de vender 1), o jogo não deixa listar 4 — confirma mínimo de **4** |
| GK | 2 | **Sim (2026-09-27):** confirmado pelo dono com certeza |
| **Total** | **13** | |

Os 4 mínimos ficam **confirmados**, batendo certo com o palpite inicial (13 no total).
- A estrutura de 18 fica acima do mínimo em todas as posições, exceto GK (exatamente no mínimo).
- Relevante para rodar o plantel por transferências: limita quantos jogadores de cada posição podem estar fora ao mesmo tempo.

### 7.3 Slots de transferência e rotação *(rascunho — o dono disse que não se está a explicar bem)*

Palavras do dono, sem interpretação:
- Existem **4 slots de transferência**. Em certas alturas do jogo abrem **6 slots** (eventos mensais ou algo do género).
- Precisa de ter **3 titulares**, **suplentes à venda** e **1 jogador de rating baixíssimo** para permitir a rotação.
- Mesmo com um plantel de **média 100+**, mantém **um jogador de ~60 em cada posição** para rodar os suplentes das vendas.

**Interpretação nossa, por confirmar** (o dono ainda não a validou):
- O jogador de ~60 por posição serve de "enchimento": permite pôr os suplentes reais à venda (e vendê-los) sem quebrar o mínimo por posição (§7.2) nem deixar o banco (§7.1) por preencher.
- **Resolvido (7.4–7.6):** um slot é um lugar na lista de venda (**4 jogadores à venda ao mesmo tempo**, 6 em eventos). O ciclo da rotação está descrito em 7.5, 7.6 e no resumo no topo da secção 7.

### 7.4 Exemplo real: plantel atual do dono *(capturas de ecrã, 2026-09-27)*

O dono pode pôr **4 jogadores de cada vez** na lista de transferências. No plantel abaixo diz que **venderia** os jogadores marcados com ➜. Camisola colorida no ecrã = titular; camisola cinzenta/branca = não titular.

| Pos | Titulares | Suplentes a vender ➜ | "Enchimento" (rating mais baixo) |
|---|---|---|---|
| **ATT** (6) | Jogador 1 PL 26a **103** · Jogador 2 EE 25a 90 · Jogador 3 ED 34a 91 | ➜ Jogador 4 ED 26a 85 (13,5M) · ➜ Jogador 5 EE 30a 84 (12,0M) | Jogador 6 PL 25a **69** (2,6M) |
| **MID** (5) | Jogador 7 MC 27a **96** · Jogador 8 MC 23a 91 · Jogador 9 MCD 31a 88 | ➜ Jogador 10 MC 25a 90 (18,4M) | Jogador 11 MCD 29a **73** (3,8M) |
| **DEF** (8) | Jogador 12 DC 28a 95 · Jogador 13 DD 26a 92 · Jogador 14 DE 28a 86 · Jogador 15 DC 35a 90 | ➜ Jogador 16 DC 32a 89 (10,5M) · ➜ Jogador 17 DC 26a 87 (10,1M) · ➜ Jogador 18 DC 28a 84 (7,9M) | Jogador 19 DC 35a **69** (1,5M) |
| **GK** | *(não mostrado nas capturas)* | | |

Observações:
- **Cada posição tem exatamente um "enchimento"** (o mais barato e de menor rating), tal como o dono descreveu: 3 titulares + 2 suplentes à venda + 1 jogador fraco = **6 atacantes**. Nos médios, um dos dois suplentes é o enchimento (Jogador 11) e o outro é o que se vende (Jogador 10).
- Depois das vendas ficariam: **ATT 4** (mínimo palpitado: 3) · **MID 4** (mínimo: 4) · **DEF 5** (mínimo: 4). Nos médios ficaria **exatamente no mínimo palpitado (4)**, o que é coerente com o palpite do dono.
- Os jogadores a vender são os **não titulares de maior valor** de cada posição.
- **Motivo de manter o jogador fraco:** o dono **já não se lembra bem**, mas "fazia muito sentido na altura". Fica em aberto. Hipóteses (nossas, não confirmadas): cobre a vaga do banco e o mínimo por posição enquanto os suplentes reais estão à venda, sem perder dinheiro (vale quase nada).
- **Ícone de setas verde/vermelha = já está na lista de transferências** (confirmado pelo dono). Os 6 jogadores marcados já estão à venda, o que corresponde a **6 slots neste momento** (evento; confirmado pelo dono, voltam a 4 dentro de umas horas).
- **Ordem de venda (resolvido):** vende os suplentes **sem ordem particular** (§7.5).
- **Discos vermelho/amarelo = jogador em treino** (confirmado). Em treino nas capturas: **Jogador 1 (ATT), Jogador 7 (MID), Jogador 8 (MID), Jogador 12 (DEF)** = 4 treinos. Dois médios só é possível porque o dono usou o **treinador universal** (normalmente cada treinador é de uma posição). Nenhum jogador em treino está à venda, coerente com a regra "nunca treinar listados" (§5).

**O que as capturas confirmam sobre os dados** (visto no ecrã do jogo, ainda não na API):
- O número a **negrito** de cada jogador é o do seu papel: **Ata** nos avançados, **Med** nos médios, **Def** nos defesas. Confirma a suposição [S] de que o "rating" é a stat principal da posição.
- Colunas visíveis: Pos, Estado (ex.: cartão amarelo), Idade, Nac, **Ata / Def / Med**, **Con / Mor** (barras de condição e moral), Golos, **Valor**.
- Posições finas visíveis: PL, EE, ED, MC, MCD, DC, DD, DE.
- Indicadores na linha do jogador: cartão amarelo (Estado), disco vermelho/amarelo (em treino), ícone de setas (na lista de transferências), camisola colorida (titular).

### 7.5 Vender: que jogadores e a que preço

- **Que jogadores:** os **suplentes**, **sem ordem particular** ("meio indiferente").
- **Preço pedido** (palavras do dono):
  - Se o **preço máximo** do jogador for **acima de 100 M€**, pede só **75% do preço máximo**.
  - Se for **abaixo de 100 M€**, pede **SEMPRE o máximo**, por cada jogador.
- **O jogo acaba por vender os jogadores a bots, independentemente do preço** (afirmação do dono). Por isso pedir o máximo não atrasa a venda.
- **Os 75% são do preço máximo permitido** (não do valor de mercado). Exemplo do dono: o preço máximo do Jogador 1 é **111 M€** (o dono foi ver ao jogo), por isso pediria 75% disso ≈ **83,25 M€**.
- **Motivo (experiência do dono):** acima de 100 M€ fica **muito mais difícil vender pelo preço máximo**.
- **É probabilidade, não um limite (dono, 2026-10-12):** em dezenas de épocas, os jogadores caros **acabam sempre por se vender**; fora dos eventos só demoram mais (dados em `DISCOVERY.md` §3).
- **Multiplicador confirmado (2026-09-27): ≈2,5×.** Pontos de dados (valor → preço máximo):
  - Jogador 1: 44,0 M€ → 111 M€ = **2,52×**
  - Jogador 18: 7,9 M€ → 20,0 M€ = **2,53×**
  - Jogador 5: 12,0 M€ → 30,2 M€ = **2,52×**
  - Jogador 2: 19,2 M€ → 48,1 M€ = **2,51×**
  - 4 exemplos, todos entre 2,51× e 2,53× — coerente com o prior art (`PRIOR_ART.md`, que reporta ~2,5× noutra liga). Multiplicador = **2,5×** para efeitos práticos.
  - Consequência: o limiar de 100 M€ de preço máximo (§7.5, regra dos 75%) corresponde a valor de mercado ≈ **40 M€**.
- O preço máximo é um valor que o jogo mostra ao listar o jogador; onde se lê na API é desconhecido.

### 7.6 Comprar: só jogadores "SALE"

Palavras do dono:
- **Dá SEMPRE preferência** a jogadores que aparecem com a etiqueta **"SALE"** na lista de transferências.
- **NUNCA comprar jogadores de outros jogadores (utilizadores).** Assume que toda a gente vende pelo preço máximo, por isso esses jogadores estão **super inflacionados**.
- **Escolher sempre jogadores marcados "SALE"** na lista de transferências.

Leitura nossa: na prática, só se compra o que tem a etiqueta "SALE".

**Respostas do dono (2.ª ronda):**
- **"SALE"** = etiqueta **azul** "SALE" no canto do preço. Os jogadores "SALE" são **mais baratos que o costume**; o dono **não sabe dizer quanto** (desconto por medir).
- **Jogadores vendidos por utilizadores** são **muito caros para o rating**.
- **Se nenhum "SALE" serve:** "aí entra na necessidade". Se precisa **urgentemente** de uma posição, **compra**; se não, **espera**. O objetivo é **ir rodando** o plantel.
- **Escolha entre "SALE":** depende do **plantel e do dinheiro**. **Às vezes compra vários "SALE" diretamente como suplentes e põe-nos logo na lista de transferências ao preço máximo.**

**Como se distingue, na lista do mercado** (captura do dono, 2026-09-27):
- **Jogador de utilizador:** o **nome do clube aparece a azul** (ligação) e por baixo, em cinzento itálico, o **nome do vendedor**. Ex.: Jogador 21 (Clube C, vendedor "utilizador A") e Jogador 22 (Clube D, vendedor "utilizador B").
- **Jogador do jogo/bots:** clube em texto normal, **sem nome de vendedor**.
- **"SALE":** fita azul no canto superior direito da célula do preço (Doué 47,2 M€ e Jogador 23 37,6 M€ na captura).
- **Jogadores "World Legends":** linhas douradas com distintivo; não são o foco da estratégia do dono (dado nosso, não dito por ele).
- Colunas do mercado: bandeira, nome, Pos, Idade, Clube, **Ata / Def / Med**, preço.

**Exemplo do dono, com números da captura** (jogadores de utilizador vs. do jogo, preço parecido):

| Jogador | Vendedor | Pos | Ata | Preço |
|---|---|---|---|---|
| Jogador 21 | **utilizador** (utilizador A) | PL | **88** | 39,1 M€ |
| Jogador 20 | jogo | PL | **94** | 39,0 M€ |
| Jogador 22 | **utilizador** (utilizador B) | EE | **90** | 37,0 M€ |
| Jogador 23 (SALE) | jogo | ED | **96** | 37,6 M€ |

Pelo mesmo preço, o do jogo tem **+6 de rating** que o de utilizador (PL) e o "SALE" **+6** (EE/ED).
- **Com necessidade e sem "SALE" (confirmado):** compra um jogador **da posição, do jogo, sem etiqueta "SALE"**. **Nunca** de utilizador.
- **Jogadores Legend** (na lista de transferências, linhas douradas): o dono **evita sempre comprar**. Cada compra custa o **dinheiro do jogador + cerca de 50 boss coins** por ser Legend.
- **Inform players:** custam o **dinheiro + cerca de 5 boss coins**; o dono acha **mais aceitável** (compra-os se fizer sentido, sem regra fixa dita).
- **Olheiro (scout):** permite escolher **nacionalidade, idade e posição**. O dono **só o usa em emergência**: **custa boss coins** e **o olheiro demora muito tempo** a chegar; **"não são bons negócios"**.

### 7.7 Mercado: jogadores novos desaparecem depressa

- Em **ligas com muitos jogadores**, nas **horas em que aparecem jogadores novos** na lista de transferências, eles são **logo comprados** por outros.
- **Ao contrário, numa liga com poucos treinadores** (dono, 2026-10-16: o Qarabag, com 2 treinadores reais), há tempo: pode esperar-se que o preço de um anúncio do jogo desça antes de comprar.
- **Automação desejada pelo dono** (não urgente): ser **notificado quando aparecem jogadores novos** na lista de transferências, para poder comprar a tempo. Ver `PROJECT_BRIEF.md`.
- **Horas / frequência de renovação da lista:** o dono **não sabe** (sabe que há horas em que aparecem novos). Só se descobre observando o mercado.
- **Alertar sobre (dono):** jogadores **"SALE"** e de **posições de que precisa**, entendendo por "precisa" as posições com **ratings abaixo da média no 11 inicial**.
- **Forma do alerta (confirmada pelo dono):** é um **aviso** para ele ir **espreitar**; a decisão de comprar é dele. Exemplo dele: *"Há 5 jogadores com tag "SALE" novos! Tens um DC de 79 no plantel, e existem DC's com mais rating à venda!"*
  - Ou seja: (1) quantos "SALE" novos apareceram; (2) para as posições em que o plantel tem um titular fraco, compara o rating dele com os "SALE" disponíveis nessa posição e diz se há melhores.
- **Horas certas:** mais tarde, com análise de dados, quando o dono souber a hora ao certo; por agora vai verificando "mais ou menos".
- **Titular "fraco" (resolvido, 2026-09-27):** **ambos os critérios contam** — é "fraco" quem for o **mais baixo da sua posição** entre os titulares, **ou** quem estiver **abaixo da média do 11** (não precisa de ser os dois ao mesmo tempo).
- **Compras para o cartão do clube (dono, 2026-10-14, depois de ver o rival do Qarabag comprar ao valor):** um SALE interessa para **reforçar** e também para **revender** (§7 ponto 4: comprar SALE e listar logo ao máximo). Sem mínimo de lucro (os números de 14/10 mostraram que quase todos dão lucro; o que filtra é o dinheiro):
  - **Estratégia de compra (dono, 2026-10-15, substitui os critérios de 14/10: vaga livre e ordem pelo lucro):** o dono tem **sempre as vagas cheias** ("toda a estratégia é ter sempre jogadores à venda"), por isso a pergunta é com que jogador encher a próxima vaga que vagar. Proposta do Claude a partir dos registos (`DISCOVERY.md` §3), aceite pelo dono:
    1. Vagas de venda sempre cheias.
    2. **Revenda:** jogadores do jogo, **com ou sem SALE**, de **valor 10–40 M** (revendem entre 25 e 100 M e vendem em menos de ~1,5 dias), que cabem em **conta + poupança**; os **mais baratos face ao valor** primeiro (o que uma vaga rende por dia anda com isso; com o mesmo preço/valor, o de maior lucro). Põe-se logo à venda ao máximo.
    3. Para revender, nada acima de 40 M de valor (prende a vaga 3 dias ou mais); os do dono acima de 100 M continuam a 75 %.
    4. **Reforço:** rating maior do que o titular mais baixo da **mesma posição geral** (ATA/MED/DEF/GR), de qualquer valor, se couber no dinheiro; sem pressa, esperar 3–4 dias (o preço desce ~4 %/dia); de preferência jovens.
  - **No cartão (dono, 2026-10-15):** a faixa mostra **a melhor hipótese** (a 1.ª pela ordem acima, revenda ou reforço) e o hover **as 3 melhores**. A etiqueta "SALE" só aparece se a melhor a tiver (≤ 1,5×).
  - **Lucro estimado** = preço máximo de revenda − preço; máximo ≈ **2,5 × valor** (**[H]**: as vendas de 14/10 saíram a 2,48–2,49×), **75 %** disso acima de 100 M (§7 ponto 2).
  - **Pechincha:** preço ≤ **1,25 × valor**, marcado à parte (dono, 2026-10-15; era 1,1×, que nunca aparecia: o jogo vende a partir de ~1,19× e baixa os preços dia a dia, `DISCOVERY.md` §3).
  - **Registo (dono, 2026-10-15):** além dos SALE, o bot guarda todos os anúncios do jogo (`logs/<PC>/transferencias/jogo/`): quando aparecem e saem, com o primeiro e o último preço.
  - **"?" no lucro** quando a liga **não vende ao máximo**: nenhuma venda de um clube da liga a ≥ 2,4× o valor nas transferências dos últimos 3 dias (Espanha, 12–13/10, `DISCOVERY.md`).
  - Só avisa; comprar continua a ser do dono (regra 5).

### 7.8 Guarda-redes, moedas e o porquê do jogador fraco

**Esclarecimentos do dono (2026-09-27):**
- **Guarda-redes:** o "fraco" é o **2.º GK**. Exemplo dele: tem um GK de 100 e um de 60; aparece um de 105 → compra-o, e fica com 3; **põe o de 100 à venda** ao ter os 3; quando vende, **volta a ficar com 2** (105 + 60). Ou seja, nos GK são sempre **2** (titular + o fraco), com 3 só de passagem.
- **Prints:** eram do plantel do Clube A, onde os jogadores mais baixos já tinham esses ratings (69, 73, 69), por isso não são "60". O ~60 é uma ordem de grandeza.
- **Duas moedas** (confirmado): **dinheiro do clube (M€)** para transferências; **boss coins** para amigáveis, treino secreto, estágio e olheiro.
- **Slots:** neste momento **6**, e vão voltar a **4** dentro de umas horas.
- Camisola laranja ou azul = titular (laranja = titular em treino); cinzenta/branca = não titular (confirmado).

**Porque manter o jogador fraco — análise nossa, NÃO confirmada** (o dono já não se lembra do motivo e pediu a nossa opinião). Com os mínimos palpitados (§7.2), depois de vender os suplentes listados:

| Pos | Titulares | Sem o fraco | Mínimo palpitado | Com o fraco |
|---|---|---|---|---|
| ATT | 3 | 3 (no limite) | 3 | 4 |
| MID | 3 | **3 (abaixo)** | 4 | 4 |
| DEF | 4 | 4 (no limite) | 4 | 5 |
| GK | 1 | **1 (abaixo)** | 2 | 2 |

Razões plausíveis:
1. **Mínimo por posição:** nos MID e GK, sem o fraco não se cumpre o mínimo palpitado; nos ATT e DEF fica-se exatamente no limite, sem margem.
2. **Cobertura de lesões e suspensões:** sem reserva na posição, uma baixa obriga a jogar fora de posição. Nas capturas há 3 titulares com cartão amarelo (Jogador 8, Jogador 12, Jogador 15).
3. **Custo quase nulo:** vale 1,5–3,8 M€ nas capturas. Um suplente bom parado prende dinheiro que pode estar em compras.

**Palpite do dono (mais provável, ainda sem certeza): o motivo é não ter dinheiro parado** (razão 3). Ou seja, o jogador fraco é a forma mais barata de preencher o plantel sem prender capital em jogadores que não estão a render.

**Opinião nossa:** faz sentido mantê-lo. Sem ele a rotação **poderia** funcionar em ATT e DEF (no limite), mas em MID e GK depende de os mínimos serem os palpitados, e sem margem nenhuma para lesões.
- **Confirmado (2026-09-27):** os mínimos reais batem certo com os palpitados (ATT 3, MID 4, DEF 4, GK 2 — ver §7.2), e o jogo **bloqueia mesmo listar para venda** quando isso deixaria a posição abaixo do mínimo (testado em ATT/MID/DEF). A análise acima confirma-se: sem o jogador fraco, MID e GK ficariam exatamente no mínimo, sem margem para lesões/suspensões.

### 7.9 Trocas no 11: a posição específica conta *(dono, 2026-10-16)*

- Só se troca um titular por outro da **mesma posição específica** (p. ex. MC por MC). Um MCO não substitui diretamente um MC; para isso é preciso gastar uma **troca de posição universal** (item do inventário).
- Essa troca fica para **emergência** (p. ex. vendeu-se o titular antes do jogo e não há negócio a fazer). Contra um adversário fraco, e com o objetivo da liga quase cumprido, aceita-se jogar com o titular mais fraco em vez de gastar a troca.
- **Reforçar primeiro onde o titular está abaixo da média da equipa** (dono, 2026-10-16): um GR de 79 numa equipa de média ~73 não precisa de reforço, mesmo que haja um GR melhor barato.
- Quer ter o titular à venda **vendido antes do jogo**: o dinheiro paga o suplente que falta (no caso, um ATA para o banco), e a gestão dos médios vê-se depois.
- **No cartão de compras** (D-058, confirmado pelo dono a 2026-10-16): um jogador do jogo é **reforço** se for melhor do que o titular mais fraco **da mesma posição específica**, e só onde esse titular está **abaixo da média do 11**. Um titular **à venda** conta como quem entraria para o lugar dele: o melhor do resto do plantel na mesma posição específica que não esteja também à venda; sem ninguém, o lugar fica aberto (qualquer um é reforço). A média é a do 11 assim. **[S]** A condição física não entra (um suplente cansado conta como se estivesse em forma).

## 8. Estádio

*Fonte: o dono, 2026-09-27.*

Há **3 componentes** a melhorar, cada um com **níveis 0, 1, 2 e 3**:

| Componente | O que dá |
|---|---|
| **Treinos** | **+% de melhoria a cada treino** |
| **Campo** | **+% de melhoria geral da equipa antes do jogo** |
| **Capacidade** | **Aumenta a receita** |

- **Ordem do dono:** melhora **sempre primeiro os Treinos**, até ao máximo (nível 3); **depois o Campo**; **por fim a Capacidade**.
- **Custo:** cada melhoramento custa cerca de **200k** em **dinheiro do clube** (confirmado; não são boss coins).
- **Melhoramentos por nível (fechado, 2026-09-27, número exato não é necessário):** do nível 0 para o 1 é **só 1 melhoramento**. Do 1 para 2 e do 2 para 3 são mais, e o número **varia por clube/liga** (Clube A 2→3: 11; clube pequeno na outra liga 2→3: 7), provavelmente pelo nível da liga — mas o dono considera **irrelevante para a automação**: a regra que importa é a **ordem de prioridade** (Treinos ao máximo → depois Campo → depois Capacidade, ver acima), que já não depende de saber quantos melhoramentos cada passo leva.
- **Duração total:** normalmente leva **quase uma época** a levar os 3 componentes ao máximo.
- Liga-se à automação de treinos (§5): o nível de Treinos aumenta o ganho de cada sessão.

## 9. Patrocinadores

*Fonte: o dono, 2026-09-27.*

- Dão **dinheiro residual**, "tipo **200k**", que **vai subindo ao longo da época**.
- **4 slots**, com **contratos de cerca de 2 ou 3 jogos**.
- É preciso **renovar no fim do contrato de cada slot**.
- **Os ~200k são por jogo, por slot** (confirmado). Conta nossa: com os 4 slots cheios e valores parecidos seriam cerca de 800k por jogo (não confirmado).
- **Ao renovar** aparecem **várias hipóteses, mas é só isco ("bait")**: ninguém escolheria uma hipótese pior, ou seja, há sempre uma opção claramente melhor e é essa que se escolhe.
- **Moeda (resolvido, 2026-09-27): dinheiro do clube**, confirmado pelo dono — 200k em boss coins não faria sentido para um valor residual deste tipo.

## 10. Médico e advogado

*Fonte: o dono, 2026-09-27.*

- **Médico:** cura lesões. Se a lesão for de **2 ou 3 dias**, pode curar **de uma vez** ("1x"), mas **nem sempre** funciona.
- **Advogado:** baixa uma suspensão de **vários jogos para 1 jogo**. **Não remove a suspensão por completo:** fica **sempre no mínimo 1 jogo**.
- **Custo e moeda (resolvido, 2026-09-27): usar não gasta nada.** Ambos **demoram 8 horas** a fazer efeito de graça; **boss coins só são gastos se se quiser saltar a espera** ("skip"), tal como os vídeos de treino (§12.1) — mesma lógica, moeda diferente (aqui é sempre boss coins para o skip, não vídeos).
- **Uso:** o dono usa **sempre** (médico e advogado) — faz sentido, já que o uso base é grátis.
- **[?]** Valor exato do skip em boss coins: não indicado, por confirmar se algum dia interessar.

## 11. Análise do adversário e objetivo da época

*Fonte: o dono, 2026-09-27.*

**Antes de cada jogo**, além de enviar o analista (§6), o dono:
1. Vai ver a **tática do adversário nos últimos jogos**.
2. Vai à **"lista de treinadores"** ver se o adversário **esteve online nos últimos dias**.
3. Vai ao **"valor do plantel"** e olha para o **"valor médio por jogador"**, que lhe dá **uma boa ideia do valor (força) do plantel**.

**Objetivo da época:** terminar **sempre com o maior "valor médio por jogador"**. Segundo o dono, **tem acontecido** com esta estratégia.

- O dono usa o **valor médio por jogador** como leitura de quão valioso é o plantel do adversário.
- **Corrigido pelo dono:** o critério de "mais forte / mais fraco" **não** é o valor médio por jogador. Antes de cada jogo o jogo mostra uma **média do plantel de 0 a 100 em rating (não em preço)**, e **é essa a referência** para saber se o adversário é mais forte ou mais fraco (§1).
- **"Valor médio por jogador"** = dinheiro (preço), conta o **plantel todo**. Mesmo com os jogadores fracos (§7.8), o dono costuma ficar **sempre com o plantel mais forte**.
- O objetivo é ter o maior **da liga**, "porque resulta em mais jogos ganhos".
- **Duas métricas diferentes:** *valor médio por jogador* (preço, plantel todo; objetivo de fim de época e leitura do adversário) e *média do plantel 0–100* (rating; mostrada antes de cada jogo; usada para escolher a formação).

## 12. Vídeos promocionais: o que o jogo oferece

*Fonte: o dono, 2026-09-27. Em curso: o dono ainda pode acrescentar mais usos.*

### 12.1 Treinos

- Ver **1 vídeo retira 2 horas** ao tempo de um treino.
- **Máximo de 4 vídeos por ciclo de 3 horas** (não por hora — ver confirmação abaixo) → dá para retirar **8 horas** (4 × 2 h), **distribuídas** por vários jogadores ou **todas ao mesmo jogador**.
- Na prática, 4 vídeos num jogador **acabam-lhe a sessão de treino**, que dura **8 horas**.
- **A duração varia com o momento do jogo.** Normalmente 8 h, mas **em certas alturas os treinos baixam para 2 h por jogador**: as mesmas alturas em que as transferências permitem **6 slots em vez de 4** (§7.8). É provavelmente o que o prior art (`PRIOR_ART.md`) observou (7200 s = 2 h). **Ler a duração real no jogo, nunca fixá-la no código.** O dono diz que é **por isso que automatizar vai ser bom**: com sessões de 2 h há muito mais recolhas e recolocações a fazer.
- **Regra do bot para os vídeos de treino (dono, 2026-10-05): uniformizar.** Cada vídeo vai para a sessão com mais tempo em falta (entre os 4 treinos de cada clube, e entre os clubes), para todos acabarem por volta da mesma hora.
- Liga-se à checklist (§6): as **4 sessões de treino têm de estar concluídas no dia do jogo**; os vídeos são o que permite encurtá-las.
- **Limites separados** (confirmado): o teto dos vídeos de treino é **independente** do teto dos vídeos da loja (boss coins).
- **Renovação (resolvido, 2026-09-27): não é de hora a hora.** Depois dos 4 vídeos, o próprio jogo diz: *"Atingiste o número máximo de vídeos que podes ver aqui. Regressa dentro de **3 horas** para veres um novo vídeo!"* Ou seja, o ciclo de treino é **4 vídeos por 3 horas**, não 4 por 1h como os vídeos da loja (§12.2). Confirmado por captura de ecrã do dono.

### 12.2 Loja: vídeos que dão boss coins

- Na loja, ver vídeos **dá boss coins**.
- **Limite confirmado (2026-09-27): 9 vídeos**, não 10 — corrige o palpite inicial do dono e a leitura do prior art (que reportava um `threshold` de 10 noutro contexto/liga; ver `PRIOR_ART.md`).
- **Tempo de espera confirmado: 1 hora.** Ao atingir o limite, o jogo pára a secção durante 1h (o dono não distinguiu se é fixo ou conta do último vídeo, mas o valor de 1h fica confirmado).
- **[?]** Continua por confirmar se, ao ver os 9 vídeos, há **recompensa extra** (o dono tinha mencionado isso para o limite antigo de "10"; por reconfirmar com o número certo).
- **Cada vídeo dá 1 boss coin** (confirmado pelo dono).
- **Treinos primeiro (dono, 2026-10-14):** entre dois vídeos da loja, se um treino já acabou, o bot pára a série, recolhe e põe os treinos, e vê o resto dos vídeos na passagem seguinte (a janela da loja continua aberta). Nos eventos de treinos de 2 h, uma série de ~20 min custava muito.
- **Conta (atualizada):** 9 vídeos = 9 boss coins por ciclo de 1 hora (mais a possível recompensa extra, por confirmar). Um amigável custa 4 (§6), ou seja, um ciclo paga mais de 2 amigáveis.

### 12.3 Finanças/poupança: vídeos de dinheiro

- Uma vez a cada **24 horas** (o dono acha; não tem a certeza), há **3 vídeos** que dão **dinheiro do clube residual**:
  1. **1.º vídeo:** cerca de **300k**
  2. **2.º vídeo:** cerca de **600k**
  3. **3.º vídeo:** **3 boss coins**

## 13. Finanças e poupança

*Fonte: o dono, 2026-09-27.*

- O dinheiro pode ser **trocado entre os fundos do clube e a poupança**.
- A **poupança rende "juro"**, oferecido **no final do jogo do dia**.
- Por isso **convém ter sempre todo o dinheiro na poupança** e não nos fundos do clube.
- **Só se pode transferir tudo de uma vez**, não parte: por exemplo, não dá para "transferir 10 milhões dos meus 50 para a poupança". É tudo ou nada.
- Notas nossas (não ditas pelo dono): como é tudo ou nada, **qualquer compra obriga a tirar todo o dinheiro da poupança**; convém voltar a depositar o que sobra o mais depressa possível, sobretudo antes do jogo do dia (é aí que o juro conta). O prior art reporta um endpoint que devolve saldo e poupança em separado (`PRIOR_ART.md`).
- **Enviar e depositar** na poupança funcionam **da mesma forma: sempre tudo** (confirmado).
- **Taxa do juro (confirmada, 2026-09-27): 2% por dia de jogo.** Três exemplos do dono, em dois clubes/ligas diferentes:
  - Clube A: 5,45 M€ → 109k (2,00%)
  - Clube A (outro dia): 26,6 M€ → 534k (2,01%)
  - Clube B (outra liga): 3,8 M€ → 76k (2,00%)
- **Depósito automático (dono, 2026-10-12):** **pouco antes de cada jogo**, o bot deposita na poupança tudo o que estiver nos fundos (patrocinadores, vendas), para o juro do fim do jogo contar. O dono pediu 2 min antes; ficou **5 min** (o bot acorda a essa hora e deposita antes de tudo o resto) e qualquer passagem nos últimos **15 min** também deposita, porque uma série de vídeos pode atrasar o acordar. Mais cedo não: o dono pode ainda tirar o dinheiro para comprar. Sem mínimo. Se o jogo recusar, não insiste até ao dia de jogo seguinte.
- **Pré-época (dono, 2026-10-15):** o dono acha que o juro também é pago na pré-época, no fim de cada dia, mesmo sem jogo. O bot deposita **5 min antes da hora do 1.º jogo do campeonato, em cada dia da pré-época** (a mesma regra dos 15 min). **[H]** Juro na pré-época: por confirmar, comparando a poupança antes e depois dessa hora.
- Consequência (nossa): a 2% por dia, dinheiro nos fundos do clube "custa" 2% por dia em juro perdido (50 M parados = 1 M/dia). Reforça o palpite do dono sobre o jogador fraco (§7.8): dinheiro preso num suplente valioso também não rende juro.

## 14. Notas de implementação (nossas)

- Tudo é **determinístico** → funções puras `(estado do jogo) → decisão`, testáveis sem tocar no jogo (44 testes).
- Os especialistas mudam sempre que o plantel muda (compras, vendas, lesões, aniversários) → boa candidata a automatizar mesmo com tática manual.
- Os endpoints para **ler/escrever** tática e especialistas são **desconhecidos** (o prior art só viu chaves `TeamTactic_{liga}_{equipa}` no localStorage). Ver `PRIOR_ART.md` §"Por verificar".
- **Eventos do jogo (dono, 2026-10-14):** as definições de cada liga lêem-se de hora a hora e, entre as 05:30 e as 07:00, de 10 em 10 min, para saber a que horas os eventos começam (`events.check_every`). Uma mudança fica no registo com as duas leituras entre as quais aconteceu.

## 15. Estádio e patrocinadores

*Fonte: o dono, 2026-10-07.*

**Estádio**
- Não há "recolher": uma melhoria acaba e a seguinte **põe-se a correr**, nada mais.
- **Ordem das partes:** campo de treinos → campo → capacidade.
- **Duração de uma melhoria (dono, 2026-10-09):** **18 h** normalmente; nos **eventos** do estádio, **4 h**. Há eventos destes para outras coisas também (p. ex. treinos). Visto nos registos: campo, 3 melhorias seguidas de 18h00. **[S]** As outras partes (treinos, capacidade) duram o mesmo. O jogo só dá a hora em que a melhoria acaba; o quadro calcula o início como "fim − 18 h" (ou "fim − 4 h" se a viu começar num evento) e, quando não dá para saber, mostra só o tempo.
- **Em todas as equipas**, sempre que houver dinheiro.
- Se não houver dinheiro nos fundos, ver a **poupança**: se tiver, tirar tudo (§13: é tudo ou nada), pagar a melhoria e **voltar a depositar o que sobra** o mais depressa possível.
- Se **nem com a poupança** chega, **não faz nada** (nem tira a poupança).
  - **Como o bot faz (aceite pelo dono, 2026-10-08):** o jogo não dá o preço da melhoria (`GET stadium` não o tem), por isso o bot não sabe de antemão se chega. Faz assim: tenta com os fundos; se o jogo recusar, tira a poupança e tenta outra vez; se recusar de novo, **deposita tudo** (a poupança é tudo ou nada, por isso o dinheiro que já estava nos fundos também vai) e só volta a tentar quando o total (fundos + poupança) subir. O dono: **fundos a 0 nunca são problema.**
- O dinheiro pode aparecer de repente (p. ex. **um jogador vendido**): por isso o bot **volta a verificar o saldo e a poupança** regularmente, não só quando um temporizador acaba.
- Cada melhoria é um temporizador (`DISCOVERY.md` §3): o bot acorda quando acaba.

**Patrocinadores**
- Quatro espaços (slots). Cada espaço livre recebe a proposta que paga **mais por ronda** (`sponsorRevenueForTeam`, que já inclui o bónus); em empate, o contrato mais curto.
- **Sempre a melhor para cada espaço** (dono, 2026-10-07): o mesmo patrocinador pode repetir-se; se o jogo recusar uma proposta nesse espaço, usa-se a seguinte melhor. Não há espaços bloqueados, só preenchidos ou vazios. O ecrã mostra 4 propostas por espaço; a API devolve 12.

## 16. Condição física dos titulares

*Fonte: o dono, 2026-10-07.*

- A condição (`fitness`, %) mostra-se a **amarelo abaixo de 80** (79 amarelo, 80 verde).
- Um **titular** (onze) com a condição a amarelo **convém ser trocado 1 jogo para descansar**.
- O bot **só avisa** (quadro e registo, uma vez por jogador até recuperar); não troca ninguém, porque o onze e a tática são do dono.
- Só contam os titulares (`lineup` 1 a 11) e não lesionados; o banco não interessa. O limiar do vermelho está por apurar.
- **Sem suplente** (dono, 2026-10-13): quando um titular cansado não tem quem o substitua na posição, o dono compra outro para o descansar (§19, compras). A linha dos cansados diz `(sem suplente DEF)` e, ao passar o rato, mostra até 3 jogadores do **SALE** dessa posição que caibam no dinheiro do clube. **Só sugestão:** comprar é uma escrita nova (regra 5).
  - **[S]** Suplente = um jogador da mesma posição (ATA/MED/DEF/GR) que não está no onze e não está lesionado nem castigado, seja qual for a condição.
  - **[S]** Dinheiro do clube = o mesmo total do cartão (conta + poupança). Opções do SALE = os jogadores do jogo com a fita "SALE" na lista de transferências da liga (§7.6), da posição em falta, preço ≤ dinheiro, os de melhor rating primeiro.

## 17. Recompensas diárias: início de sessão, missões e vídeos acumulados

*Fonte: o dono, 2026-10-07. Pedidos observados com `inspect-writes` (`DISCOVERY.md` §3).*

**Início de sessão** (uma vez por dia, quando `user/dailylogin` diz `isClaimable`)
- Reclamar. O site gasta a recompensa logo na carteira certa; o bot faz o mesmo: **energia** → carteira de energia; **boss coins** → carteira de boss coins (o dono: "vão para a carteira, não há nada a ver").
- Qualquer outra recompensa (p. ex. o saco do dia 21): reclamar e **deixar no inventário**, sem gastar. **[S]** O pedido que a gasta nunca foi observado.
- **Janela "Unclaimed Energy"** (energia por reclamar, p. ex. depois do prémio das missões; aparece no browser dos vídeos e tapa o jogo): carregar **sempre em Claim**; a energia vai para a carteira de energia (dono, 2026-10-09: "dá claim sempre"; D-028).
- **Janela das boss coins por reclamar** ("Boss Coins não reclamadas", vista pelo dono a 2026-10-15): igual, **Claim**; as boss coins vão para a carteira (D-055). No browser dos vídeos o título é "**Unclaimed Boss Coins**", com um botão **Claim** (visto na captura de 2026-10-15 16:08, PC do trabalho); o bot aceita esse título e variantes.

**Missões**
- As **3 missões diárias** (as que têm `order`) reclamam-se quando o progresso chega ao objetivo (`threshold`, do catálogo `missions`). O bot já treina jogadores, por isso são as que se cumprem sozinhas.
- Depois de reclamar as 3, abre-se a **recompensa do dia**: a missão sem `order` cujo `sourceType` é **o dia de hoje** da semana (calculado a partir de `endDateTime`: semana de 7 dias, que mudam às 04:00 UTC). As dos dias seguintes também aparecem na lista, mas **nunca se reclamam antes do dia delas**; no máximo uma por dia. O jogo pergunta "guardar" ou "usar já": o bot escolhe **sempre guardar**, ou seja, reclama e **nunca gasta** o prémio (fica no inventário). Se o jogo recusar o pedido, o bot não insiste nesse prémio até ser reiniciado.
- Só se reclama o que o próprio quadro de missões do jogo mostra como disponível.
- **Dinheiro no inventário (dono, 2026-10-15): "claim sim, usar não".** O que é só dinheiro (**boss coins** e **dinheiro do clube**, p. ex. a recompensa do dia das missões) vai logo para a carteira, como o "Claim" do jogo; os outros itens (trocas de posição, treino +100, treinador universal) ficam no inventário para o dono usar. O dinheiro do clube vai para o clube com **menos dinheiro** (fundos + poupança) nesse momento (escolha do dono). Antes ficava tudo no inventário e o jogo mostrava "Boss Coins não reclamadas".

**Vídeos acumulados (troca de posição)**
- A cada 10 vídeos (contador `RewardedVideoCounterPositionModifier`), quando `isClaimable`, reclamar: o item ("Switch") vai para o **inventário** e **não se usa**. O contador é alimentado pelos vídeos que o bot já vê.

**Limites do jogo (regra geral)**
- O inventário tem um limite por item (`inventoryLimit`, catálogos `actionrewards` e `rewards`). O bot **não reclama** se o item ficasse acima do limite.
- Nunca se usam os itens do inventário (isso exige escolhas: jogador, posição...). É decisão do dono. **Exceção (D-039):** os que vão expirar usam-se 4 h antes (§20).
- O bot respeita o jogo: sem pedidos repetidos para o que o jogo recusou.

## 18. Médico e advogado

*Fonte: o dono, 2026-10-09. Pedidos em `DISCOVERY.md` §3 (médico observado; advogado e levantamentos por analogia, aceite pelo dono).*

- **De graça**, com um timer de 8 h; no fim **levanta-se** (como um treino). **Sem vídeo** para encurtar no PC.
- **Médico:** **todos** os lesionados (onze, banco ou fora), **logo** que se lesionam. Pode usar-se **várias vezes por jornada** (às vezes tira 1 jogo, às vezes 4). Com 2 lesionados ao mesmo tempo, tenta os dois; se o jogo só deixar 1, o outro espera.
- **Advogado:** a mesma lógica para os suspensos, mas **só 1 vez por jornada** por jogador. **Só com 2 ou mais jogos de suspensão:** com 1 jogo o jogo não deixa pôr no advogado (dono, 2026-10-09; coerente com §10, o advogado baixa para 1 jogo). O quadro mostra na mesma o suspenso.
- Uma falha aqui nunca encrava as outras tarefas do bot; o quadro mostra a mudança logo a seguir (D-026).

## 19. Plano de época: criar a liga e ganhar distância cedo

*Fonte: o dono, 2026-10-12 (conversa sobre ganhar mais jogos e campeonatos; a conta das boss coins está em `WORKLOG.md`, 2026-10-12).*

- **Criar a liga** em vez de entrar numa já a decorrer. Cada criação custa **~350 boss coins** em média.
- **Começar logo com o clube de maior valor do plantel** da liga (ao criar a liga, o jogo deixa escolher o clube). Como as automações tornam tudo mais eficiente (treinos, amigáveis, vídeos, poupança), quanto mais cedo o plantel for o melhor, **mais depressa ganha distância** para os outros.
- **Estágios: até 3 por época** (10 + 20 + 50 = 80 coins). Os 3 seguintes (100, 200, 500) são exponencialmente mais caros; com a distância ganha cedo, deixam de ser precisos.
- Conta do dono: com ~190 boss coins por dia, a liga (~350), os 3 estágios (80) e os amigáveis (≈28 coins por dia por equipa) dá para **4 equipas**.

*Mais respostas do dono, 2026-10-13:*

- **Objetivo de longo prazo: domínio mundial.** Conquistas em todos os países, pela **ordem alfabética** dos países. **O jogo conta o país com qualquer uma das 3** (campeonato, taça ou objetivo da época, numa liga "Major"; verificado no código do site em 2026-10-14, `DISCOVERY.md`). **[?]** Falta o dono dizer se a regra dele abaixo ("só feito quando não falta nada") se mantém, sabendo isto. Um país só fica "feito" quando lá não falta nada; por exemplo, um país onde só faltava a taça foi repetido por isso.
- **Que clube escolher** ao criar a liga: em regra o de **maior valor e mais jogadores**, sobretudo nas ligas que o dono não acompanha. Pode escolher outro **muito perto do melhor** por gosto pessoal. Não é obrigatoriamente o de melhor onze. *Em observação (dono, 2026-10-14: "vamos indo vamos vendo"; regra igual por agora):* o objetivo da época não segue a força do plantel (`DISCOVERY.md`) e o país conta com o objetivo; um clube com mais folga entre objetivo e força pode ser mais seguro do que o mais forte (o mais forte pode ter objetivo 1.º).
- **Estágios: só em momentos cruciais**, como eliminatórias da taça contra adversários difíceis. Não há calendário fixo.
- **Quando criar a liga seguinte:** quando apetecer ao dono, sem regra. Sinal de que pode valer a pena: o campeonato atual a acalmar (equipas desistem, mais jogos contra bots, plantéis mais caros, transferências mais lentas).
- **Mercado no arranque:** vender os piores até ficar só com o necessário (**onze + banco**); depois, rodar como se faz agora (§7).
- **Prioridade da época: as 3 conquistas** (campeonato, taça e objetivo), sem uma acima das outras: com o bot, a teoria e o melhor clube, o dono conta ganhar tudo.
- **Taça:** jogos a uma mão, no máximo 4 (oitavos, quartos, meias, final).
- **Objetivo da época:** o clube diz no início um lugar (p. ex. 7.º, 3.º); acabar nesse lugar ou acima cumpre. Com um clube cujo objetivo é o 1.º, não ganhar o campeonato é falhar a época.
- **Todos os países**, mesmo os de ligas fracas (o objetivo é 100 % do mundo). **[?]** Ordem alfabética provavelmente em português, como o jogo os mostra em português.
- **Banco:** 2 atacantes, 2 médios, 2 defesas e 1 guarda-redes, mais alguma folga para ir rodando as vendas. Os piores vendem-se **sempre ao preço máximo** (§7).
- **Fim da época:** o dono fica **sempre até a liga acabar**. Se falhar uma conquista, não dá para ficar: a época termina e é preciso criar uma liga nova nesse país.
- **Poupar coins quando a época está segura** (dono, 2026-10-13, a partir de uma ideia do Claude): no fim da época muitos treinadores já desistiram e há muitos clubes com bots, por isso faz sentido poupar. Fazer **só 1 amigável** em vez de 4 quando: há **+10 pontos** sobre os adversários, e/ou não há mais jogos importantes até ao fim da época, ou o plantel do dono vale **muito mais** do que o dos outros.
  - **[S] Proposta do Claude, por confirmar:** a decisão é por jogo; o jogo perigoso (confronto direto, como o alarme da janela, ou taça contra plantel mais forte) tem sempre os 4.
  - *Respostas do dono (2026-10-13):* os pontos de avanço contam-se **sobre o 2.º** (com a liga criada e o melhor clube, o dono conta ir sempre em 1.º). O número 10 foi "por alto": **[?]** a calibrar com a diferença real nas ligas atuais. **Taça: igual ao campeonato** (o modo poupança também se aplica). **Intense Friendlies:** sem certeza; numa fase adiantada, já a dominar, talvez **2 amigáveis por dia** em vez de 8; depende sempre da fase da época **[?]**. **[?]** "Plantel muito maior": sem resposta ainda.
  - *Dados para calibrar (leitura de 2026-10-13, ligas em que o dono entrou, não criadas):* liga de 20 clubes, 16 de 38 jogos feitos: dono em 2.º a 1 ponto do 1.º; o seu plantel é o mais valioso, 1,20× o 2.º. Liga de 12 clubes, 14 de 22 jogos: dono em 3.º, a 7 pontos do 1.º; o seu plantel é só o 6.º em valor (o 1.º vale 1,10× o 2.º). Nas duas, os planteis do topo estão perto uns dos outros (1,1–1,2×): **um limite de 1,5× quase nunca disparava**, e +10 pontos não acontece em nenhuma.
  - **[S] Proposta do Claude (2026-10-13), em vez dos 10 fixos:** poupar quando o **avanço sobre o 2.º for igual ou maior do que o número de jogos de campeonato que faltam** (com 10 por jogar, 10 pontos; com 4, 4). Acompanha a fase da época, como o dono pediu; matematicamente campeão é avanço maior do que 3 × jogos que faltam.
  - **Em aberto por decisão do dono (2026-10-13):** discutir de novo no futuro, de preferência com números de uma liga criada por ele. Por decidir: a regra dos pontos (10 fixos ou "avanço ≥ jogos que faltam"), a condição do plantel muito maior (que valor, ou sai) e o Intense Friendlies (2 por dia?). Nada a construir até lá.
- **Passagem para o torneio de campeões:** o dono acha que **tudo** desaparece (dinheiro e poupança) e que todos recomeçam iguais. **[?]** Para analisar no fim de uma época com bilhete.
- **Compras:** conforme a necessidade. Se só há um jogador numa posição e está a ficar cansado, compra-se outro para o descansar. Com tudo tranquilo, compra-se o mais valioso que o dinheiro permita, de preferência no SALE (nem sempre há).
- **Nada passa de uma liga para a outra.** Exceção: no fim da liga às vezes ganha-se um **bilhete para um torneio de campeões**. O dono costuma jogá-lo; aí passa o plantel e quase tudo, mas **não conta para o domínio mundial**. Na passagem para o torneio convém ter tudo em jogadores, porque o dinheiro desaparece (ver "Passagem para o torneio de campeões" abaixo).
- **Duração:** sempre 1 jogo por dia: 4 dias de pré-época, depois o campeonato e a taça, e o último dia. O tamanho da liga é o do país (não se escolhe).
- **Taça:** a preparação é a mesma do campeonato, mas um jogo a eliminar justifica um estágio mais facilmente. Se o jogo da taça for contra um bot muito fraco e houver a seguir um jogo difícil do campeonato contra um adversário direto, pode poupar titulares na taça.
- **Várias equipas:** o jogo dá **4 lugares** por conta. A partir de agora, ligas criadas pelo dono, um país de cada vez pela ordem alfabética; às vezes também um torneio de campeões.
- **Na janela (dono, 2026-10-13):**
  - *Força da equipa* num círculo (o número do jogo, `DISCOVERY.md`): a do clube do dono sempre; a do adversário **só depois da análise**, como no jogo (antes, o jogo não mostra o onze dos outros; sem estimativas). **[S]** Cores: a do clube do dono azul (neutra); a do adversário comparada com a nossa: verde se for 2 ou mais abaixo, vermelho se for 2 ou mais acima, amarelo se estiverem a menos de 2.
  - *Hover no lugar do campeonato:* os 3 primeiros com os pontos (se o clube estiver abaixo do 3.º: os 2 primeiros e o clube) e o objetivo da época ("Objetivo: 4.º ou acima"). Com o título **matematicamente garantido**, o cabeçalho diz "Campeões" em vez de "1.º Campeonato". **[S]** Garantido = em 1.º e o 2.º não consegue chegar aos nossos pontos nem ganhando todos os jogos de campeonato que lhe faltam (o empate não conta como garantido: o critério de desempate do jogo não é conhecido).
  - *Hover no valor do plantel (dono, 2026-10-15):* a tabela do jogo por valor do plantel (clube, valor, jogadores, valor médio por jogador) à volta do clube: em **1.º, os 2 de baixo**; senão **1 acima e 1 abaixo** (em último, só o de cima). Sem o nome do treinador (o bot não o lê).
  - *Formato dos dois hovers (dono, 2026-10-15):* tabelas como as do jogo, com os nomes das colunas por cima e o nosso clube destacado. Campeonato: **# · Clube · J · DG · Pts** e o objetivo por baixo; valor do plantel: **# · Clube · Valor · Jogadores · Média**.
  - *Cores e objetivo (dono, 2026-10-15):* a linha do nosso clube numa faixa da **cor do clube** (meio transparente). Ao lado do objetivo, o **certo verde** se o lugar atual o cumpre (nesse lugar ou acima) e o **"!" amarelo** se está abaixo; sem marca na pré-época (`weekNr` < 1), porque a tabela ainda não conta. O hover do adversário passa a linhas: nome, valor do plantel, jogadores, média.
  - *Círculos cheios (dono, 2026-10-15):* um círculo cheio (treino pronto, médico/advogado/treinador universal pronto, parte do estádio no máximo) fica na **cor do clube**, um pouco mais forte do que a dos temporizadores a correr (que é a cor do clube meio apagada). Antes ficava sempre verde, fosse qual fosse o clube. O amarelo de "à espera" mantém-se, porque pede atenção. **[S]** "Um pouco mais forte" = 70 % da cor do clube (o temporizador tem 50 %).
- **Criar a liga:** o dono ainda nunca criou uma; vai ser **pública**. O jogo deixa escolher o número de clubes, pública ou privada e convidar amigos. O custo varia com o número de clubes/jornadas e talvez com a popularidade da liga.

## 20. Inventário: usar o que vai expirar

*Fonte: o dono, 2026-10-12 ("há itens que eu perco porque me esqueço"; perder = expirar sem usar). Pedidos em `DISCOVERY.md` §3 (lidos no código da web; o 1.º uso do treinador universal feito e visto a 2026-10-12). Substitui, para estes itens, o "nunca se usam itens" do §17 (D-039).*

- **Que itens:** só os que **expiram** (o jogo dá-lhes prazo, 7 dias depois de entrarem): **treinadores universais** (24 h, 48 h) e **sacos** (p. ex. o do início de sessão). As **trocas de posição** e a **progressão** não expiram: continuam **manuais**, nunca as usa o bot.
- **Quando:** **4 h antes de expirar** (o dono: "3 ou 4 horas"), o bot usa o item sozinho. **24 h antes**, a janela avisa junto ao ícone do inventário.
- **Treinador universal: que equipa.** É por equipa (dura 24/48 h a contar da ativação). Vai para a equipa com **mais a ganhar**: a de maior previsão do jogo para o treinador universal (`forecastUniversal`) entre os jogadores que ele pode treinar (regra abaixo); empate → a de **pior plantel** (o dono: "ou a que tiver em pior lugar/pior plantel"; em geral coincidem, porque os de rating mais baixo ganham mais por treino). **[S]** Uma equipa com um treinador universal já ativo não recebe outro; se nenhuma estiver livre, o bot avisa e o item expira. **[S]** Só nas ligas que deixam usar itens (`consumablesAllowed`).
- **Treinador universal: quem treina** (dono: "concordo"): a regra do §5 mas **de qualquer posição**: titular, menos sessões nesta jornada, maior previsão para o treinador universal; fora quem já treina, está à venda, lesionado ou tem 30+ (GR de qualquer idade). Sessões de 6 h (`TrainingUniversalSession`); quando uma acaba e é recolhida, entra outro, enquanto o treinador estiver ativo. **[S]** Sem titular possível, o resto do plantel com as mesmas exclusões. No 1.º uso (2026-10-12, escolha do Claude com o OK do dono): um defesa titular de 24 anos da equipa 1 (a outra equipa não tinha titular possível: todos a treinar, à venda ou 30+).
- **Sacos:** abrir 4 h antes de expirar. O que sai fica no inventário (se expirar, entra nesta mesma regra); os **boss coins** que saem vão logo para a carteira, como faz o site.
- **Janela:** o ícone do inventário do jogo na barra de cima, **à direita**, junto ao estado do bot, **sem número**; um ponto amarelo quando algo expira em menos de 24 h; ao passar o rato, **só os itens que expiram**, com o tempo em dias e horas ("1 dia e 13 horas") (dono, 2026-10-12, depois da 0.11.6). O treinador universal ativo aparece como um círculo **ao lado do médico e do advogado** (não na linha dos treinos, para não estragar o quadro).


## 21. Avisos do pré-jogo: banco, onze e especialistas

*Fonte: o dono, 2026-10-13, depois de ver o empate em que um suplente fraco entrou por lesão. O bot **só avisa**: o onze, o banco e a tática são do dono.*

Na checklist do cartão, o passo fica **amarelo** quando o jogo o dá como feito mas algo está fora da regra, e o **hover diz o quê**. Um passo que o jogo não dá como feito (por ex. onze com menos de 11, posição sem suplente) continua sem verde, como já estava.

**Banco** (o jogo põe a entrar, numa lesão, o 1.º suplente da posição na ordem do banco):
- **Lugares do banco por posição** (dono, 2026-10-16; visto nos 3 clubes): **12 GR, 13 DEF, 14 MED, 15 ATA, 16 DEF, 17 MED, 18 ATA**. Um jogador num lugar de outra posição é dito como tal: "Tens um defesa a suplente do ataque: Akanni 51". Pode ser de propósito (no FC Van, sem avançados para o banco nem à venda, o dono pôs lá um defesa); o passo fica amarelo, com esta frase.
- **Ordem dentro da posição:** nos lugares dessa posição, um suplente com rating pior à frente de um melhor (ex.: "Akanni 51 entra antes de Ndicka 107"). Quem está num lugar de outra posição não entra nesta comparação. Avisa **sempre**, mesmo que o melhor esteja cansado: na lesão entra quem está à frente.
- **Suplente melhor do que um titular** da mesma posição (ex.: "Marmoush 110 no banco, Diomande 102 a jogar"). **Não avisa se o suplente estiver cansado** (condição a amarelo, §16): está no banco de propósito.
  - **Só contra titulares da mesma posição específica** (dono, 2026-10-14): um PL só com o PL, um extremo só com os extremos. O jogo diz que "os jogadores rendem mais na sua posição específica" (o ponto "Posiciona os jogadores" da checklist fica por fazer com um jogador fora dela), embora as barras de força do onze não mudem com a troca. A **ordem** do banco continua pela posição geral (é assim que o jogo escolhe numa lesão).
- Rating = o principal da posição (ATA ataque, MED overall, DEF e GR defesa; confirmado, §4). Lesionados e castigados não contam.

**Onze (tática):**
- **Desarme vs árbitro do próximo jogo**, pela tabela do §3 com o que o dono aceita.
- **Formação** (§1): antes da análise só aceita **4-3-3 A**; depois da análise, com o adversário mais forte (qualquer margem, com bónus e casa, §1) pede **5 defesas** e aceita qualquer uma (5-3-2, 5-2-3, 5-4-1; D-049). O 4-3-3 B fica amarelo (o dono pode experimentá-lo na mesma).

**Posições** (dono, 2026-10-14): o jogo conta quantos titulares estão no lugar da sua posição específica (9/11 = 2 fora). O hover diz **quem**: "Messi (ED) a jogar a PL". O mapa de cada lugar de cada formação vem do código do próprio jogo (`theory/lineup.places`). Nomes: GR, DE, DC, DD, MDC, MC, MO, ME, MD, EE, PL, ED.

**Especialistas:** como já estava (D-042), amarelo fora da regra (§4); o hover passa a dizer que papel está errado e quem a regra pede.

**Treino secreto e estágio na janela** (dono, 2026-10-14): por baixo dos 8 passos, no fim da lista, com os ícones do próprio jogo (o escudo com cadeado e a tenda). **Marcado** para o próximo jogo: texto **verde** e ícone a cores com um anel verde. **Não marcado**: texto **cinzento** e ícone a cinzento. Sem jogo nesta jornada (o jogo não deixa marcar): igual a não marcado, e o hover diz porquê. Só mostra: comprar continua a ser decisão do dono (§6).

## 22. Experiência do treinador (XP, `skillRating`)

*Fonte: o dono, 2026-10-17 ("estou stuck nos 397-398k, não entendo porque não subo"). Só registo para estudar; o bot não muda nada por causa disto. Factos em `DISCOVERY.md` §3.*

- **O que se regista:** depois de cada jornada, uma linha por jogo do dono (liga ou taça) em `logs/<PC>/xp/`: resultado, adversário humano (com o rating) ou CPU, o rating total da conta, o saldo nessa liga (`leagueSkillRating`) e quanto mudaram desde a leitura anterior, os bónus da jornada e o nível (falta para o seguinte). `osmbot xp` mostra a tabela e a média da variação por resultado e tipo de adversário.
- **[S]** A variação de um jogo é a do saldo **dessa liga** (o total mistura as ligas). Só conta para as médias quando a leitura anterior foi a jornada anterior (`jornadas` 1).
- **[S]** Os amigáveis não contam para o rating (não se registam).
- **[?]** Como o jogo calcula o rating (quanto dá uma vitória, quanto tira uma derrota, se depende do rating do adversário): sem fonte pública; o registo é para o descobrir.

