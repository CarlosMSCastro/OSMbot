# Teoria de jogo do dono

*Fonte: o dono, 2026-09-27 (2 rondas). Tratada como verdade do projeto; **não validada por nós** (o dono afirma resultados comprovados).*
*Regra: este ficheiro só muda quando o dono o disser. Não "otimizar" nem corrigir a teoria.*
*Implementação: `src/osmbot/theory/` e `src/osmbot/training/`. Pontos ainda por confirmar: **[?]**. Suposições nossas: **[S]**.*

## 1. Escolha de formação

| Formação | Meio-campo | Quando |
|---|---|---|
| **4-3-3 A** | Leva **MCO** (médio centro ofensivo) | Padrão quando a equipa é claramente mais forte (o dono começa aqui quando já desenvolveu o plantel). Na prática "meio indiferente, depende do plantel" |
| **4-3-3 B** | Leva **MCD** (médio centro defensivo) | **Rating parecido** com o do dono, ou **fora de casa em matchups equilibrados** |
| **5-3-2** | — | Adversário **mais forte** |

A tática só pesa realmente em matchups difíceis. A "força" compara o **rating da equipa** (o do dono vs. o do adversário).

Implementado em `choose_formation(my_rating, opp_rating, *, similar_margin=2)`:
mais forte → 5-3-2 · parecido → 4-3-3 B · mais fraco → 4-3-3 A.

- **`similar_margin` (resolvido, 2026-09-27):** **2 pontos**, para os dois lados. Dentro de ±2 o dono considera que "ainda pode jogar 433"; passado isso (adversário mais forte por mais de 2) joga 5-3-2.
- **"Fora de casa em matchups equilibrados" (resolvido):** não alarga a margem — o local do jogo continua a não entrar na conta. **Pouco relevante na prática:** o dono faz as táticas manualmente (não é para automatizar, ver §6 do histórico/cont. 6). Nuance dele: dentro da margem de ±2, se tiver um **bom MCD** disponível nesse jogo, prefere 4-3-3 B por causa do jogador, não por o adversário ser "parecido" — isto já estava coberto pela nota existente de que a escolha entre A/B "depende do plantel".
- **Rating da equipa (resolvido):** vem da **média do plantel de 0 a 100 em rating** que o jogo mostra **antes de cada jogo** (não é o preço). Ver §11. **[?]** O campo na API só se sabe observando o jogo.

**Confronto direto (dono, 2026-10-08):** um jogo contra um clube que está **a 1 ou 2 lugares** do do dono na classificação, acima ou abaixo. São os jogos que o dono gosta de ver ele próprio nas últimas horas (§6). O quadro marca-os com um símbolo de perigo (D-026).

## 2. Instruções por formação

| | **4-3-3** (A e B) | **5-3-2** |
|---|---|---|
| Fora de jogo (offside trap) | Não | Não |
| Marcação à zona | **Não** | Sim |
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

## 4. Especialistas (só entre os **titulares**)

| Papel | Regra |
|---|---|
| **Capitão** | O mais **velho**, independentemente do rating. Empate de idade → maior rating |
| **Penáltis** | **Avançado** com mais ataque |
| **Livres** | Qualquer titular com mais ataque |
| **Cantos** | **Médio** com mais ataque |

- "Ataque" = estatística de ataque do jogador (`statAtt` no API, segundo o prior art) **[?] confirmar o nome do campo quando observarmos o jogo**.
- "Rating" (no capitão e nos desempates) = *stat principal da posição* **[S]**: avançado→ataque, médio→overall, defesa e guarda-redes→defesa. Segue o prior art; confirmar.
- **[S]** Empates que a teoria não cobre resolvem-se por maior rating e depois menor id de jogador, para o resultado ser sempre o mesmo.
- Sem titular elegível (ex.: sem avançado) → o código devolve `None` e o chamador decide.

## 5. Política de treino

Como a política de transferências **roda o plantel inteiro** várias vezes, o dono treina quase sempre o **melhor jogador de cada posição**, exceto se tiver **30+ anos**.

Implementado em `plan_training` / `pick_trainee`:
- Melhor = maior *rating* da posição **[S]** (ver acima). Treinadores 1–4 são por posição (ATT, MID, DEF, GK).
- Exclui (confirmado pelo dono): lesionados, já em treino, **quem está na lista de transferências (nunca treinar)**, e **idade ≥ 30**: nesse caso não treina o melhor, treina outros.
- Se o melhor tem 30+, usa-se o melhor dos restantes (confirmado).
- **Exceção (dono, 2026-10-04): guarda-redes treinam sempre o melhor, independentemente da idade.** O limite de 30+ aplica-se só a jogadores de campo.
- **[S]** Jogadores com forecast ≤ 0 (previsão do servidor: nada a ganhar) também são excluídos, quando essa informação existe.
- **Treinador universal (5): fora de âmbito.** O dono não o usa por padrão: só ganha um às vezes e usa-o situacionalmente. Não automatizar.

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
- **Amigáveis em quantidade (dono, 2026-10-08; ideia, não é para construir já):**
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
  - Se o **preço máximo** do jogador for **acima de 100 M€**, pede só **75% do seu valor**.
  - Se for **abaixo de 100 M€**, pede **SEMPRE o máximo**, por cada jogador.
- **O jogo acaba por vender os jogadores a bots, independentemente do preço** (afirmação do dono). Por isso pedir o máximo não atrasa a venda.
- **Os 75% são do preço máximo permitido** (não do valor de mercado). Exemplo do dono: o preço máximo do Jogador 1 é **111 M€** (o dono foi ver ao jogo), por isso pediria 75% disso ≈ **83,25 M€**.
- **Motivo (experiência do dono):** acima de 100 M€ fica **muito mais difícil vender pelo preço máximo**.
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
- **Automação desejada pelo dono** (não urgente): ser **notificado quando aparecem jogadores novos** na lista de transferências, para poder comprar a tempo. Ver `PROJECT_BRIEF.md`.
- **Horas / frequência de renovação da lista:** o dono **não sabe** (sabe que há horas em que aparecem novos). Só se descobre observando o mercado.
- **Alertar sobre (dono):** jogadores **"SALE"** e de **posições de que precisa**, entendendo por "precisa" as posições com **ratings abaixo da média no 11 inicial**.
- **Forma do alerta (confirmada pelo dono):** é um **aviso** para ele ir **espreitar**; a decisão de comprar é dele. Exemplo dele: *"Há 5 jogadores com tag "SALE" novos! Tens um DC de 79 no plantel, e existem DC's com mais rating à venda!"*
  - Ou seja: (1) quantos "SALE" novos apareceram; (2) para as posições em que o plantel tem um titular fraco, compara o rating dele com os "SALE" disponíveis nessa posição e diz se há melhores.
- **Horas certas:** mais tarde, com análise de dados, quando o dono souber a hora ao certo; por agora vai verificando "mais ou menos".
- **Titular "fraco" (resolvido, 2026-09-27):** **ambos os critérios contam** — é "fraco" quem for o **mais baixo da sua posição** entre os titulares, **ou** quem estiver **abaixo da média do 11** (não precisa de ser os dois ao mesmo tempo).

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
- Consequência (nossa): a 2% por dia, dinheiro nos fundos do clube "custa" 2% por dia em juro perdido (50 M parados = 1 M/dia). Reforça o palpite do dono sobre o jogador fraco (§7.8): dinheiro preso num suplente valioso também não rende juro.

## 14. Notas de implementação (nossas)

- Tudo é **determinístico** → funções puras `(estado do jogo) → decisão`, testáveis sem tocar no jogo (44 testes).
- Os especialistas mudam sempre que o plantel muda (compras, vendas, lesões, aniversários) → boa candidata a automatizar mesmo com tática manual.
- Os endpoints para **ler/escrever** tática e especialistas são **desconhecidos** (o prior art só viu chaves `TeamTactic_{liga}_{equipa}` no localStorage). Ver `PRIOR_ART.md` §"Por verificar".

## 15. Estádio e patrocinadores

*Fonte: o dono, 2026-10-07.*

**Estádio**
- Não há "recolher": uma melhoria acaba e a seguinte **põe-se a correr**, nada mais.
- **Ordem das partes:** campo de treinos → campo → capacidade.
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

## 17. Recompensas diárias: início de sessão, missões e vídeos acumulados

*Fonte: o dono, 2026-10-07. Pedidos observados com `inspect-writes` (`DISCOVERY.md` §3).*

**Início de sessão** (uma vez por dia, quando `user/dailylogin` diz `isClaimable`)
- Reclamar. O site gasta a recompensa logo na carteira certa; o bot faz o mesmo: **energia** → carteira de energia; **boss coins** → carteira de boss coins (o dono: "vão para a carteira, não há nada a ver").
- Qualquer outra recompensa (p. ex. o saco do dia 21): reclamar e **deixar no inventário**, sem gastar. **[S]** O pedido que a gasta nunca foi observado.

**Missões**
- As **3 missões diárias** (as que têm `order`) reclamam-se quando o progresso chega ao objetivo (`threshold`, do catálogo `missions`). O bot já treina jogadores, por isso são as que se cumprem sozinhas.
- Depois de reclamar as 3, abre-se a **recompensa do dia**: a missão sem `order` cujo `sourceType` é **o dia de hoje** da semana (calculado a partir de `endDateTime`: semana de 7 dias, que mudam às 04:00 UTC). As dos dias seguintes também aparecem na lista, mas **nunca se reclamam antes do dia delas**; no máximo uma por dia. O jogo pergunta "guardar" ou "usar já": o bot escolhe **sempre guardar**, ou seja, reclama e **nunca gasta** o prémio (fica no inventário). Se o jogo recusar o pedido, o bot não insiste nesse prémio até ser reiniciado.
- Só se reclama o que o próprio quadro de missões do jogo mostra como disponível.

**Vídeos acumulados (troca de posição)**
- A cada 10 vídeos (contador `RewardedVideoCounterPositionModifier`), quando `isClaimable`, reclamar: o item ("Switch") vai para o **inventário** e **não se usa**. O contador é alimentado pelos vídeos que o bot já vê.

**Limites do jogo (regra geral)**
- O inventário tem um limite por item (`inventoryLimit`, catálogos `actionrewards` e `rewards`). O bot **não reclama** se o item ficasse acima do limite.
- Nunca se usam os itens do inventário (isso exige escolhas: jogador, posição...). É decisão do dono.
- O bot respeita o jogo: sem pedidos repetidos para o que o jogo recusou.

## 18. Médico e advogado

*Fonte: o dono, 2026-10-09. Pedidos em `DISCOVERY.md` §3 (médico observado; advogado e levantamentos por analogia, aceite pelo dono).*

- **De graça**, com um timer de 8 h; no fim **levanta-se** (como um treino). **Sem vídeo** para encurtar no PC.
- **Médico:** **todos** os lesionados (onze, banco ou fora), **logo** que se lesionam. Pode usar-se **várias vezes por jornada** (às vezes tira 1 jogo, às vezes 4). Com 2 lesionados ao mesmo tempo, tenta os dois; se o jogo só deixar 1, o outro espera.
- **Advogado:** a mesma lógica para os suspensos, mas **só 1 vez por jornada** por jogador.
- Uma falha aqui nunca encrava as outras tarefas do bot; o quadro mostra a mudança logo a seguir (D-026).
