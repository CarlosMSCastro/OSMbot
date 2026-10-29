# Verificação da teoria nos registos

Rotina pedida pelo dono (2026-10-28): ver de tempos a tempos se alguma regra do `THEORY.md` deixou de fazer sentido face ao histórico real do bot. **De 7 em 7 dias** o Claude propõe correr a verificação no início de uma sessão e traz ao dono **só** o que "não bate" ou está "pronto a decidir"; o que bate fica registado aqui.

**Correr:** `python tools/verificar_teoria.py` (só lê `logs/*/jogos`, `logs/*/amigaveis` e `logs/*/xp`; nunca fala com o jogo). Código das medições: `src/osmbot/checks/theory.py` (puro, testado em `tests/test_checks.py`).

**Veredictos:** **bate** · **não bate** (levar ao dono) · **amostra curta** (ainda poucos jogos) · **pronto a decidir** (regra por definir, já com jogos que cheguem).

## Verificações automáticas

| Id | Regra (`THEORY.md`) | Como se mede | Mínimo | 2026-10-28 |
|---|---|---|---|---|
| `casa` | Casa vale ~5 % de força (§1, [S]) | Jogos de liga a ±15 %: reta resultado × vantagem de força; onde dá empate | 150 jogos | ~4,3 % (340) · **bate** |
| `12pc` | Claramente mais forte = > 12 % (D-074) | Derrotas do mais forte entre 5–12 % e acima de 12 % | 40 em cada | 22 % / 8 % (573) · **bate** |
| `433fora` | Fora, o 4-3-3 B e não o A (§1, [S] pouca amostra) | Pontos por jogo dos teus clubes fora, até 12 % mais fortes, B contra A | 10 em cada | B 3,00 (2), A 2,00 (4) · **amostra curta** |
| `cansaco` | Titular perde ~4 de condição por jogo (§16) | Titulares em duas jornadas seguidas do mesmo clube | 50 casos | −3,9 (238) · **bate** |
| `523fora` | Fora: 4-3-3 (a regra, §1) ou 5-2-3 (OSMPro OSMPROworld 2)? | Pontos por jogo das equipas de fora (todos os clubes das ligas) com forças a ±12 %, em 4-3-3 e em 5-2-3 | 15 de cada | 4-3-3 com amostra, 5-2-3 quase sem jogos · **amostra curta** |
| `451` | Contra mais forte: 5 defesas (a regra, §1) ou 4-5-1 / 4-2-3-1 (OSMPro OSMPROworld 3)? | Pontos por jogo de quem é mais de 3 % mais fraco (todos os clubes, casa e fora), com 5 defesas e com 4-5-1 / 4-2-3-1 | 15 de cada | 5 defesas 1,10 (21), 4-5-1 0,34 (59) · **bate** (a regra das 5 defesas sai melhor; voltar a ver com mais jogos) |
| `tempo` | 5 defesas contra mais forte: temporização 60–80 (OSMPro Táticas 12, a medir) | Pontos por jogo com 60–80 e abaixo de 60 | 8 em cada | 0,80 (5) / — (0) · **amostra curta** |
| `ritmo` | Temporização 60–80 qualquer que seja a força (§2; OSMPro Série 4: mais forte → mais rápido, mais fraco → mais lento) | Pontos por jogo com <60, 60–80 e >80, mais forte e mais fraco à parte, todas as formações | 8 em 60–80 e noutra banda, de cada lado | mais forte: 60–80 2,87 (30), >80 3,00 (7); mais fraco: 60–80 0,71 (7) · **amostra curta** |
| `especialistas` | Especialistas evoluem mais nos amigáveis? (OSMPro Série 6, palpite do autor, a medir) | Ganho de treino por amigável, especialistas contra os outros (quem tinha cada papel fica registado em cada amigável desde a versão a seguir à 0.14.7) | 30 especialistas | 0 · **amostra curta** |
| `xp` | XP do treinador (§22, só estudo): perder com humanos custa muito | Variação na liga por resultado e adversário (CPU, humano com mais / menos rating do que o dono), sem os prémios de fim de época (`logs/*/xp`, lidos uma jornada depois); quantas vitórias contra o CPU uma derrota com um humano apaga | 10 derrotas com humanos | derrota humano −706 (3), vitória CPU +23 (20): ~30 vitórias · **amostra curta** |
| `cantos` | Cantos ≠ livres (§4; dono, 2026-10-29: "os nossos resultados eram bons com a teoria antiga") | Pontos por jogo, golos e força dos teus jogos de liga em que o médio com mais ataque é também o dos livres: ele nos cantos (a regra antiga, jogos até 2026-10-27) ou outro médio (a nova, desde o jogo de 2026-10-29; os especialistas de cada jogo ficam registados desde a versão a seguir à 0.14.10) | 10 em cada | antiga 2,54, 2,6 golos, força +22 % (28); nova 0 jogos · **amostra curta** |
| `contra` | 4-3-3 contra contra-ataque (OSMPro Táticas 7, a medir) | Pontos por jogo com o estilo do adversário lido no analista (desde a 0.14.6) | 10 jogos | 0 jogos · **amostra curta** |

## Lembretes com data

| Quando | O quê |
|---|---|
| julho–agosto (todos os anos; próxima ~2027-07) | Atualização anual das ligas (`THEORY.md` §19): ver nos registos dos jogos (`logs/*/jogos`) quem dos plantéis do dono mudou de nota e de valor sem treino, e quanto |

## Por automatizar (medíveis com os registos que já existem)

| Regra | Registo |
|---|---|
| Venda a 100 % do máximo até 150 M, 75 % acima (D-071, [S] amostras pequenas) | `transferencias/` |
| Campo de treinos +10 / +25 / +50 % na previsão (§5) | `treinos/` |
| Treino crítico ~+10 pontos em média; idade só ajuda abaixo de 85 (§5) | `treinos/` |
| Vantagem de casa pelo nível do campo do estádio (§1, nota "para mais tarde") | `jogos/` |
| 4-4-2 B / 3 defesas quando falta um lado (D-072): pontos por jogo | `jogos/` |
| 4 amigáveis por jogo e o ganho de cada um (§6) | `amigaveis/` |
| Desarme pelo árbitro (§3): cartões e resultado por rigor | `jogos/` |
| 4-3-3 contra contra-ataque e o que resulta contra cada estilo, na liga toda (com os relatórios do analista) | `analista/` + `jogos/` |
| In Form: bom negócio? (preço face ao valor, rapidez de venda; o bónus desaparece depois da compra?) (OSMPro Atualizações 2) | `transferencias/` (`raridade`, desde a versão a seguir à 0.14.8) + `jogos/` |
| Trainingcamp Terror: o ganho cresce a cada amigável? (§6; só quando o evento aparecer) | `amigaveis/` |

## Não medíveis com os registos

Escolhas do dono sem número (ordem do estádio, especialistas, posições), suposições sobre o próprio jogo que só se veem ao observar um pedido (regra 7) e as que dependem de dados que o jogo não dá (táticas dos outros clubes, bónus do capitão).
