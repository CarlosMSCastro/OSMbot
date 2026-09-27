# Prior art — `nsozturk/osm-ad-bot`

*Análise de 2026-09-27, feita lendo o código (clone em scratchpad, fora do projeto). **Nada foi executado nem testado contra o jogo.** Tudo o que se refere à API é [R] (reportado pelo código/docs do autor) até verificarmos.*

## Estado do repo

- 22 commits, entre 2026-06-20 e **2026-08-23** (último há ~5 semanas). Ativo, mas **projeto de um só autor, pensado para macOS** (launchd, `run.sh`), com comentários em turco.
- 4 ficheiros de testes (não corridos por nós).
- **Sem ficheiro LICENSE** → por defeito, todos os direitos reservados. **Não podemos copiar código para um repo público.** Podemos usar o repo como *referência* (factos como endpoints não são código) e reescrever. Ou pedir licença ao autor.
- Risco de desatualização: header `AppVersion: 3.251.0` fixo no código; IDs de timers de treino (746 / 982) o próprio autor diz que o OSM pode mudar.

## Mapa da API interna [R]

Host: `https://web-api.onlinesoccermanager.com` · Headers usados: `Authorization: Bearer <access_token>`, `AppVersion`, `PlatformId: 13`, `Origin/Referer: https://en.onlinesoccermanager.com`.

| Uso | Método e path | Notas |
|---|---|---|
| Renovar token | `POST /api/tokenRefresh` (form: grant_type, client_id, client_secret, refresh_token) | O `client_secret` **não está no repo** (lê de cache local ignorada). O caminho principal do autor evita isto: mantém uma página aberta no browser que o front-end usa para rodar o token. |
| Limite de anúncios | `GET /api/v1/user/caps/actions/Shop/0` | Devolve `isCapReached`, `isClaimable`, `currentCount`, `threshold` (código assume 10), `timestampUntilUnreached`. **É um teto imposto pelo servidor.** |
| Plantel | `GET /api/v1/leagues/{L}/teams/{T}/players` | position: 1=ATT 2=MID 3=DEF 4=GK; campos `statAtt/statOvr/statDef`, `injuryId`, `age` |
| Previsões de treino | `GET .../trainingforecasts` | `playerId`, `forecast`, `forecastUniversal` |
| Treinos em curso | `GET .../trainingsessions/ongoing` | 404 quando vazio |
| Iniciar treino | `POST .../trainingsessions` | **form-urlencoded**: `playerId`, `trainer` (1-5), `timerGameSettingId` |
| Recolher treino | `PUT /api/v1.1/.../trainingsessions/{id}/claim` | Obrigatório antes de libertar o slot |
| Outros (leitura) | `GET .../transferplayers/0`, `.../finances/balanceandsavings`, `.../timers` | mercado, saldo, timers |
| Vídeos | `/api/v1.1/user/videos/start` | só observado/logado, não usado para reclamar recompensa |

**Treinos:** 5 slots (1 ATT, 2 MID, 3 DEF, 4 GK, 5 universal). Duração observada: 7200 s (normais), 5400 s (universal). Tudo por **HTTP simples**, sem browser (o browser só serve para manter o token vivo).

**Compras/vendas de jogadores:** o repo **não implementa** nenhum endpoint de compra/venda. O "transfer advisor" só lê e recomenda. Endpoints de transferência = por descobrir.

## Como funciona o farm de anúncios

- Precisa de **browser real** (Playwright): a recompensa vem de um SDK de anúncios embebido (safeframe googlesyndication / Applixir / AdinPlay), não de uma chamada HTTP simples.
- Arquitetura: 1 tab "conductor" + até 8 tabs "watcher" em paralelo; scout verifica o cap via API; ao atingir o limite, dorme o cooldown + 5 min.
- **Pontos problemáticos no código** (não reutilizar):
  - Injeta **callbacks falsos de "anúncio visto"** (`invokeApplixirVideoUnit(... reward:true)`, `adinplay...onAdRewarded()`) para tentar forjar a recompensa. Isto é falsificar a conclusão do anúncio perante o fornecedor de ads, não é só automatizar cliques.
  - Remove overlays de consentimento (GDPR) do DOM à força.
  - 8 tabs em paralelo = padrão muito fácil de detetar; e o cap do servidor limita o ganho de qualquer forma.

## O que vale a pena aproveitar (como conhecimento, reescrito por nós)

| Item | Valor | Comentário |
|---|---|---|
| Mapa de endpoints e auth | **Alto** | Poupa semanas de engenharia inversa. Verificar cada um antes de confiar. |
| Esqueleto do gestor de treinos (`claim → ler estado → preencher slots`) | Alto | Lógica pura e separável, sem gastar coins. Trocar a **política de seleção** pela do dono (a do autor: main stat ≥ 90, forecast máximo). |
| Padrões de tokens (ler `exp` do JWT, rodar sob lock, só em memória) | Médio | Boas práticas |
| Estrutura do "transfer advisor" (ler plantel + mercado + saldo → pontuar) | Médio | Substituir a pontuação pela política de transferências do dono |
| Deteção de cap de anúncios via API (`caps/actions`) | Médio | Útil para não passar o teto |

## O que **não** vale a pena

- Farm de anúncios como está (browser pesado, paralelismo, forja de callbacks).
- Login por StorageDump manual (frágil: o refresh token roda, o dump fica inválido).
- Tudo o que é launchd/macOS, `proxy.pac` com IP local, comentários em turco.

## Melhorias óbvias face ao original

- **Polling inteligente:** o original consulta ~6 endpoints a cada 60 s. Os treinos duram 2 h e o servidor devolve `finishedTimestamp`, por isso basta agendar a próxima verificação para essa hora. Menos pedidos = menos risco.
- Política de seleção configurável (a do dono) em vez de fixa.
- IDs de timers e `AppVersion` lidos dinamicamente em vez de fixos.
- Sem paralelismo agressivo.

## Por verificar (só com OK do dono)

1. Que todos os endpoints acima ainda respondem como descrito.
2. Como é o **login** (username/password → tokens) — o repo não o mapeia.
3. Endpoints de **compra/venda** de jogadores e de **colocar em lista**.
4. Valor real do cap de anúncios e do cooldown na conta do dono.
