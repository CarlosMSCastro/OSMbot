# Project Brief

*Última atualização: 2026-10-06*

## Objetivo

**Poupar tempo ao dono automatizando tarefas repetitivas** no Online Soccer Manager (D-010). Estado em 0.5.0:

| # | Automação | Estado |
|---|---|---|
| 1 | **Treinos**: recolher e voltar a pôr a treinar quando acabam (política em `THEORY.md` §5) | **Feito e em uso** (`osmbot ativo`) |
| 2 | **Vídeos da loja** (1 boss coin cada, até 9 por hora): pagam os amigáveis (4 boss coins cada) | **Feito** |
| 3 | **Vídeos de treino** (−2h cada, 4 por 3h): o treino acaba mais cedo e o ciclo volta a treinar mais cedo; regra "uniformizar" | **Feito** |
| 4 | **Vídeos de dinheiro** (3 por dia: ~300k, ~600k, 3 boss coins) | Por fazer (fluxo já observado) |
| 5 | **Aviso de slots de venda livres** (4 normalmente, 6 em eventos) | **Feito** (consola e registo) |
| 6 | Transferências automáticas | Por especificar; escritas novas pedem OK |
| 7 | Aviso de jogadores novos "SALE" no mercado (`THEORY.md` §7.7) | Por fazer |

Os vídeos têm limites impostos pelo servidor (detalhe em `THEORY.md` §12); o bot respeita-os sempre, salta algumas janelas de propósito e nunca forja a recompensa (D-012, regra 8).

Fora do alcance: táticas. O dono aplica a sua teoria de jogo ele mesmo; está registada em `THEORY.md` mas não se automatiza.

**Consequência:** é automação com escrita na conta (A3/A4 em `OPTIONS.md`), o cenário de maior risco face aos ToS, na **conta principal** do dono (D-004). O repo é público (D-016) e por isso não leva nomes de clubes, ligas, jogadores nem segredos.

## Critérios de sucesso

- [x] Alcance escolhido (D-002) e postura de risco definida (D-004).
- [x] Forma como o jogo comunica verificada com o dono presente (`DISCOVERY.md`).
- [x] Stack escolhida: Python (D-001); Firefox/Playwright só para login e vídeos, HTTP para o resto.
- [x] O bot recolhe e treina sozinho, e vê vídeos dentro dos limites do jogo.
- [x] Funciona em Windows sem instalar o ambiente de desenvolvimento (D-016).
- [ ] Corre vários dias seguidos sem intervenção (por validar).
- [ ] Funciona no PC da empresa (por testar).

## Quem

- Dono do projeto: o autor do repositório (contactos no perfil do GitHub). Git e GitHub são dele (regra 9 do `CLAUDE.md`).
- Uso pessoal (D-002), com repositório público e sem licença (D-007).
