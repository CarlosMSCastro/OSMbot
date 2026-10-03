# OSMbot

Exploração de um bot para o **Online Soccer Manager** (Gamebasics).

> **Estado:** lógica pura e testes existem; primeiro contacto real com o jogo (login) em construção. Ver [`docs/`](docs/).

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

## Documentação

- [`CLAUDE.md`](CLAUDE.md) — contexto para o Claude Code
- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — objetivo e critérios
- [`docs/DISCOVERY.md`](docs/DISCOVERY.md) — o que é possível
- [`docs/OPTIONS.md`](docs/OPTIONS.md) — opções em aberto
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — decisões
- [`docs/WORKLOG.md`](docs/WORKLOG.md) — diário de sessões
