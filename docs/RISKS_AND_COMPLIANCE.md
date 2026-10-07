# Riscos e conformidade

*Fonte dos ToS: https://www.onlinesoccermanager.com/termsandconditions (lido em 2026-09-27). Reler antes de qualquer decisão — podem mudar.*

## O que os ToS dizem (citações)

- **Bots / software de terceiros:** *"a form of cheating, including without limitation the use or participation (directly or indirectly) in the use of cheats, exploits, bots, hacks, mods or any unauthorised third-party software"*
- **Scraping / APIs:** *"you will not use our APIs, or otherwise scrape, collect or use data from our Website for any reason without our express prior written authorisation"*
- **Sanções:** *"You may be warned, temporarily banned or permanently banned if we think that you have not followed the Rules or if we believe in our sole discretion that you have behaved inappropriately"*
- **Consequências:** remoção de itens virtuais, sem reembolso nem compensação.
- Nota: os ToS admitem que **eles** usam bots em certos jogos; isso não autoriza terceiros.

## Leitura prática

| Cenário | Conflito com ToS |
|---|---|
| A0 — offline, dados introduzidos à mão | Nenhum contacto com o serviço |
| A1/A2 — leitura automática | Sim: "scrape/collect data" sem autorização escrita |
| A3/A4 — ações automáticas | Sim, e é o caso mais claro de "bot" |

Consequência para o utilizador: **conta banida e itens/moedas perdidos.** Um repo dos encontrados (atuncer) avisa expressamente do bloqueio por excesso de pedidos.

## Mitigações possíveis (não eliminam o risco)

- Usar conta descartável para desenvolvimento.
- Volume baixo, sem paralelismo, respeitar rate limits.
- Pedir autorização escrita à Gamebasics (única via limpa para A1+).
- Se publicar no GitHub: disclaimer claro, sem incluir nada que facilite contornar deteção, sem credenciais.

**[R]** O OSM tem "device ban" (dispositivo banido fica bloqueado para contas novas no mesmo dispositivo) — ver `DISCOVERY.md` §5. Isto limita a mitigação "conta descartável": se for testada no mesmo PC/browser que a conta principal, o isolamento pode não ser total. Não confirmado se o OSM liga contas por IP/fingerprint além do device ban.

**[R] Precedente de junho 2026 (D-012, ver `DISCOVERY.md` §5):** contas banidas por **exceder o teto normal de vídeos/hora** via um bug, sanção mantida mesmo sem intenção maliciosa. **Isto é sobre exceder limites, não sobre automatizar dentro deles** — não é prova de que um bot que respeite os limites do jogo (ex.: 4 vídeos/hora, cooldown) seja detetado da mesma forma. Essa questão específica fica **[H] em aberto**: os ToS proíbem "bots" como categoria, independentemente de exceder limites, mas não há precedente conhecido de deteção nesse caso mais moderado.

**Mitigação proposta pelo dono para D-012:** em vez de tentar apanhar 100% das janelas de anúncio, capar a uma fração (ex. 60-70%, valor **[H]** por afinar) com timings aleatórios entre cliques, e correr só durante as horas em que o PC normalmente está ligado (não 24/7) — aproxima o padrão de um jogador muito dedicado em vez de disponibilidade perfeita, e evita precisar de servidor/Raspberry Pi dedicado. *(Afinado: 85% das janelas da loja; desde 2026-10-08 só a loja salta janelas, D-021.)*

## Postura de risco — **decidida (D-004, emendada)**

O dono aceita o risco de ban em A3 (treinos, transferências) e A4 (anúncios) **na conta principal**, sem conta descartável. O contacto com o jogo segue a regra 5 do `CLAUDE.md` por níveis (D-014): leitura livre; `recolher`/`treinar`, os vídeos e as recompensas diárias (D-020: só reclamam e guardam no inventário) autónomos só com o bot ativo; escritas novas (vender, comprar, outros) pedem OK sempre.

Medidas em vigor no código: nunca exceder os limites do jogo (lidos de `user/caps/actions/...`), saltar 15% das janelas dos vídeos da **loja** (os de treino e de dinheiro vêem-se sempre, D-021), pausas e despertares com aleatoriedade, nunca insistir: uma escrita falhada nos treinos volta a ser vista 10 min depois e o bot pára ao fim de 3 passagens seguidas com falhas; rede e vídeos com pausas cada vez maiores (D-019), nunca chamar `videos/watched` (é a página que o faz), nunca clicar em botões que gastam boss coins, nunca usar itens do inventário, só reclamar o prémio do dia de hoje (no máximo um por dia) e não reclamar o que ultrapassaria os limites do inventário.

## Publicação pública do repo e dos instaladores (D-016, 2026-10-05)

O dono escolheu repo **e** Release públicos, ciente dos riscos:

| Risco | Medida / estado |
|---|---|
| Identidade do dono ligada ao bot (nome no GitHub + clubes no jogo) | Nomes de clubes, ligas, jogadores e utilizadores de terceiros removidos de `docs/` e `tests/`. **O histórico do git já enviado ainda os contém** (2 commits): reescrevê-lo é decisão do dono |
| Deteção por popularidade (muitos a usar o mesmo padrão de pedidos) | Sem mitigação técnica; é o argumento principal contra um Release público |
| ToS proíbem bots; pedido de remoção do repo/Release | Aceite pelo dono; o aviso no `README.md` mantém-se |
| Arte do jogo (ícone) | O instalador usa um ícone original (`tools/make_icon.py`); o oficial fica só em `tools/local/` (ignorado pelo git) |
| Segredos | Varredura limpa (nenhum token, ID, email ou nome de manager); a sessão fica em `~/.osmbot`, fora do pacote |
| Registo do bot em `logs/` (D-022, 2026-10-08) | **Público e completo**: nomes dos clubes e jogadores do dono, nome de cada PC, horas a que o bot corre. Aceite pelo dono. Tokens e e-mails apagados antes de escrever (regra 6) |

## Segredos (obrigatório, repo público)

Nunca versionar: passwords, cookies, tokens, `localStorage`/`sessionStorage`, dumps do StorageDump, ficheiros HAR com sessão, `.env*`, bases de dados com dados de conta (`*.db`). O `.gitignore` já cobre os padrões comuns; **verificar `git status` antes de cada commit.**
