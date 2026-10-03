# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-PT/1.1.0/); versões segundo [SemVer](https://semver.org/lang/pt-BR/) (`0.x` até haver automação estável).

Este ficheiro é o **histórico de versões, para quem lê o repo**. O diário interno de cada sessão de trabalho está em [`docs/WORKLOG.md`](docs/WORKLOG.md).

## [Por lançar]

## [0.3.0] — 2026-10-03

Sessão persistente e primeiro cliente sem browser (só leitura).

### Adicionado
- Sessão guardada em `~/.osmbot/session.json` (cookies, 0600, fora do repo), restaurada no arranque: o login deixa de se repetir. Funciona no Mac; Windows por testar.
- `src/osmbot/game/client.py`: cliente HTTP sem browser (só GET) que renova o `access_token` sozinho pelo `tokenRefresh` e guarda os tokens novos. Os códigos OAuth do cliente são apanhados do pedido do próprio site para `~/.osmbot/client.json` (0600, nunca versionados).
- `osmbot status`: clubes ativos, ranking, orçamento e boss coins.
- `osmbot probe <caminho>`: GET de leitura que mostra só a estrutura da resposta (nomes e tipos, nunca valores).
- Comandos de descoberta: `inspect-session`, `token-info`, `inspect-network`.
- Dependência `certifi` (o Python do Homebrew no Mac não traz certificados).
- 7 testes novos (cliente e status); 51 no total.

### Corrigido
- O "login funciona" de 0.2.0 não guardava a sessão: os tokens do OSM são cookies de sessão e o Firefox apagava-os ao fechar. Perfil persistente abandonado.

### Descoberto (ver `docs/DISCOVERY.md`)
- `access_token` dura 20 min; `refresh_token` 7 dias com prazo deslizante; formato do `tokenRefresh` (OAuth2); autenticação por `Authorization: Bearer` confirmada.

## [0.2.0] — 2026-09-28

Primeiro contacto real com o jogo: login confirmado a funcionar.

### Decidido
- D-013 encerrada: dono deu OK explícito (regra 5) para contacto real com o jogo — login e leitura, para já.
- D-004 emendada: os testes começam já na **conta principal**, não numa conta secundária como estava previsto; fica registado que isto expõe a conta principal diretamente ao risco de ban (sem isolamento de "conta descartável").

### Adicionado
- `osmbot login`: abre uma janela real de Firefox (Playwright, perfil persistente guardado fora do repo em `~/.osmbot/firefox-profile`) para um login manual único; a sessão fica guardada e é reutilizada sozinha depois — sem copiar cookies nem guardar password. **Confirmado pelo dono a funcionar.**
- `osmbot dashboard`: abre a sessão guardada na área do clube, passo de descoberta antes de qualquer extração de dados.
- `pyproject.toml`: dependência de runtime `playwright` e entry point `osmbot`.

### Corrigido
- `choose_formation`: `similar_margin` passa a ter valor por omissão **2** (regra do dono: dentro de ±2 pontos ainda considera 4-3-3), deixando de ser obrigatório.

### Notas técnicas
- Login foi tentado primeiro em Chromium (Playwright); o popup de login do Facebook (única via de login desta conta) bloqueia o build "Chrome for Testing", mesmo com login manual por uma pessoa real. Resolvido trocando para **Firefox** (também gerido pelo Playwright, sem instalar nada como programa no Windows).

## [0.1.0] — 2026-09-27

Âmbito e postura de risco definidos. **Continua sem nenhum acesso ao jogo.**

### Decidido
- Alcance (D-002): automação até **A3** (treinos, transferências) já, e **A4** (anúncios) também aceite.
- Postura de risco (D-004): risco de ban aceite conscientemente pelo dono; testes começam em conta secundária.
- Anúncios (D-012): sem servidor dedicado — corre nas máquinas do dono conforme ligadas, sempre a respeitar os limites do jogo, sem horário fixo.
- Interface (D-006): CLI fina sobre a biblioteca existente, com arranque automático por máquina.
- Licença (D-007): nenhuma (todos os direitos reservados); disclaimer de risco reforçado no `README.md`.

### Investigado
- `docs/DISCOVERY.md`: deteção e histórico de bans no OSM (device ban; precedente de junho de 2026 sobre exceder limites via bug — não sobre automatizar dentro deles).

## [0.0.1] — 2026-09-27

Primeira versão: **documentação e lógica pura. Não há nenhum acesso ao jogo.**

### Adicionado
- Documentação de contexto: `CLAUDE.md`, `README.md` e `docs/` (`PROJECT_BRIEF`, `DISCOVERY`, `PRIOR_ART`, `OPTIONS`, `DECISIONS`, `RISKS_AND_COMPLIANCE`, `GLOSSARY`, `WORKLOG`).
- `docs/THEORY.md`: a metodologia de jogo do dono (tática, especialistas, treinos, transferências, estádio, patrocinadores, vídeos, poupança).
- Projeto Python (`pyproject.toml`, layout `src/`) com lógica pura, sem I/O:
  - `osmbot.models`: `Player`, `Position`.
  - `osmbot.theory.tactics`: escolha de formação, sliders, desarme.
  - `osmbot.theory.specialists`: capitão, penáltis, livres, cantos.
  - `osmbot.training.policy`: quem treinar em cada slot.
- 44 testes (pytest) com dados sintéticos.
- `.gitignore` que exclui credenciais, sessões, HARs e dados recolhidos.
