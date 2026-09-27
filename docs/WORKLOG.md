# Worklog

Entradas mais recentes primeiro. Cada sessão: o que se fez · o que ficou por fazer · próximo passo.

## 2026-09-27 (cont. 13) — D-007 fechada; todas as decisões em aberto resolvidas

- **D-007 aceite:** sem licença (todos os direitos reservados) — visível mas não reutilizável por terceiros; coerente com D-002 (uso só pessoal). MIT foi considerada e descartada.
- `README.md` atualizado: estado corrigido (já há código de lógica pura, não é "sem código ainda") e disclaimer reforçado com a nota de licença/risco.
- Com isto, `DECISIONS.md` fica sem itens "Em aberto" exceto D-008, que não é bem uma decisão pendente — é a regra fixa de que git/GitHub são só do dono.
- **Próximo passo:** não há mais decisões de alcance/risco a bloquear trabalho. Pode avançar-se para código de A3 (treinos, transferências) — o dono decide se quer começar por aí, ou por outra coisa.

## 2026-09-27 (cont. 12) — D-012 e D-006 fechadas

- Discussão sobre risco dos anúncios: corrigida a leitura do precedente de junho — é sobre **exceder** limites via bug, não sobre automatizar **dentro** dos limites (isso fica desconhecido, não confirmado nem afastado). `DISCOVERY.md` §5 e `RISKS_AND_COMPLIANCE.md` corrigidos.
- Dono propôs mitigação: respeitar sempre os limites do jogo, capar a fração de janelas apanhadas (~60-70%, por afinar) com timings aleatórios, correr só nas horas em que as máquinas estão ligadas (sem horário fixo, varia dia a dia).
- **D-012 aceite:** anúncios (A4) sem servidor dedicado — corre em PC pessoal, MacBook e PC da empresa (dono é o IT da empresa, sem risco de política de TI de terceiros).
- **D-006 aceite:** CLI fina + biblioteca, arranque automático por máquina (Task Scheduler/LaunchAgent), sem horário fixo.
- Descartada a ideia de usar um iPhone antigo (6s/8) como "servidor": iOS não corre automação em background sem jailbreak, e mesmo com jailbreak não é viável correr um browser real para ver o anúncio sem forjar a confirmação.
- Sem código novo.
- **Próximo passo:** só falta **D-007** (licença do repo) para fechar todas as decisões em aberto. Depois disso, pode começar-se código (treinos/transferências, A3, não depende de mais nada).

## 2026-09-27 (cont. 11) — D-004 e D-002 fechadas

- Pesquisa web nova em `DISCOVERY.md` §5: OSM tem "device ban"; precedente de junho 2026 em que contas foram banidas por ver vídeos ilimitados (bug do jogo, não bot) e a sanção foi mantida — sinal de que a deteção olha para o padrão/volume, não só para a intenção. Refletido também em `RISKS_AND_COMPLIANCE.md`.
- **D-004 aceite:** dono aceita risco A3 já, A4 quando D-012 estiver resolvida; testes começam em conta secundária "a seu tempo"; registado que a conta secundária não isola 100% (device ban).
- **D-002 aceite:** alcance = A3 (treinos, transferências automáticos). A4 (anúncios) fica preso a D-012, que passou a depender só de **infraestrutura** (onde correr algo 24/7 sem gastar dinheiro — servidor vs. Raspberry Pi), não de risco.
- Sem código novo.
- **Próximo passo:** decidir D-006 (interface) e D-007 (licença), agora destravadas; D-012 fica para quando o dono resolver a questão de infraestrutura.

## 2026-09-27 (cont. 10) — Teoria fechada, incluindo vídeos e finanças

- Acrescentados em `THEORY.md`: análise do adversário e objetivo de época (§11); vídeos de treino, loja e finanças (§12); poupança e juros (§13, ≈2% por dia de jogo).
- Correções relevantes: o critério de "mais forte/mais fraco" é a **média do plantel 0–100 mostrada antes do jogo** (não o preço); a duração dos treinos **varia** (8 h normal, 2 h em eventos) e nunca deve ser fixada no código.
- Dono confirma **"é tudo"**. A recolha de teoria está terminada.
- **Por confirmar** (só observando o jogo): mínimos por posição; multiplicador do preço máximo; desconto do "SALE"; taxa do juro (só 1 exemplo); horas de renovação do mercado; melhoramentos por nível do estádio; se os "4 vídeos/hora" e os "10 vídeos" se renovam de hora a hora.
- **Próximo passo:** decidir o que automatizar, por que ordem (D-002) e a postura de risco (D-004). Sem código novo.

## 2026-09-27 (cont. 9) — Teoria do jogo completa (segundo o dono)

- Registados: guarda-redes/moedas/jogador fraco (§7.8; palpite do dono: evitar dinheiro parado), **estádio** (§8), **patrocinadores** (§9), **médico e advogado** (§10), Legend e Inform players (§7.6). Glossário atualizado.
- O dono diz que **"passámos tudo do jogo"**.
- **Próximo passo:** decidir o que automatizar e por que ordem (D-002), e a postura de risco (D-004), antes de qualquer contacto com o jogo. Sem código novo.

## 2026-09-27 (cont. 8) — Transferências e plantel: fechado

- Dono explicou a estratégia de transferências e gestão de plantel; registada em `THEORY.md` §7 (7.1–7.7, com resumo no topo) e **fechada por ele**.
- Usadas 4 capturas de ecrã (plantel em 3 imagens, lista de transferências numa): confirmam colunas, ícones (em treino, na lista de transferências, cartão amarelo), etiqueta "SALE" e como distinguir vendedores utilizadores.
- Pedidos de automação, não urgentes: **treinos** (recolher e recolocar), **coins via anúncios** (para os amigáveis, ver §6), **notificação de "SALE" novos** (§7.7). Ver `PROJECT_BRIEF.md`.
- **Por confirmar** (todos marcados [?] em `THEORY.md`): mínimo de jogadores por posição; número de slots atual (4 ou 6); multiplicador do preço máximo (~2,5×?); horas de renovação do mercado; desconto do "SALE".
- Sem código novo. **Próximo passo:** o dono diz se ainda tem teoria para juntar (ponto (c) dele) ou se passamos ao que automatizar (D-002, D-004).

## 2026-09-27 (cont. 7) — Checklist de preparação do jogo registada

- *(Acrescento)* Amigáveis sobem stats de jogadores; o dono faz ≥1/dia, às vezes mais (4 boss coins cada). É o motivo principal para querer farmar coins com automação.

- Dono descreveu a checklist pré-jogo (10 pontos: 8 que faz quase sempre, incluindo o amigável que faz SEMPRE; 2 que custam muitas coins e usa por vezes — treino secreto e estágio). Registada em `THEORY.md` §6.
- Treinos automáticos confirmados como automação desejada, não urgente (`PROJECT_BRIEF.md`). Ligação notada: 4 sessões concluídas **no dia do jogo**.
- Sem código novo. Dono ainda pode acrescentar mais teoria/metodologia.

## 2026-09-27 (cont. 6) — Correção de rumo

- O dono disse que a parte tática/especialistas **gere ele sozinho**; só a explicou para ficar registada e para o Claude perceber a sua forma de jogar. O Claude tinha ido construir código e testes sem isso ser pedido → regra 10 no `CLAUDE.md` (registar antes de construir).
- Respostas registadas em `THEORY.md`: árbitro/desarme é contextual (véspera de jogo duro → não arriscar vermelhos; jogo difícil → talvez Agressivo); treino: nunca listados para venda, 30+ treina outros; treinador universal fora de âmbito.
- **Git/GitHub é do dono** (regra 9, D-008). Retirada a proposta de `git init`.
- O dono **ainda tem mais teoria e metodologia para juntar**. Aguardar.
- O código de `src/` e `tests/` fica (é pequeno e o dono pode apagá-lo), mas **não é para expandir** sem o dono pedir. Ponto pendente sobre "rating parecido" (`similar_margin`) só interessa se um dia se automatizar a escolha de formação.
- **Próximo passo:** o dono continua a explicar a teoria/metodologia; ao terminar, decide-se o que automatizar (coins/treinos/transferências) e D-004.

## 2026-09-27 (cont. 5) — Primeiro código: lógica pura

- Dono respondeu aos [?] de `THEORY.md` e à política de treino; linguagem = Python (D-001).
- Criado o projeto Python (`pyproject.toml`, `src/osmbot/`, `tests/`, `.venv/` ignorado): `models.py`, `theory/specialists.py`, `theory/tactics.py`, `training/policy.py`. **44 testes a passar** (dados sintéticos; nada tocou no jogo).
- `THEORY.md` reescrito com as respostas; ficam poucos [?] (ver abaixo) e várias suposições marcadas [S].
- **Por confirmar (dono):** `similar_margin` (o que é rating "parecido"); Rigoroso → Agressivo?; limite exato de "30+"; uso do treinador universal; listados para venda excluídos do treino?
- **Próximo passo:** ou (a) `git init` + primeiro commit, ou (b) cliente de API offline (parsing de respostas com fixtures) e agendamento inteligente dos treinos, ou (c) decidir D-004 para começar a verificar endpoints. Aguardar escolha do dono.

## 2026-09-27 (cont. 4) — Teoria tática registada

- D-011 aceite (construir de raiz); D-013 registada (contacto com o jogo adiado).
- Dono explicou a teoria: formações vs força do adversário, sliders, desarme por árbitro, especialistas (capitão, penáltis, livres, cantos). Registada em `docs/THEORY.md`, com pontos **[?]** por confirmar.
- Ainda por responder: linguagem (recomendado Python) e política de seleção de treinos.
- **Próximo passo:** dono responde aos [?] de `THEORY.md`; depois estrutura do projeto + `specialists` (função pura mais simples e sem ambiguidade) + gestor de treinos.

## 2026-09-27 (cont. 3) — Análise do `osm-ad-bot`

- Lido o código completo (clone em scratchpad, fora do projeto). Resultado em `docs/PRIOR_ART.md`.
- Achados-chave: API interna mapeada (host `web-api.onlinesoccermanager.com`, `/api/v1/leagues/{L}/teams/{T}/...`); treinos são **HTTP puro**; anúncios exigem browser e o repo **forja callbacks de recompensa**; sem endpoints de compra/venda; sem LICENSE.
- Recomendação: construir de raiz (D-011), começar pelos treinos, depois transferências; anúncios em separado (D-012).
- **Próximo passo:** dono decide D-004/D-011/D-012. Depois, verificação read-only dos endpoints com OK explícito.

## 2026-09-27 (cont. 2) — Pivot do propósito

- Dono esclarece: teoria tática já é dele, nada a testar, pouco a automatizar. Quer automatizar **coins via vídeos, encurtar treinos, cortar vídeos promocionais e possivelmente transferências** (D-010; D-009 substituída).
- Alcance passa a A3/A4. Prior art relevante: `nsozturk/osm-ad-bot` faz exatamente ads + treinos (ver `DISCOVERY.md`).
- **Bloqueio:** D-004 (postura de risco / que conta) tem de ser decidida antes de qualquer contacto com o jogo.
- **Próximo passo possível sem tocar no jogo:** ler o código-fonte público de `nsozturk/osm-ad-bot` para perceber como ads/treinos funcionam (auth, endpoints reportados, rate limits).

## 2026-09-27 (cont.) — Propósito definido (substituído acima)

- Dono afirma ter uma teoria de jogo com resultados comprovados; o bot deve codificá-la (D-009).
- Domínios indicados: táticas vs mais forte, táticas vs mais fraca, política de transferências, capitães/roles, etc.
- **Próximo passo:** extrair a teoria em formato estruturado (regras, inputs, outputs) e recolher os resultados que a sustentam. Só depois fechar alcance (D-002) e risco (D-004).

## 2026-09-27 — Sessão 1: arranque e descoberta inicial

**Feito**
- Esclarecido que OSM = Online Soccer Manager (D-000).
- Pesquisa web sobre viabilidade: sem API pública oficial encontrada; 4 repos de prior art (todos automação de browser; foco em farm de moedas); ToS proíbem bots e scraping sem autorização escrita.
- Criada a estrutura: `CLAUDE.md`, `docs/*`, `.gitignore`, `README.md`.

**Por fazer / bloqueios**
- Tópico do fórum "Osm API" e artigo de suporte "What's considered cheating" não puderam ser lidos automaticamente (Anubis / 403).
- Nada foi testado contra o jogo real.

**Próximo passo**
- Utilizador responde às perguntas de `OPTIONS.md` §E e decide D-004 (postura de risco) e D-002 (alcance).
- Depois: decidir se se faz observação de rede na web app (só com OK explícito), e só então stack.
