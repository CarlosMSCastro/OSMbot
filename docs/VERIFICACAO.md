# Verificação da teoria nos registos

Rotina pedida pelo dono (2026-10-28): ver de tempos a tempos se alguma regra do `THEORY.md` deixou de fazer sentido face ao histórico real do bot. **De 7 em 7 dias** o Claude propõe correr a verificação no início de uma sessão e traz ao dono **só** o que "não bate" ou está "pronto a decidir"; o que bate fica registado aqui.

**Correr:** `python tools/verificar_teoria.py` (só lê `logs/*/jogos`; nunca fala com o jogo). Código das medições: `src/osmbot/checks/theory.py` (puro, testado em `tests/test_checks.py`).

**Veredictos:** **bate** · **não bate** (levar ao dono) · **amostra curta** (ainda poucos jogos) · **pronto a decidir** (regra por definir, já com jogos que cheguem).

## Verificações automáticas

| Id | Regra (`THEORY.md`) | Como se mede | Mínimo | 2026-10-28 |
|---|---|---|---|---|
| `casa` | Casa vale ~5 % de força (§1, [S]) | Jogos de liga a ±15 %: reta resultado × vantagem de força; onde dá empate | 150 jogos | ~4,3 % (340) · **bate** |
| `12pc` | Claramente mais forte = > 12 % (D-074) | Derrotas do mais forte entre 5–12 % e acima de 12 % | 40 em cada | 22 % / 8 % (573) · **bate** |
| `433fora` | Fora, o 4-3-3 B e não o A (§1, [S] pouca amostra) | Pontos por jogo dos teus clubes fora, até 12 % mais fortes, B contra A | 10 em cada | B 3,00 (2), A 2,00 (4) · **amostra curta** |
| `cansaco` | Titular perde ~4 de condição por jogo (§16) | Titulares em duas jornadas seguidas do mesmo clube | 50 casos | −3,9 (238) · **bate** |
| `tempo` | 5 defesas contra mais forte: temporização 60–80 (OSMPro Táticas 12, a medir) | Pontos por jogo com 60–80 e abaixo de 60 | 8 em cada | 0,80 (5) / — (0) · **amostra curta** |
| `contra` | 4-3-3 contra contra-ataque (OSMPro Táticas 7, a medir) | Pontos por jogo com o estilo do adversário lido no analista (desde a 0.14.6) | 10 jogos | 0 jogos · **amostra curta** |

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

## Não medíveis com os registos

Escolhas do dono sem número (ordem do estádio, especialistas, posições), suposições sobre o próprio jogo que só se veem ao observar um pedido (regra 7) e as que dependem de dados que o jogo não dá (táticas dos outros clubes, bónus do capitão).
