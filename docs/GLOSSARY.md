# Glossário

## Desambiguação de "OSM"

| Sigla | Significa | Relevante? |
|---|---|---|
| **OSM** (este projeto) | **Online Soccer Manager** — jogo de gestão de futebol da Gamebasics | ✅ Sim |
| OSM | OpenStreetMap — mapa colaborativo | ❌ Não |
| OSM | Online Scout Manager — software de gestão de escuteiros; tem docs de API reverse-engineered (`osm-api-docs`) | ❌ Não — não usar como referência |

## Termos do jogo (só o que foi visto em fontes)

- **Gamebasics** — empresa por trás do OSM; nome usado nos ToS.
- **BossCoin** — moeda premium do jogo; alvo dos bots de "farm" por anúncios.
- **Anúncios (ads)** — vídeos que dão moedas; automatizá-los é o caso de uso dos repos existentes.
- **Treino (training)** — sessões de treino com slots de treinador; existem endpoints `forecast`/`forecastUniversal` (reportado).

- **Duas moedas** (confirmado pelo dono): **dinheiro do clube (M€)** para transferências; **boss coins** para amigáveis, treino secreto, estágio e olheiro.
- **SALE** — etiqueta azul no preço de jogadores do jogo, mais baratos que o normal (desconto por medir).
- **Slots de transferência** — jogadores que se podem ter à venda ao mesmo tempo: 4 (6 em eventos).
- **Amigável** — jogo que custa 4 boss coins e sobe stats de alguns jogadores.
- **Posições finas:** PL (ponta de lança), EE / ED (extremo esq./dir.), MC (médio centro), MCO / MCD (médio centro ofensivo / defensivo), DC (defesa central), DD / DE (defesa dir./esq.), GK (guarda-redes).
- **Nomes de colunas no ecrã:** Ata / Def / Med (stats), Con (condição), Mor (moral), Valor.

- **Legend / World Legends** — jogadores especiais na lista de transferências (linhas douradas). Comprar custa o dinheiro do jogador **+ ~50 boss coins**; o dono evita.
- **Inform players** — comprar custa o dinheiro **+ ~5 boss coins**; mais aceitável para o dono.
- **Olheiro** — scout: escolhe nacionalidade, idade e posição; custa boss coins e demora muito; só em emergência.
- **Estádio** — 3 componentes com níveis 0–3: Treinos, Campo, Capacidade (ver `THEORY.md` §8).
- **Patrocinadores** — 4 slots, contratos de 2–3 jogos, ~200k por jogo por slot.
- **Médico / advogado** — curam lesões / reduzem suspensões (mínimo 1 jogo); custos residuais.

*Acrescentar termos à medida que forem verificados.*
