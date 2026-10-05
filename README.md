# OSMbot

Exploração de um bot para o **Online Soccer Manager** (Gamebasics).

> **Estado (0.5.0):** o bot trabalha sozinho no Windows (treinos, vídeos da loja e de treino, aviso de slots de venda), com quadro de consola em tempo real. Ver [`CHANGELOG.md`](CHANGELOG.md) e [`docs/`](docs/).

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
pip install -e .
python -m playwright install firefox   # transferência única (~120 MB)
osmbot login
```

O comando `login` abre uma janela de Firefox a sério (não Chromium — o popup de login do Facebook bloqueia o build "Chrome for Testing" do Playwright); entra no OSM à mão nessa janela. A sessão fica guardada em `~/.osmbot/session.json` (cookies exportados; fora do repo, nunca commitada — trata como uma password) e é reutilizada sozinha nas próximas vezes — só precisas de repetir o login se a sessão expirar.

## Utilização

`osmbot` sem argumentos abre um **menu**: iniciar o bot (com ou sem anúncios), estado (clubes, treinos, slots), ensaio (mostra o que faria, sem escrever) e login. Comandos diretos:

| Comando | O que faz |
|---|---|
| `osmbot login` | Abre o Firefox para entrares; fecha a janela para guardar a sessão |
| `osmbot ativo` | **Modo ativo**: recolhe e treina quando os treinos acabam, vê vídeos da loja e de treino, avisa de slots livres; quadro em tempo real. Ctrl+C para parar |
| `osmbot ativo --simular` | Uma passagem sem escrever nada |
| `osmbot ativo --sem-anuncios` / `--sem-quadro` | Sem vídeos / linhas simples em vez do quadro |
| `osmbot status`, `treinos`, `slots` | Só leitura |
| `osmbot recolher`, `treinar` | Escrevem na conta; `--simular` mostra o plano |

Só **uma máquina com o bot ligado de cada vez**. O registo fica em `~/.osmbot/bot.log`.

## Windows: pasta portátil e instalador

`python tools/build_portable.py --zip --installer` cria, em `dist/` (fora do git), `osmbot-portable.zip` (Python, dependências e Firefox lá dentro; abre-se `OSMbot.exe`) e `OSMbot-Setup.exe` (instalador por utilizador, sem administrador; precisa do Inno Setup para ser construído). A sessão não viaja: fica em `%USERPROFILE%\.osmbot` de cada PC e faz-se *Login* uma vez em cada um. Ver `docs/DECISIONS.md` D-016.

## Documentação

- [`CLAUDE.md`](CLAUDE.md) — contexto para o Claude Code
- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — objetivo e critérios
- [`docs/DISCOVERY.md`](docs/DISCOVERY.md) — o que é possível
- [`docs/OPTIONS.md`](docs/OPTIONS.md) — opções consideradas
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — decisões
- [`docs/WORKLOG.md`](docs/WORKLOG.md) — diário de sessões
