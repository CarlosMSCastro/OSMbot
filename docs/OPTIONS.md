# Opções em aberto

*Estado em 0.8.0: o essencial está decidido (ver `DECISIONS.md`): alcance **A3/A4** (D-002), abordagem **híbrida** (browser só para login e vídeos; HTTP para o resto), interface **consola** com quadro e menu (D-015), depois **janela PySide6** com ícone junto ao relógio (D-024, 0.9.0), stack **Python** (D-001), distribuição Windows em pasta portátil e instalador (D-016). O texto abaixo fica como registo das opções consideradas.*

## A. Alcance — o que faz o bot?

*Decidido: A3 para treinos/transferências, A4 (anúncios) dependente de D-012. Ver `DECISIONS.md` D-002/D-004.*

| Nível | Exemplos | Toca no jogo? | Risco de ban |
|---|---|---|---|
| **A0 — Offline** | Otimizador/simulador de plantel e táticas com dados que o utilizador introduz ou exporta à mão | Não | Nenhum |
| **A1 — Só leitura** | Ler o próprio plantel, mercado, valores; gerar análises/alertas | Sim (leitura) | Baixo–médio (ToS proíbe scraping sem autorização; volume conta) |
| **A2 — Assistido** | Bot sugere (tática, compras, treinos); humano clica | Sim (leitura) | Baixo–médio |
| **A3 — Autónomo (gestão)** | Bot faz treinos, escalações, transferências | Sim (escrita) | Alto |
| **A4 — Autónomo (farm)** | Ver anúncios para moedas | Sim (escrita) | Muito alto — é o que os repos existentes fazem e o que mais claramente é "bot" |

## B. Abordagem técnica (se tocar no jogo)

| Abordagem | Prós | Contras |
|---|---|---|
| **Browser automation** (Playwright/Selenium) | Provado por 4 repos; comporta-se como um utilizador; não exige reverse engineering | Pesado; frágil a mudanças de UI; mais fácil de detetar por padrões |
| **HTTP direto à API interna** | Leve, rápido, estável se a API for estável | Exige mapear API e auth; tokens rodam; mais fácil de exceder rate limits sem notar |
| **Híbrido** (browser para login/token, HTTP para dados) | Equilíbrio | Mais complexidade |

## C. Interface

CLI · bot Discord/Telegram · dashboard web · biblioteca importável. (Se for para GitHub, uma lib + CLI fina costuma ser a base mais reutilizável.)

## D. Stack

Não decidido. Python e TypeScript têm ambos Playwright e ecossistema de bots (discord.py / discord.js, python-telegram-bot / grammY). A escolha deve seguir o alcance (A) e a interface (C), não o contrário.

## E. Perguntas para o utilizador (respondidas: poupar tempo; conta principal; uso pessoal com repo público; risco aceite)

1. Que problema queres resolver no jogo? (poupar tempo, ganhar vantagem, analisar dados, aprender)
2. Conta própria "a sério" ou conta de teste descartável?
3. Público: só para ti, ou ferramenta para outros jogadores?
4. Aceitas o risco de ban (A3/A4), ou preferes ficar em A0–A2?
