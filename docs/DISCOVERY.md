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
- **[H]** O jogo é uma web app com API interna JSON. Não confirmado; hosts/paths desconhecidos.
- **[H]** Existe algum tipo de proteção anti-automação no jogo (não foi observada). Desconhecido.
- **Por descobrir:** autenticação exata, hosts, formato dos dados de plantel/mercado/jogos, limites concretos de pedidos.

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
