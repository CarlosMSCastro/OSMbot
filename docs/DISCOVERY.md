# Discovery — o que é possível

*Recolhido em 2026-09-27 por pesquisa web. Nada foi testado contra o jogo real.*
Legenda: **[V]** verificado por nós · **[R]** reportado por fonte de terceiros · **[H]** hipótese

## 1. API oficial

- **[R] Não foi encontrada API pública oficial nem documentação.** A pesquisa devolve sobretudo docs do *Online Scout Manager* (outro produto) — não confundir.
- **[R]** Os ToS mencionam "our APIs", o que sugere que existem APIs internas, usadas pelo próprio front-end.
- O fórum oficial tem um tópico "Osm API" (`forum.onlinesoccermanager.com/topic/70973/osm-api`) mas está atrás de proteção anti-bot (Anubis) e não deu para o ler. **Por ler.**

## 2. Projetos existentes (prior art)

| Repo | Stack | O que faz | Notas |
|---|---|---|---|
| [nsozturk/osm-ad-bot](https://github.com/nsozturk/osm-ad-bot) | Python + Playwright | Farm de BossCoin vendo anúncios; gestor opcional de treinos | Arquitetura "conductor + watcher" (1 tab monitoriza rate limits via API, N tabs veem anúncios). Sessão importada por dump de cookies/localStorage. Usa endpoints `forecast`/`forecastUniversal` para treinos. Trata rate limits. |
| [RuiRC/Online-Soccer-Manager-Ad-Watch-Bot](https://github.com/RuiRC/Online-Soccer-Manager-Ad-Watch-Bot) | Selenium | Vê anúncios automaticamente | Simples |
| [okch-codes/onlinesoccermanager-auto-manager](https://github.com/okch-codes/onlinesoccermanager-auto-manager) | Node/TS + Playwright + Docker | Moedas grátis via testes Playwright | **Arquivado a 2026-03-26.** Login por `.env` com user/password. Autor diz ser "apenas demonstração". |
| [atuncer/OSM_Scraping](https://github.com/atuncer/OSM_Scraping) | Python + Selenium + SQLite | Scraping de dados de jogadores para `players.db` | Cookie de sessão em `cookie.pkl`. **Avisa que o servidor pode bloquear a conta por excesso de pedidos.** |

**Leitura:** todos os projetos encontrados são automação de browser, e o caso de uso dominante é farm de moedas. Não encontrei nenhuma biblioteca de cliente HTTP para o jogo nem documentação de endpoints. Ninguém publicou a forma da API — é território por mapear.

## 3. O que se sabe sobre a superfície técnica

- **[R]** Existe rate limiting do lado do servidor (nsozturk e atuncer tratam-no/avisam).
- **[R]** Os tokens são de curta duração e rodados pelo front-end (nsozturk mantém a página viva para os manter).
- **[R]** Sessão por cookies funciona para automação (dois projetos independentes o usam).
- **[V]** (2026-09-30, `osmbot inspect-session`, só nomes/tamanhos, sem valores) Após o login por Facebook, o OSM guarda a sessão em cookies: `access_token` (~443 B) e `refresh_token` (~331 B) em `en.onlinesoccermanager.com`, ambos **cookies de sessão** (sem validade → o browser apaga-os ao fechar); `session` (~591 B, validade 1 ano; função desconhecida); `forum_token`; `MachineId` em `web-api.onlinesoccermanager.com`. Não apareceu localStorage/sessionStorage. A sessão do Facebook (`c_user`, `xs`) dura 1 ano — daí o botão "Continuar como ..." em cada visita.
- **[V]** (2026-09-30, `token-info` + `inspect-network`) `access_token` e `refresh_token` são JWT. `access_token` dura **20 min**; `refresh_token` dura **7 dias**. Renovação: `POST web-api.onlinesoccermanager.com/api/tokenRefresh` com `refresh_token` no corpo → 200; após renovar, **ambos** os tokens são reemitidos e o `refresh_token` ganha outros 7 dias (prazo deslizante) → basta renovar ≥1×/semana. O site repete os pedidos que deram 401 depois de renovar. O `access_token` traz `team` e `world`.
- **[H]** Ao renovar, o `refresh_token` antigo deixa de valer (rotação) → guardar sempre o mais recente.
- **[V]** (2026-10-03, `inspect-network`, só nomes e tipos) Formato do `tokenRefresh`: pedido `application/x-www-form-urlencoded` com `grant_type`, `client_id`, `client_secret`, `refresh_token` (todos texto); resposta JSON 200 com `access_token` (texto), `token_type` (texto), `expires_in` (inteiro), `refresh_token` (texto). É um fluxo OAuth2 `refresh_token` normal. Com uma sessão guardada há 3 dias, o site renovou sozinho (2 renovações numa visita). O `client_id`/`client_secret` são apanhados do pedido do próprio site (`browser.py`) e guardados em `~/.osmbot/client.json` (0600) — **nunca em ficheiros versionados**.
- **[V]** (2026-10-03) Cliente sem browser funciona: `GET` com `Authorization: Bearer <access_token>` → 200; renovação pelo `tokenRefresh` com os códigos guardados. No Python do Homebrew (Mac) faltam certificados → usa-se `certifi`.
- **[V]** (2026-10-03, `probe`, só estrutura) `user/bosscoinwallet` → `id`, `userId`, `amount` (int). `user/accounts` → dados do manager + `teamSlots` (chaves "0", "1"…), cada um com `team` (`id`, `leagueId`, `name`, `ranking`, `budget`, `stadiumLevel`, `crewId`…) e `league` (`id`, `name`, `weekNr`, `seasonNr`, `leagueType`…). **[H]** `ranking` = posição na liga (confirmar com o ecrã do jogo).
- **[V]** (2026-10-03) Endpoints extra vistos ao abrir o jogo, por equipa (`leagues/{L}/teams/{T}/`): `matchpreparation`, `teamtactics`, `teamtrainings`, `trainingsessions/ongoing`, `finances/balanceandsavings`, `transferplayers/0`, `players`, `timers`. Utilizador: `user/bosscoinwallet`, `user/dailylogin`, `user/accounts`, `missions`. Os 404 (`offers`, `specialoffer`, `user/ads`, `webnotifications`) parecem "sem dados", não "não existe". Um `POST usermissions/weeklytrack` foi feito pelo próprio site, não por nós. Corpos de resposta (plantel, treinos, finanças): **por ver**.
- **[V]** API observada (só método/endereço/estado; corpos por ver): base `web-api.onlinesoccermanager.com/api/v1` (e `v1.1`). Por equipa: `leagues/{L}/teams/{T}/` + `players`, `timers`, `teamtactics`, `teamtrainings`, `teamtrainings/camphistory`, `trainingsessions/ongoing`, `finances/balanceandsavings`, `transferplayers/0`, `matchpreparation`, `offers`, `specialoffer`, `spyinstructions`. Por liga: `leagues/{L}`, `standings`, `teams`, `referees`, `settings`. Utilizador: `user/bosscoinwallet`, `user/dailylogin`, `user/accounts`, `user/ads` (404), `missions`.
- **[V]** Exportar estes cookies e restaurá-los num Firefox novo **entra no jogo sem novo login**, minutos depois. Duração da validade e mecanismo de renovação pelo `refresh_token`: **por descobrir**.
- **[V]** (2026-10-03, `probe`, só estrutura; caminhos por equipa em `leagues/{L}/teams/{T}/`) `players` → lista de jogadores com `id`, `fullName`, `position`, `specificPosition`, `statAtt`, `statDef`, `statOvr`, `age`, `fitness`, `morale`, `status`, `unavailable`, `lineup`, `value`, `yellowCards`, `trainingProgress`, `injuryId`, `suspensionId`, `goals`, `assists`, `matchesPlayed`, `rarity`, `nationality`, `squadNumber`. `trainingsessions/ongoing` → lista (4 itens na equipa testada, coincide com os 4 slots) com `playerId`, `player` (o jogador completo), `trainer`, `weekNr` e `countdownTimer` (`type`, `currentTimestamp`, `finishedTimestamp`, `isClaimed`, `isBoosted`). `timers` → lista (9 itens) com os mesmos campos do `countdownTimer`. `teamtrainings` → lista curta com `week` e `type`. **[H]** `statAtt` é o campo do preço máximo/ataque (ver THEORY.md); significado dos códigos numéricos (`position`, `status`, `lineup`, timers `type`) **por descobrir**: cruzar com o ecrã do jogo antes de usar.
- **[V]** (2026-10-03, confirmado pelo dono contra o ecrã) Códigos de `players`: `position` 1=avançado, 2=médio, 3=defesa, 4=guarda-redes. `unavailable` = **jogos de ausência** (jogador lesionado a 2 → "2 jogos"); `lineup` 0 = fora do onze. `injuryId` **não** serve de indicador de lesão (há jogadores com `injuryId` ≠ 0, `unavailable` 0 e que não estão lesionados) → usar `unavailable` > 0. `fitness` mostra-se a amarelo abaixo de algum limiar (76 era amarelo); limite exato por descobrir.
- **[V/H]** `lineup` 1..11 são os titulares e 12..18 os suplentes. **[H]** Nos titulares, os números seguem a ordem GK, defesas, médios, avançados, pelo que a formação deduz-se da contagem por posição (num clube deu 4-3-3, confirmado; no outro deu 5-3-2, por confirmar). `status` 1 (jogador no médico?) e `specificPosition` (4=PL?, 11=extremo?, 3=DC?, 12=lateral?) são **[H]**.
- **[V]** (2026-10-04) O `tokenRefresh` **exige** o cabeçalho `AppVersion` (e outros que o site envia: `PlatformId`, `Origin`, `Referer`, `User-Agent`…). Sem ele → 400 *"You must update the app to continue playing OSM!"*. Com os cabeçalhos copiados do pedido real do site, a renovação sem browser funciona e o `refresh_token` ganha +7 dias. A versão (formato `3.x.y`) muda quando o jogo atualiza → o bot apanha-a sempre que o browser abre (`osmbot dashboard`) e avisa se ficar desatualizada. Os `GET` normais funcionam só com `Authorization: Bearer`. **Lição:** antes de 2026-10-04 o cliente só tinha sido testado dentro dos 20 min de validade; a renovação real nunca tinha sido exercitada.
- **[V]** (2026-10-04, `inspect-writes`; o dono recolheu 1 treino e pôs 1 jogador a treinar) **Recolher** um treino: `PUT /api/v1.1/leagues/{L}/teams/{T}/trainingsessions/{sessionId}/claim`, **sem corpo**; resposta 200 com `trainingSession`, `progressImprovement`, `variableTrainingProgression`. **Pôr a treinar**: `POST /api/v1/leagues/{L}/teams/{T}/trainingsessions`, corpo `application/x-www-form-urlencoded` com `playerId`, `trainer`, `timerGameSettingId`; resposta 200 com a sessão nova (e `countdownTimer`, `trainingForecast`). Ambos levam o mesmo conjunto de cabeçalhos dos GET (`Authorization`, `AppVersion`, `PlatformId`, `Origin`, `Referer`…). O site faz também `POST usermissions/weeklytrack` (sem corpo) várias vezes por sessão (missões); não é necessário para treinar, mas é o que o site faz.
- **[V]** `trainer` = posição do jogador: 1 ataque, 2 médio, 3 defesa, 4 guarda-redes (cada sessão ongoing tem `trainer` igual à `position` do jogador e o timer do mesmo `type`). Cada slot de treinador treina um jogador dessa posição. Um treino novo dura **8h**.
- **[V]** (2026-10-04, confirmado com um pedido do bot: 200 e treino registado com ~8h) `timerGameSettingId` = id da definição `TrainingSession` em `leagues/{L}/gamesettings` (valor 480 min = 8h). Existe também `TrainingUniversalSession` (360 min, treinador universal: fora de âmbito). Procurar o id **pelo nome** em runtime em vez de o fixar no código.
- **[H]** O jogo é uma web app com API interna JSON. Não confirmado; hosts/paths desconhecidos.
- **[H]** Existe algum tipo de proteção anti-automação no jogo (não foi observada). Desconhecido.
- **Por descobrir:** validade do `access_token` e pedido de renovação, hosts, hosts, formato dos dados de plantel/mercado/jogos, limites concretos de pedidos.

## 4. Regras do jogo/ToS relevantes

Resumo (detalhe e citações em `RISKS_AND_COMPLIANCE.md`): bots e software de terceiros são tratados como *cheating*; scraping/uso das APIs sem autorização escrita é proibido; sanções vão de aviso a ban permanente com perda de itens virtuais sem reembolso.

## 5. Deteção e histórico de bans (pesquisa web, 2026-09-27)

- **[R]** O jogo tem **"device ban"**: um dispositivo banido fica impedido de jogar com contas novas criadas nesse mesmo dispositivo/browser. Fonte: fóruns de terceiros sobre OSM.
- **[R] Caso concreto relevante (fórum oficial, ~junho 2026):** um bug no jogo permitiu a alguns jogadores ver **vídeos ilimitados** (mais do que o limite normal). A Gamebasics baniu essas contas; mesmo depois de confirmarem que era um bug do jogo e não erro do jogador, **mantiveram as sanções** porque consideraram que os jogadores "abusaram de um exploit". Fonte: `forum.onlinesoccermanager.com/topic/76755` e tópicos relacionados.
  - **Porque interessa (e o que NÃO prova):** este caso foi especificamente sobre **exceder o teto normal de vídeos/hora** via bug — não sobre automatizar cliques **dentro** dos limites do jogo. Não é prova de que um bot bem-comportado (respeita "4/hora", respeita o cooldown de 1-3h) seja detetado da mesma forma; isso continua **desconhecido**, não confirmado nem afastado. O que prova é que "não sabia que era um exploit" não livra da sanção — relevante se algum dia se exceder um limite por engano, não para o caso de respeitar os limites.
- **[H]** Deteção por *fingerprint* de dispositivo (Canvas/WebGL/resolução/etc.) e correlação de IP entre contas é comum noutros jogos com sistemas anti-multi-conta; **não confirmado especificamente para o OSM**, só inferido de artigos genéricos sobre deteção de multi-contas.
- **Leitura para D-004:** uma conta secundária no mesmo PC/browser que a principal pode não isolar totalmente o risco, se o OSM ligar contas por dispositivo. Testar em conta separada ajuda, mas não é garantia total enquanto não soubermos se há device-linking aqui.

## 6. Níveis do estádio: pesquisa web (2026-09-27, sem resultado fiável)

*Motivo: o dono viu que o número de melhoramentos para subir o estádio de nível 2→3 difere entre clubes (Betis: 11; clube pequeno na liga da Arménia: 7) e pediu para procurar online como funciona.*

- **Sem resposta fiável.** O tópico do fórum oficial mais relevante (`forum.onlinesoccermanager.com/topic/5022/upgrading-stadium`) está atrás do mesmo bloqueio anti-bot (Anubis) já registado em §1/§7 — não deu para ler.
- **[R], com reserva:** a pesquisa devolveu uma percentagem de bónus por nível (Campo: +2%/+4%/+6%; Treinos: +10%/+25%/+50%) supostamente vinda de uma wiki chamada "Online Soccer Manager Wiki" (Fandom), mas o fetch direto a essa página falhou (erro 402) — não conseguimos confirmar o conteúdo em primeira mão.
- **Risco de confusão de jogo (como o aviso do `GLOSSARY.md` para OpenStreetMap/Scout Manager):** várias páginas devolvidas eram de **`soccermanager.com`** ("Soccer Manager"), um jogo **diferente** do nosso (`onlinesoccermanager.com`, Gamebasics), com nome muito parecido. Não é seguro que os números acima sejam do jogo certo. **Tratar como não confirmado até se ver o mesmo no jogo do dono.**
- **Conclusão:** não há fonte online fiável para "quantos melhoramentos por nível". A via mais fiável continua a ser o dono recolher mais exemplos reais (mais clubes/ligas) e nós procurarmos um padrão (ex.: será que escala com o nível da liga ou com o valor do plantel?).

## 7. Próximos passos de descoberta

1. Ler o tópico do fórum "Osm API" (manualmente, no browser, por causa do Anubis).
2. Ler o artigo do suporte "What's considered cheating in OSM?" (devolveu 403 ao fetch automático).
3. **Só com OK do utilizador e conta que ele aceite arriscar:** observar, no browser, as chamadas de rede da web app durante uso normal (só leitura), para mapear hosts/endpoints/auth.
4. Considerar contactar a Gamebasics a pedir autorização escrita (única via limpa para scraping/API).
5. Se o dono conseguir mais exemplos de melhoramentos/nível do estádio (clube + liga + número), procurar padrão (§6).
