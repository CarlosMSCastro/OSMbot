# CLAUDE.md — OSMbot

Ficheiro de entrada para o Claude Code. Lê isto primeiro em cada sessão, depois os docs que a tarefa exigir.

## O que é este projeto

Um bot para o **Online Soccer Manager (OSM)** — o jogo de gestão de futebol da Gamebasics (onlinesoccermanager.com).

> **Atenção à ambiguidade:** "OSM" também é OpenStreetMap e Online *Scout* Manager. Este projeto **não** tem nada a ver com nenhum deles. Resultados de pesquisa e repos com "osm-api" são muitas vezes Scout Manager — ignorar. Ver `docs/GLOSSARY.md`.

## Estado atual

O bot já **escreve na conta** (modo ativo). Versão atual em `pyproject.toml` e `CHANGELOG.md`; o que falta fazer em `docs/WORKLOG.md`; decisões (alcance A3/A4, risco aceite, autonomia por níveis) em `docs/DECISIONS.md`. O repo é **público** (D-016): sem nomes de clubes, ligas, jogadores ou utilizadores de terceiros em ficheiros versionados, **exceto em `logs/`** (D-022: o registo do bot, completo, aceite pelo dono). Para diagnosticar o bot noutra máquina, ler `logs/<PC>/AAAA-MM-DD.log`.

## Código

Python ≥ 3.11, layout `src/`. A lógica de decisão (`theory/`, `training/`, políticas) é **pura** (sem I/O, sem rede) e testada com dados sintéticos; o contacto com o jogo está só em `src/osmbot/game/`. A janela (`src/osmbot/gui/`, PySide6, D-024) só mostra: `gui/view.py` é puro e testado; `gui/window.py` corre o mesmo ciclo (`run_active(board=...)`) numa thread e não fala com o jogo por si, exceto a leitura do quadro (só GET), a qualquer momento: de 3 em 3 min e em Ver → Atualizar (D-027).

Correr testes (com o venv ativado, igual em Windows e macOS): `python -m pytest`. Criar o venv e ativá-lo: ver `README.md`. O projeto corre em Windows e macOS (o dono desenvolve nos dois): código com `pathlib`, `encoding="utf-8"` explícito, sem comandos específicos de um SO; a sessão do browser (`~/.osmbot/`) é por máquina e nunca se sincroniza.

Regra: **cada regra do código tem de estar em `THEORY.md`**. Se o código precisar de uma regra que a teoria não cobre, marcar como suposição **[S]** lá e perguntar ao dono.

## Mapa dos docs

| Ficheiro | Para quê |
|---|---|
| `docs/PROJECT_BRIEF.md` | Objetivo, não-objetivos, critérios de sucesso |
| `docs/DISCOVERY.md` | O que se apurou sobre o que é possível (com fontes e nível de confiança) |
| `docs/THEORY.md` | Teoria de jogo do dono (formações, sliders, desarme, especialistas). Fonte de verdade das regras; não alterar sem o dono |
| `docs/PRIOR_ART.md` | Análise do `osm-ad-bot`: mapa da API, o que reutilizar, o que evitar |
| `docs/OPTIONS.md` | Opções de alcance/abordagem/stack e trade-offs, sem decisão |
| `docs/DECISIONS.md` | Registo de decisões (ADR leve) + lista de decisões em aberto |
| `docs/RISKS_AND_COMPLIANCE.md` | ToS do OSM, risco de ban, gestão de segredos |
| `docs/GLOSSARY.md` | Termos do jogo e desambiguação |
| `docs/WORKLOG.md` | Diário por sessão: o que foi feito, o que falta, próximo passo |
| `logs/<PC>/` | Registo do bot por máquina e por dia (D-022); o dono faz commit/push |

## Regras para o Claude neste repo

1. **Contexto primeiro:** ler `docs/WORKLOG.md` (última entrada) e `docs/DECISIONS.md` antes de propor trabalho.
2. **Não re-litigar** decisões já registadas como "Aceite". Se houver razão para as rever, propor uma nova entrada que a substitua.
3. **Fim de sessão:** atualizar `docs/WORKLOG.md`; se surgiu ou se fechou uma decisão, atualizar `docs/DECISIONS.md`; se se apurou um facto novo, `docs/DISCOVERY.md`.
4. **Factos vs. hipóteses:** em `DISCOVERY.md` marcar cada afirmação como *Verificado* (visto por nós), *Reportado* (fonte de terceiros) ou *Hipótese*. Não promover sem verificar.
5. **Contacto com o jogo real, por níveis (D-014, 2026-10-05).** Ver `RISKS_AND_COMPLIANCE.md`.
   - **Livre (só leitura):** `status`, `treinos`, `probe`, GETs. Posso correr sem perguntar, desde que a sessão já exista. O login é sempre feito pelo dono (interativo).
   - **Autónomo, só com o bot "ativo":** `recolher`, `treinar` e `recompensas` (início de sessão, missões, vídeos acumulados; D-020; só reclamam e guardam no inventário, nunca usam itens, exceto o Claim da janela "Unclaimed Energy", D-028) (escritas já observadas e testadas), sem `--max`, sem pedir confirmação. "Ativo" = o dono disse nessa sessão que o bot está a trabalhar. **Em modo de desenvolvimento (por omissão) não executo escritas na conta**; só simulação ou testes.
   - **Pede OK sempre:** qualquer escrita nova, nunca observada (vender, comprar, anúncios) e tudo o que o jogo possa tratar como abuso. Nunca exceder os limites do próprio jogo; nunca forjar recompensas (regra 8).
   - Segredos continuam a ser regra 6, sem exceção.
6. **Segredos:** nunca escrever credenciais, cookies, tokens, HARs ou dumps de sessão em ficheiros versionados. Vão para `.env*` / pastas ignoradas (ver `.gitignore`). O repo vai ser público no GitHub.
7. **Não inventar endpoints ou comportamento da API do OSM.** Se não foi observado, é hipótese.
8. **Código de terceiros:** não copiar código de outros repos (sem licença = todos os direitos reservados). Usar como referência e reescrever. Não implementar falsificação de recompensas de anúncios (ver `PRIOR_ART.md`).
9. **Git e GitHub são do dono.** O Claude **não** corre `git init`, commit, push, pull, nem cria repos ou branches. Só ajuda, quando pedido, a escrever mensagens de commit e a sugerir versões (escrever o texto e entregar).
10. **Registar antes de construir.** Quando o dono explica a sua metodologia, registar em `docs/THEORY.md` e perguntar o que fazer a seguir; só construir o que ele disser que quer automatizado. Explicar termos técnicos em português simples.

## Convenções

- Idioma dos docs: **português europeu**. Código, identificadores e mensagens de commit: a decidir (D-003).
- Datas em ISO (`AAAA-MM-DD`).
- **Versões:** SemVer, `0.x` até haver automação estável. A versão vive em `pyproject.toml`; o histórico em `CHANGELOG.md` (para quem lê o repo), separado de `docs/WORKLOG.md` (diário interno). Quando o dono pedir uma versão, o Claude atualiza os dois ficheiros e escreve a mensagem de commit; **tags e releases são do dono** (regra 9).
- Docs curtos e factuais; preferir tabelas e listas a prosa.
- Repo git inicializado (ramo `main`) com `origin` = https://github.com/CarlosMSCastro/OSMbot.git. Foi feito pelo Claude **a pedido pontual do dono em 2026-09-27** (só `git init` + `git remote add`); commits, pushes e pulls continuam a ser do dono (regra 9).
