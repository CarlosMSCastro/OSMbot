# Verificação da teoria nos registos

Rotina pedida pelo dono (2026-10-28): ver de tempos a tempos se alguma regra do `THEORY.md` deixou de fazer sentido face ao histórico real do bot. **De 7 em 7 dias** o Claude propõe correr a verificação no início de uma sessão e traz ao dono **só** o que "não bate" ou está "pronto a decidir"; o que bate fica registado aqui.

**Correr:** `python tools/verificar_teoria.py` (só lê `logs/*/jogos`, `amigaveis`, `xp`, `analista` e as linhas "Venda:" dos `.log`; nunca fala com o jogo). Código das medições: `src/osmbot/checks/theory.py` (puro, testado em `tests/test_checks.py`).

**Veredictos:** **bate** · **não bate** (levar ao dono) · **amostra curta** (ainda poucos jogos) · **pronto a decidir** (regra por definir, já com jogos que cheguem).

## Verificações automáticas

| Id | Regra (`THEORY.md`) | Como se mede | Mínimo | 2026-10-28 |
|---|---|---|---|---|
| `casa` | Casa vale ~5 % de força (§1, [S]) | Jogos de liga a ±15 %: reta resultado × vantagem de força; onde dá empate | 150 jogos | ~4,3 % (340) · **bate** |
| `12pc` | Claramente mais forte = > 12 % (D-074) | Derrotas do mais forte entre 5–12 % e acima de 12 % | 40 em cada | 22 % / 8 % (573) · **bate** |
| `433fora` | Fora, o 4-3-3 B e não o A (§1, [S] pouca amostra) | Pontos por jogo dos teus clubes fora, até 12 % mais fortes, B contra A | 10 em cada | B 3,00 (2), A 2,00 (4) · **amostra curta** |
| `cansaco` | Titular perde ~4 de condição por jogo (§16) | Titulares em duas jornadas seguidas do mesmo clube | 50 casos | −3,9 (238) · **bate** |
| `523fora` | Fora: 4-3-3 (a regra, §1) ou 5-2-3 (OSMPro OSMPROworld 2)? | Pontos por jogo das equipas de fora (todos os clubes das ligas) com forças a ±12 %, em 4-3-3 e em 5-2-3 | 15 de cada | 4-3-3 com amostra, 5-2-3 quase sem jogos · **amostra curta** |
| `tabela` | A contra-tática do autor pela formação do adversário rende mais (OSMPro OSMPROworld 4)? | Pontos por jogo (todos os clubes, forças a ±12 %) de quem usou a contra-tática da tabela e de quem usou outra | 15 de cada | contra-tática 0,91 (66), outras 1,34 (440), sem acertar pelo campo · **pronto a decidir** (2026-10-30: fica o §1) |
| `vs523` | Contra 5-2-3, sendo mais forte: 4-3-3 A, B ou 5-3-2 (OSMPro OSMPROworld 4; dono, 2026-10-30)? | Pontos por jogo de quem é mais forte, todos os clubes | 8 no A e 8 no B | A 1,20 (5), B 2,40 (5), 5-3-2 sem jogos · **amostra curta** |
| `451` | Contra mais forte: 5 defesas (a regra, §1) ou 4-5-1 / 4-2-3-1 (OSMPro OSMPROworld 3)? | Pontos por jogo de quem é mais de 3 % mais fraco (todos os clubes, casa e fora), com 5 defesas e com 4-5-1 / 4-2-3-1 | 15 de cada | 5 defesas 1,10 (21), 4-5-1 0,34 (59) · **bate**; 2026-11-02: 1,12 (24), 0,32 (69), fica a regra |
| `tempo` | 5 defesas contra mais forte: temporização 60–80 (OSMPro Táticas 12, a medir) | Pontos por jogo com 60–80 e abaixo de 60 | 8 em cada | 0,80 (5) / — (0) · **amostra curta** |
| `ritmo` | Temporização 60–80 qualquer que seja a força (§2; OSMPro Série 4: mais forte → mais rápido, mais fraco → mais lento) | Pontos por jogo com <60, 60–80 e >80, mais forte e mais fraco à parte, todas as formações | 8 em 60–80 e noutra banda, de cada lado | mais forte: 60–80 2,87 (30), >80 3,00 (7); mais fraco: 60–80 0,71 (7) · **amostra curta** |
| `especialistas` | Especialistas evoluem mais nos amigáveis? (OSMPro Série 6, palpite do autor, a medir) | Ganho de treino por amigável, especialistas contra os outros (quem tinha cada papel fica registado em cada amigável desde a versão a seguir à 0.14.7) | 30 especialistas | 2026-11-02: especialistas +16,7 (80), os outros +20,8 (98) · sem ganho à vista, nada muda (os especialistas tendem a ser os melhores, que sobem menos) |
| `xp` | XP do treinador (§22, só estudo): perder com humanos custa muito | Variação na liga por resultado e adversário (CPU, humano com mais / menos rating do que o dono), sem os prémios de fim de época (`logs/*/xp`, lidos uma jornada depois); quantas vitórias contra o CPU uma derrota com um humano apaga | 10 derrotas com humanos | derrota humano −706 (3), vitória CPU +23 (20): ~30 vitórias · **amostra curta** |
| `cantos` | Cantos ≠ livres (§4; dono, 2026-10-29: "os nossos resultados eram bons com a teoria antiga") | Pontos por jogo, golos e força dos teus jogos de liga em que o médio com mais ataque é também o dos livres: ele nos cantos (a regra antiga, jogos até 2026-10-27) ou outro médio (a nova, desde o jogo de 2026-10-29; os especialistas de cada jogo ficam registados desde a versão a seguir à 0.14.10) | 10 em cada | antiga 2,54, 2,6 golos, força +22 % (28); nova 0 jogos · **amostra curta** |
| `armadilha` | 4-3-3 sem fora de jogo (D-094) | Pontos por jogo e golos sofridos dos teus 4-3-3 de liga sendo mais forte, sem e com armadilha (o lado "com" deixa de crescer) | 15 em cada | 2026-11-06: sem 2,94, 0,21 sofridos (34); com 2,39, 0,61 (23) · **bate** |
| `vs5def` | Pista (2026-11-06): contra 5 defesas rendemos menos? | Pontos por jogo dos teus clubes sendo mais fortes, contra 5 defesas e contra as outras, com a força média de cada grupo | 10 contra 5 defesas | 0,67 (3) / 2,89 (79) · **amostra curta** |
| `casanossa` | Pista (2026-11-06): os teus clubes rendem menos em casa? | Pontos por jogo em casa e fora sendo 0–25 % mais fortes, com a força média de cada lado | 15 em cada | casa 2,74, +16 % (19); fora 2,47, +12 % (17) · **pronto a decidir** (pelos pontos crus, não se vê pior em casa) |
| `extremo` | Pista (2026-11-06): desarme extremo rende mais? (liga toda) | Relatórios do analista ligados ao jogo seguinte de cada clube, forças a ±15 %: pontos por jogo em Extremo e nos outros, com o rigor médio dos árbitros | 30 em Extremo | 2,57, árbitro 3,6 (7) / 1,34, árbitro 3,1 (156) · **amostra curta** |
| `contra` | 4-3-3 contra contra-ataque (OSMPro Táticas 7, a medir) | Pontos por jogo com o estilo do adversário lido no analista (desde a 0.14.6) | 10 jogos | 0 jogos · **amostra curta** |
| `vermelhos` | Agressivo não rende mais e só arrisca vermelhos com árbitro rigoroso (§3; dono, 2026-11-02) | Vermelhos e pontos por jogo, dos teus clubes e dos outros da liga (desarme lido no analista), árbitro rigoroso (1–2) em Normal e em Agressivo/Extremo, forças a ±15 %; e os vermelhos com árbitro brando ou médio | 15 em cada | 2026-11-13: Normal 0,08 vermelhos/jogo, 1,46 pts (90); Agressivo/Extremo 0,33, 1,75 (12); brando 0,01 (193) · **amostra curta** (à mão, só os teus: Normal 6 em 21, Agressivo 6 em 14, pontos iguais) |
| `intense` | Intense Friendlies: 8 amigáveis rendem mais do que 4 (D-038) | Soma do ganho médio por jogador numa jornada completa (4 ou 8 amigáveis), e o ganho de cada amigável por ordem | 10 jornadas de cada | 2026-11-13: normal 66 (81), Intense 93 (4) · **amostra curta** (a favor, ~1,4×; à mão, com jornadas incompletas, ~2,9×) |
| `descida` | Cada amigável do dia rende menos do que o anterior (§6) | Ganho médio do 1.º e do 4.º amigável do dia, fora de eventos | 30 de cada | 2026-11-13: 24,9 (95) / 10,7 (94) · **bate** |
| `venda150` | Vender: 75 % do máximo só acima de 150 M (D-071) | Das linhas "Venda:" dos registos (sem repetidos entre PCs): mediana de horas acima de 150 M a 75 %, entre 100 e 150 M a 100 % e a 75 % | 5 acima de 150 M e 5 a 100 % | 2026-11-13: 17,8 h (1) / 14,5 h (9) / 31,4 h (3) · **amostra curta** |

**2026-11-03 (corrida, 744 jogos nos registos):** nada "não bate". `casa` 4,4 % (425) · `12pc` 21 % / 8 % (728) · `cansaco` −3,9 (374): batem. `451`, `tabela` e `especialistas` "pronto a decidir" já decididos (ficam as regras; números iguais: 1,12 / 0,34; 0,96 / 1,31; +16,8 / +20,1). Mexeram-se, ainda curtos: `cantos` regra nova 3,00 pts/jogo em 5 jogos (antiga 2,54 em 28); `433fora` B 2,50 (4) / A 2,00 (4); `xp` 6 derrotas com humanos (faltam 4). À mão, "100 % até 150 M, 75 % acima" (D-071): vendas do dono com máximo acima de 150 M só 1 (a 75 %, 18 h): **amostra curta**. Próxima: ~2026-11-10.

**2026-11-09 (corrida, 869 jogos nos registos):** **não bate:** `cantos`, com a regra nova (outro médio nos cantos) a 2,47 pts/jogo, 2,8 golos, força +38 % (17), contra a antiga a 2,54, 2,6 golos, força +22 % (28). A diferença de pontos é pequena (0,07), mas os jogos da regra nova foram contra equipas mais fracas. Levado ao dono. Batem: `casa` 5,0 % (499) · `12pc` 21 % / 7 % (869) · `cansaco` −3,9 (497) · `armadilha` sem 2,88, 0,27 sofridos (41); com 2,39, 0,61 (23). "Pronto a decidir" já decididos, com números parecidos: `451` 1,08 / 0,39 · `tabela` 0,96 / 1,30 · `especialistas` +18,2 / +19,2 · `casanossa` casa 2,64 (22), fora 2,47 (17). Mexeram-se, ainda curtos: `xp` com 9 derrotas com humanos (falta 1); `433fora` B 2,50 (4) / A 1,83 (6); `extremo` 2,44 (9) / 1,33 (209). À mão, D-071 (linhas "Venda:" dos registos, sem repetidos entre PCs): acima de 150 M de máximo continua só 1 venda (a 75 %, 17,8 h), por isso **amostra curta**. Entre 100 e 150 M, a 100 % desde a D-071: 6 vendas, mediana ~23 h (10,5–48 h); a 75 % em outubro: 5, mediana 20,8 h (4,7–73 h). Vende quase tão depressa, o que confirma o limiar dos 150 M. Próxima: ~2026-11-16.

**2026-11-13 (corrida extra a pedido do dono, 957 jogos nos registos):** **não bate (continua):** `cantos`, regra nova (outro médio nos cantos) 2,52 pts/jogo, 2,7 golos, força +34 % (25) contra a antiga 2,54, 2,6 golos, força +22 % (28); diferença de pontos 0,02, mas a nova joga contra equipas mais fracas (+34 % contra +22 %). Já passou o mínimo de 10 em cada lado. Batem: `casa` 5,4 % (538) · `12pc` 22 % / 7 % (957) · `cansaco` −3,9 (550) · `armadilha` sem 2,83, 0,30 sofridos (46); com 2,39, 0,61 (23) · `xp` (82; derrotas com humanos 9). "Pronto a decidir" já decididos, números parecidos: `451` 1,20 / 0,40 · `tabela` 1,00 / 1,30 · `especialistas` +18,6 / +19,7 · `casanossa` casa 2,67 (24), fora 2,37 (19). Ainda curtos: `433fora` B 2,50 (4) / A 1,57 (7); `vs523` A 1,50 (8) / B 2,40 (5); `extremo` 2,44 (9) / 1,33 (254); `contra` 3,00 (4); `vs5def` 4 jogos; `523fora` 5-2-3 7 jogos. Próxima: ~2026-11-16.

## Lembretes

**2026-11-13 (medições à mão, 1045 jogos únicos, 122 do dono, 448 amigáveis):** (1) **Vermelhos × desarme** (`THEORY.md` §2): árbitro rigor 1–2: Normal 6 vermelhos em 21 jogos (0,29/jogo), 2,33 pts; Agressivo 6 em 14 (0,43/jogo), 2,29 pts. Rigor 3–5: 0 vermelhos em 69 jogos. Bate com a regra: o Agressivo não rende mais e só arrisca com árbitro rigoroso. (2) **Intense Friendlies** (D-038): ganho médio por jogador, por amigável da jornada: normal 24,9 / 20,5 / 15,1 / 10,7 (soma ~71); Intense 31,7 / 38,9 / 36,9 / 33,8 / 16,2 / 15,2 / 19,4 / 14,2 (soma ~206; 6–8 jornadas por posição). Compensam (~2,9×). Por fazer como verificação automática. com data

| Quando | O quê |
|---|---|
| julho–agosto (todos os anos; próxima ~2027-07) | Atualização anual das ligas (`THEORY.md` §19): ver nos registos dos jogos (`logs/*/jogos`) quem dos plantéis do dono mudou de nota e de valor sem treino, e quanto |

## Por automatizar (medíveis com os registos que já existem)

| Regra | Registo |
|---|---|
| Venda a 100 % do máximo até 150 M, 75 % acima (D-071, [S] amostras pequenas) | `transferencias/` |
| Campo de treinos +10 / +25 / +50 % na previsão (§5) | `treinos/` |
| Treino crítico ~+10 pontos em média; idade só ajuda abaixo de 85 (§5) | `treinos/` |
| Vantagem de casa pelo nível do campo do estádio (§1, nota "para mais tarde"); e fora, com o relvado do adversário no nível 0, o 4-3-3 rende mais? (OSMPro Outros, ponto 2; dono, 2026-11-03: medir primeiro). 2026-11-03, forças a ±12 %: nível 0 1,90 pts/jogo (39), níveis 1–3 2,00 (7) · **amostra curta** | `jogos/` + `analista/` (`stadiumPitchBonus`) |
| 4-4-2 B / 3 defesas quando falta um lado (D-072): pontos por jogo | `jogos/` |
| 4-4-2 B do autor contra contra-ataque (D-079): pontos por jogo, quando houver jogos | `jogos/` |
| 4 amigáveis por jogo e o ganho de cada um (§6) | `amigaveis/` |
| Desarme pelo árbitro (§3, D-084): vermelhos e pontos por jogo em Normal com árbitro rigoroso, contra os 6 vermelhos em 15 jogos em Agressivo; Cuidadoso com árbitro muito rigoroso | `jogos/` |
| 4-3-3 contra contra-ataque e o que resulta contra cada estilo, na liga toda (com os relatórios do analista) | `analista/` + `jogos/` |
| In Form: bom negócio? (preço face ao valor, rapidez de venda; o bónus desaparece depois da compra?) (OSMPro Atualizações 2) | `transferencias/` (`raridade`, desde a versão a seguir à 0.14.8) + `jogos/` |
| Trainingcamp Terror: o ganho cresce a cada amigável? (§6; só quando o evento aparecer) | `amigaveis/` |

## Não medíveis com os registos

Escolhas do dono sem número (ordem do estádio, especialistas, posições), suposições sobre o próprio jogo que só se veem ao observar um pedido (regra 7) e as que dependem de dados que o jogo não dá (táticas dos outros clubes, bónus do capitão).
