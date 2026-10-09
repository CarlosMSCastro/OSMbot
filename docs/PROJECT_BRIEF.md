# Project Brief

*Última atualização: 2026-10-08*

## Objetivo

**Poupar tempo ao dono automatizando tarefas repetitivas** no Online Soccer Manager (D-010). Estado em 0.9.1 (o bot corre numa janela com ícone junto ao relógio, D-024):

| # | Automação | Estado |
|---|---|---|
| 1 | **Treinos**: recolher e voltar a pôr a treinar quando acabam (política em `THEORY.md` §5) | **Feito e em uso** (`osmbot ativo`) |
| 2 | **Vídeos da loja** (1 boss coin cada, até 9 por hora): pagam os amigáveis (4 boss coins cada) | **Feito** |
| 3 | **Vídeos de treino** (−2h cada, 4 por 3h): o treino acaba mais cedo e o ciclo volta a treinar mais cedo; regra "uniformizar"; nunca salta janelas (D-021) | **Feito** |
| 4 | **Vídeos de dinheiro** (3 por dia: ~300k, ~600k, 3 boss coins) | **Feito** (no clube com mais poupança) |
| 5 | **Aviso de slots de venda livres** (4 normalmente, 6 em eventos) | **Feito** (janela, consola e registo) |
| 6 | **Estádio**: começar a melhoria seguinte quando há dinheiro (`THEORY.md` §15) | **Feito** |
| 7 | **Patrocinadores**: a melhor proposta em cada espaço livre (`THEORY.md` §15) | **Feito** |
| 8 | **Recompensas diárias**: início de sessão, 3 missões, prémio do dia e vídeos acumulados; ficam no inventário, nunca se usam itens (`THEORY.md` §17, D-020) | **Feito** (0.8.0; a validar em real) |
| 9 | **Aviso de condição física** dos titulares (`THEORY.md` §16) | **Feito** (quadro) |
| 10 | Transferências automáticas | **Próxima grande funcionalidade, depois do 1.0** (dono, 2026-10-09): o dono vai dar a teoria de gestão de plantel primeiro; escritas novas pedem OK |
| 11 | Aviso de jogadores novos "SALE" no mercado (`THEORY.md` §7.7) | Por fazer |
| 12a | **Amigável e análise do adversário**: 4 h antes de cada jogo, se o dono ainda não os fez; amigável contra qualquer clube, analista ao próximo adversário (`THEORY.md` §6, D-025) | **Feito** (a validar em real) |
| 12b | **Médico e advogado**: lesionados e suspensos tratados e levantados sozinhos (`THEORY.md` §18) | **Feito** (0.9.3; a validar em real) |
| 12 | **Amigáveis em quantidade** com as boss coins dos vídeos (~25 por equipa por jornada, `THEORY.md` §6) | **Posta de lado** (dono, 2026-10-09): 10 amigáveis (40 coins) subiram só ~1,5–2 M o valor do plantel; não compensa |
| 13 | **Preço máximo de venda dos jogadores caros**: estudar no histórico de transferências até onde se consegue vender (dono, 2026-10-09) | **A recolher dados** (D-029): o bot guarda as transferências das ligas 1 vez por dia; até ~70 M€ de preço máximo vende-se ao máximo; acima de 100 M€ ainda não há vendas para estudar |
| 14 | **Quanto melhora a equipa com os amigáveis**: medir ao certo e em média o ganho por amigável, para decidir subir o número por equipa (liga-se ao 12; dono, 2026-10-09) | **Posta de lado** com o 12 (dono, 2026-10-09: o ganho medido à mão não compensa) |

Os vídeos têm limites impostos pelo servidor (detalhe em `THEORY.md` §12); o bot respeita-os sempre, salta algumas janelas da **loja** de propósito (os de treino e de dinheiro vêem-se sempre, D-021) e nunca forja a recompensa (D-012, regra 8).

Fora do alcance: táticas. O dono aplica a sua teoria de jogo ele mesmo; está registada em `THEORY.md` mas não se automatiza.

**Consequência:** é automação com escrita na conta (A3/A4 em `OPTIONS.md`), o cenário de maior risco face aos ToS, na **conta principal** do dono (D-004). O repo é público (D-016) e por isso não leva nomes de clubes, ligas, jogadores nem segredos.

## Critérios de sucesso

- [x] Alcance escolhido (D-002) e postura de risco definida (D-004).
- [x] Forma como o jogo comunica verificada com o dono presente (`DISCOVERY.md`).
- [x] Stack escolhida: Python (D-001); Firefox/Playwright só para login e vídeos, HTTP para o resto.
- [x] O bot recolhe e treina sozinho, vê vídeos dentro dos limites do jogo, trata do estádio, dos patrocinadores, das recompensas diárias e, 4 h antes de cada jogo, do amigável e da análise do adversário.
- [x] Funciona em Windows sem instalar o ambiente de desenvolvimento (D-016).
- [ ] Corre vários dias seguidos sem intervenção (por validar).
- [x] Funciona no PC da empresa e no pessoal, instalado (verificado pelo dono, 2026-10-09).

## Critérios do 1.0

*Proposta do Claude, aceite pelo dono em 2026-10-09. O 1.0 não pede funções novas: pede que o que existe esteja provado em uso real.*

- [ ] **Tudo o que escreve na conta foi visto em real**, nenhum pedido "por analogia" ativo: levantar o médico (corrigido), pôr e levantar o advogado (precisa de um suspenso de 2+ jogos), levantar o analista, amigável e análise 4 h antes, recompensas diárias, deteção de vendas.
- [x] **Nunca repete um pedido que o jogo recusou** (D-032, 0.9.6; falta ver em real).
- [ ] **7 dias seguidos num PC** sem intervenção e sem erros novos nos logs.
- [ ] Quando a sessão expira, o aviso é claro e o bot volta a trabalhar depois do login.
- [x] Instala e funciona noutros PCs (pessoal e fábrica, 2026-10-09).

**Fora do 1.0** (dono, 2026-10-09): transferências automáticas (próxima grande funcionalidade); versão para **Mac** instalada à mão, sem App Store (mais à frente); amigáveis em quantidade (postos de lado); README para o público (só se um dia houver uma versão para distribuir); mais traduções (vêm a seguir).

## Quem

- Dono do projeto: o autor do repositório (contactos no perfil do GitHub). Git e GitHub são dele (regra 9 do `CLAUDE.md`).
- Uso pessoal (D-002), com repositório público e sem licença (D-007).
