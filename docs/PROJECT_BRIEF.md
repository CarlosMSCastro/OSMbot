# Project Brief

*Última atualização: 2026-10-13*

## Objetivo

**Poupar tempo ao dono automatizando tarefas repetitivas** no Online Soccer Manager (D-010). Estado em 0.9.1 (o bot corre numa janela com ícone junto ao relógio, D-024):

| # | Automação | Estado |
|---|---|---|
| 1 | **Treinos**: recolher e voltar a pôr a treinar quando acabam (política em `THEORY.md` §5; rotação entre titulares desde a 0.11.0, D-035; desempate pela previsão do jogo e treinos vistos noutro PC desde a 0.11.3, D-037) | **Feito e em uso** (`osmbot ativo`) |
| 2 | **Vídeos da loja** (1 boss coin cada, até 9 por hora): pagam os amigáveis (4 boss coins cada) | **Feito** |
| 3 | **Vídeos de treino** (−2h cada, 4 por 3h): o treino acaba mais cedo e o ciclo volta a treinar mais cedo; regra "uniformizar"; nunca salta janelas (D-021) | **Feito** |
| 4 | **Vídeos de dinheiro** (3 por dia: ~300k, ~600k, 3 boss coins) | **Feito** (no clube com mais poupança) |
| 5 | **Aviso de slots de venda livres** (4 normalmente, 6 em eventos) | **Feito** (janela, consola e registo) |
| 6 | **Estádio**: começar a melhoria seguinte quando há dinheiro (`THEORY.md` §15) | **Feito** |
| 7 | **Patrocinadores**: a melhor proposta em cada espaço livre (`THEORY.md` §15) | **Feito** |
| 8 | **Recompensas diárias**: início de sessão, 3 missões, prémio do dia e vídeos acumulados; ficam no inventário; só se usam os itens que vão expirar, 4 h antes (`THEORY.md` §17 e §20, D-020, D-039) | **Feito** (0.8.0; visto em real: início de sessão, missões e prémio do dia) |
| 8a | **Poupança**: depositar tudo 5 min antes de cada jogo (`THEORY.md` §13, D-035) | **Feito** (0.11.0, por ver em real; 0.12.0: também em cada dia da pré-época, D-054) |
| 9 | **Aviso de condição física** dos titulares (`THEORY.md` §16) | **Feito** (quadro; desde a 0.11.8 também "sem suplente" com opções "SALE" ao passar o rato, D-043) |
| 9c | **Força das equipas e objetivo da época na janela**: força num círculo (a do adversário depois da análise), os 3 primeiros com os pontos, o objetivo e "Campeões" (`THEORY.md` §19, D-043) | **Feito** (0.11.8; força conferida com o jogo em 3 clubes) |
| 9a | **Especialistas** pela regra do dono antes de cada jogo (`THEORY.md` §4, D-042) | **Feito** (0.11.7; 1.ª gravação vista em real) |
| 9d | **Avisos do pré-jogo**: banco fora de ordem ou com suplente melhor do que um titular, desarme que não serve ao árbitro, formação fora da regra, especialistas errados (`THEORY.md` §21, D-046) | **Feito** (0.11.9; só avisa; 0.11.10: banco pela posição específica e hover de quem está fora de posição, D-047; 0.11.12: formação com 5 defesas contra quem for mais forte, contando os bónus do jogo e a casa, D-049, D-050; 0.11.13: 4-4-2 B aceite sem extremos em forma, Agressivo aceite com árbitro muito brando, D-052) |
| 9e | **Registo dos jogos reais** de todos os clubes (onze, notas, eventos, força do jogo) e a época inteira (D-044) | **Feito** (0.11.9; base da análise de 272 jogos que mudou a regra da formação, D-045) |
| 9b | **Registo dos jogos** das ligas do dono, para estudar (D-041) | **Feito** (0.11.7; histórico da época gravado; táticas dos outros clubes o jogo não dá) |
| 10 | Transferências automáticas | **Próxima grande funcionalidade, depois do 1.0** (dono, 2026-10-09): o dono vai dar a teoria de gestão de plantel primeiro; escritas novas pedem OK |
| 11 | Aviso de jogadores novos "SALE" no mercado (`THEORY.md` §7.7) | **Feito** (0.11.14, D-053): no cartão do clube, os 3 SALE que cabem no dinheiro pelo lucro de revenda, marcados reforço/pechincha. Desde a 0.11.3 (D-037) cada "SALE" que aparece e sai fica em `logs/<PC>/transferencias/sale/` |
| 12a | **Amigáveis e análise do adversário**: o que o dono ainda não fez; **4 amigáveis** (dono, 2026-10-11) contra quaisquer clubes, **distribuídos pelo dia** (16/12/8/4 h antes do jogo, 0.11.2, D-036); analista ao próximo adversário nas últimas 4 h, **levantado logo que acaba** (`THEORY.md` §6, D-025, D-036) | **Feito** (visto em real em 2026-10-11: amigável, enviar e levantar o analista; 0.12.0: 4 amigáveis em cada dia da pré-época, D-054) |
| 12b | **Médico e advogado**: lesionados e suspensos tratados e levantados sozinhos (`THEORY.md` §18) | **Feito** (0.9.3; médico visto em real a pôr e a levantar, 2026-10-09–11; advogado por ver, precisa de um suspenso de 2+ jogos) |
| 12 | **Amigáveis em quantidade** com as boss coins dos vídeos (~25 por equipa por jornada, `THEORY.md` §6) | **Posta de lado** (dono, 2026-10-09): 10 amigáveis (40 coins) subiram só ~1,5–2 M o valor do plantel; não compensa |
| 13 | **Preço máximo de venda dos jogadores caros**: estudar no histórico de transferências até onde se consegue vender (dono, 2026-10-09) | **A recolher dados** (D-029): o bot guarda as transferências das ligas 1 vez por dia; numa liga já se vendeu **ao máximo até ~167 M€**; a 75 % até ~155 M€; as vendas chegam em lotes (numa liga a cada ~2 h) e cada lote leva só uma parte da lista, sem ser pelo preço (2026-10-11, `DISCOVERY.md` §3). Desde a 0.10.3 o registo do bot guarda, para cada listagem do dono, a hora em que foi posta à venda e, quando vende, quanto demorou e a percentagem do máximo; desde a 0.10.4 regista também cada passagem do motor de transferências em cada liga (D-034) |
| 8b | **Inventário**: usar os itens que vão expirar (treinadores universais, sacos) e avisar 24 h antes (`THEORY.md` §20, D-039) | **Feito** (0.11.6; visto em real: ativar o treinador universal e treinar com ele; abrir um saco ainda por ver) |
| 13a | **Calendário de eventos**: o do mês, lido do fórum, e o evento em curso, visto nas definições do jogo (D-038) | **Feito** (0.11.4; lido em real: os 10 eventos de outubro; na janela, com o calendário do mês, desde a 0.11.5; 8 amigáveis no Intense Friendlies desde a 0.11.7, D-040) |
| 14 | **Quanto melhora a equipa com os amigáveis**: medir ao certo e em média o ganho por amigável, para decidir subir o número por equipa (liga-se ao 12; dono, 2026-10-09) | **Posta de lado** com o 12 (dono, 2026-10-09: o ganho medido à mão não compensa) |

Os vídeos têm limites impostos pelo servidor (detalhe em `THEORY.md` §12); o bot respeita-os sempre, salta algumas janelas da **loja** de propósito (os de treino e de dinheiro vêem-se sempre, D-021) e nunca forja a recompensa (D-012, regra 8).

Fora do alcance: táticas. O dono aplica a sua teoria de jogo ele mesmo; está registada em `THEORY.md` mas não se automatiza.

**Consequência:** é automação com escrita na conta (A3/A4 em `OPTIONS.md`), o cenário de maior risco face aos ToS, na **conta principal** do dono (D-004). O repo é público (D-016) e por isso não leva nomes de clubes, ligas, jogadores nem segredos.

## Critérios de sucesso

- [x] Alcance escolhido (D-002) e postura de risco definida (D-004).
- [x] Forma como o jogo comunica verificada com o dono presente (`DISCOVERY.md`).
- [x] Stack escolhida: Python (D-001); Firefox/Playwright só para login e vídeos, HTTP para o resto.
- [x] O bot recolhe e treina sozinho, vê vídeos dentro dos limites do jogo, trata do estádio, dos patrocinadores, das recompensas diárias e, antes de cada jogo, dos amigáveis (ao longo do dia) e da análise do adversário (4 h antes).
- [x] Funciona em Windows sem instalar o ambiente de desenvolvimento (D-016).
- [ ] Corre vários dias seguidos sem intervenção (por validar).
- [x] Funciona no PC da empresa e no pessoal, instalado (verificado pelo dono, 2026-10-09).

## Critérios do 1.0

*Proposta do Claude, aceite pelo dono em 2026-10-09. O 1.0 não pede funções novas: pede que o que existe esteja provado em uso real.*

- [ ] **Tudo o que escreve na conta foi visto em real**, nenhum pedido "por analogia" ativo: pôr e levantar o advogado (precisa de um suspenso de 2+ jogos). Vistos nos logs (2026-10-11): médico pôr ×3 e levantar ×2 (DESKTOP-KAM70RR, 10–11/10), levantar o analista ×2, enviar o analista ×1 (forçado a pedido do dono, 11/10), amigável ×1, início de sessão e missões.
- [x] **Nunca repete um pedido que o jogo recusou** (D-032, 0.9.6; falta ver em real).
- [ ] **7 dias seguidos num PC** sem intervenção e sem erros novos nos logs.
- [ ] Quando a sessão expira, o aviso é claro e o bot volta a trabalhar depois do login.
- [x] Instala e funciona noutros PCs (pessoal e fábrica, 2026-10-09).

**Fora do 1.0** (dono, 2026-10-09): transferências automáticas (próxima grande funcionalidade); versão para **Mac** instalada à mão, sem App Store (mais à frente); amigáveis em quantidade (postos de lado); README para o público (só se um dia houver uma versão para distribuir); mais traduções (vêm a seguir).

## Quem

- Dono do projeto: o autor do repositório (contactos no perfil do GitHub). Git e GitHub são dele (regra 9 do `CLAUDE.md`).
- Uso pessoal (D-002), com repositório público e sem licença (D-007).
