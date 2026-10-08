# OSMbot

Exploração de um bot para o **Online Soccer Manager** (Gamebasics).

> **Estado (0.9.2):** o bot trabalha sozinho no Windows (treinos, estádio, patrocinadores, vídeos da loja, de treino e de dinheiro, recompensas diárias, amigável e análise do adversário 4 h antes de cada jogo, aviso de vagas na lista de transferências), numa **janela de programa** com ícone junto ao relógio (o quadro de consola continua disponível). Ver [`CHANGELOG.md`](CHANGELOG.md) e [`docs/`](docs/).

## Aviso

Projeto independente, não afiliado nem aprovado pela Gamebasics. Os Termos de Serviço do jogo restringem bots e scraping sem autorização escrita; usar automação numa conta real pode levar a ban e perda de itens virtuais. Ver [`docs/RISKS_AND_COMPLIANCE.md`](docs/RISKS_AND_COMPLIANCE.md).

Uso por conta e risco de quem o correr, incluindo o autor. Código sem licença (todos os direitos reservados): visível, mas não autorizado para reutilização, modificação ou redistribuição.

## Instalação e login

Funciona em Windows e macOS. Cria o ambiente virtual e ativa-o:

| | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Criar | `python -m venv .venv` | `python3 -m venv .venv` |
| Ativar | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |

Com o ambiente ativado, os comandos são iguais nos dois sistemas:

```
pip install -e .                       # inclui o PySide6 (a janela)
python -m playwright install firefox   # transferência única (~120 MB)
osmbot login
```

O comando `login` abre uma janela de Firefox a sério (não Chromium — o popup de login do Facebook bloqueia o build "Chrome for Testing" do Playwright); entra no OSM à mão nessa janela. A sessão fica guardada em `~/.osmbot/session.json` (cookies exportados; fora do repo, nunca commitada — trata como uma password) e é reutilizada sozinha nas próximas vezes — só precisas de repetir o login se a sessão expirar.

## Utilização

`osmbot` sem argumentos (ou o `OSMbot.exe` da pasta portátil, que não abre consola) abre a **janela** (D-024, só Windows por agora):

- abre pequena, com **Abrir**, **Login** e **Sair**. Num PC novo, começa pelo Login;
- **Abrir** mostra "A carregar o jogo…", põe o bot a trabalhar e a janela cresce para o **quadro**: os clubes lado a lado (jogo, lista de transferências, dinheiro, patrocinadores, estádio, treinos, cansados), a conta (boss coins, loja, diárias, troca de posição) e o que o bot fez desde que foi ligado;
- menu **Bot**: Iniciar, Parar (pára na pausa seguinte), Login, Sair. Menu **Ver**: Avisos e erros, Atualizar quadro, Pasta dos logs, Capturas das falhas;
- a barra de baixo mostra o estado e a próxima verificação;
- com o bot a trabalhar, fechar a janela (X) **só a esconde**: o **ícone junto ao relógio** (logótipo com bolinha verde a trabalhar, cinzenta parado) volta a abri-la. Para sair: Bot → Sair, ou o ícone → Sair. Sem notificações do Windows.

O resto é por comandos:

| Comando | O que faz |
|---|---|
| `osmbot menu` | O menu antigo, na consola (Iniciar, Login, Sair), com o quadro em texto |
| `osmbot login` | Abre o Firefox para entrares; fecha a janela para guardar a sessão |
| `osmbot ativo` | **Modo ativo**: recolhe e treina quando os treinos acabam, sobe o estádio, assina patrocinadores, vê os vídeos (loja, treino, dinheiro), reclama as recompensas diárias, faz o amigável e a análise do adversário 4 h antes de cada jogo (se ainda não estiverem feitos) e avisa de vagas na lista de transferências; quadro em tempo real. Ctrl+C para parar |
| `osmbot ativo --simular` | Uma passagem sem escrever nada |
| `osmbot ativo --sem-anuncios` / `--sem-quadro` | Sem vídeos / linhas simples em vez do quadro |
| `osmbot status`, `treinos`, `slots` | Só leitura |
| `osmbot recolher`, `treinar` | Escrevem na conta; `--simular` mostra o plano |
| `osmbot pasta-logs [pasta do repo]` | Mostra ou escolhe o repo para onde vai o registo (`logs/<PC>/`), se não for encontrado sozinho; copia o registo antigo |
| `osmbot recompensas` | Reclama as recompensas diárias (início de sessão, missões, vídeos acumulados); ficam no inventário; `--simular` mostra o plano |

Só **uma máquina com o bot ligado de cada vez**. O registo fica em `~/.osmbot/bot.log` e também no repo, em `logs/<nome do PC>/AAAA-MM-DD.log` (D-022), para o ver noutra máquina depois do teu commit/push. O bot encontra o repo sozinho (D-023): o código de onde corre, ou uma pasta `OSMbot` ao lado da pasta do bot ou na pasta pessoal, `Documents` ou `Desktop`. Só se o repo estiver noutro sítio: `osmbot pasta-logs <pasta do repo>`.

## Windows: pasta portátil e instalador

`python tools/build_portable.py --zip --installer` cria, em `dist/` (fora do git), `osmbot-portable.zip` (Python, dependências e Firefox lá dentro; abre-se `OSMbot.exe`, só a janela, sem consola; os comandos correm com `OSMbot-consola.exe`, p. ex. `OSMbot-consola.exe menu`) e `OSMbot-Setup.exe` (instalador por utilizador, sem administrador; precisa do Inno Setup para ser construído). A sessão não viaja: fica em `%USERPROFILE%\.osmbot` de cada PC e faz-se *Login* uma vez em cada um. Ver `docs/DECISIONS.md` D-016.

## Documentação

- [`CLAUDE.md`](CLAUDE.md) — contexto para o Claude Code
- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — objetivo e critérios
- [`docs/DISCOVERY.md`](docs/DISCOVERY.md) — o que é possível
- [`docs/OPTIONS.md`](docs/OPTIONS.md) — opções consideradas
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — decisões
- [`docs/WORKLOG.md`](docs/WORKLOG.md) — diário de sessões
