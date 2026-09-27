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

## Postura de risco — **por decidir (D-004)**

O Claude não assume nenhuma. Antes de qualquer contacto com o jogo real, o utilizador confirma o nível de risco que aceita e em que conta.

## Segredos (obrigatório, repo público)

Nunca versionar: passwords, cookies, tokens, `localStorage`/`sessionStorage`, dumps do StorageDump, ficheiros HAR com sessão, `.env*`, bases de dados com dados de conta (`*.db`). O `.gitignore` já cobre os padrões comuns; **verificar `git status` antes de cada commit.**
