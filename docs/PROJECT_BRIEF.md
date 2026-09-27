# Project Brief

*Última atualização: 2026-09-27*

## Objetivo (provisório)

**Poupar tempo ao dono automatizando tarefas repetitivas** no Online Soccer Manager (D-010):

1. Obter coins através de vídeos promocionais. **Motivo (dono):** os jogos amigáveis custam 4 boss coins cada, sobem stats de jogadores, e o dono faz sempre pelo menos 1 por dia, às vezes mais; precisa de coins para os sustentar. Ver `THEORY.md` §6.
2. **Treinos (prioridade confirmada, não urgente):** sempre que um treino acaba, recolhê-lo e voltar a pôr um jogador a treinar, sem o dono ter de o fazer. A escolha do jogador segue `THEORY.md` §5 (melhor da posição, sem 30+, nunca listados para venda). Não é para agora; fica na lista do que se vai automatizar.
3. Cortar tudo o que dependa de ver vídeos promocionais. Os 3 usos de vídeos que o jogo oferece (detalhe em `THEORY.md` §12):
   - **Treinos:** cada vídeo tira 2 h; máx. 4 por hora (8 h).
   - **Loja:** 1 boss coin por vídeo; ~10 por ciclo de 1 h; recompensa extra ao 10.º (treinador universal, troca de posição, etc.).
   - **Finanças:** 3 vídeos por dia (~300k, ~600k, 3 boss coins).
   Todos com limites impostos pelo servidor; os anúncios continuam a ser a parte de maior risco (D-012).
4. Possivelmente parte da gestão de transferências (por especificar).
5. **Notificação de jogadores novos na lista de transferências** (pedido do dono, não urgente): em ligas com muitos jogadores os novos são comprados logo, por isso quer ser avisado quando aparecem. Ver `THEORY.md` §7.7.

Fora do alcance inicial: táticas. O dono tem uma teoria de jogo própria, com bons resultados, que aplica ele mesmo (ver histórico em `WORKLOG.md`); não há nada a codificar ou testar aí para já.

**Consequência:** isto é automação com escrita na conta (A3/A4 em `OPTIONS.md`) — o cenário de maior risco face aos ToS. A conta em risco é a conta principal do dono, onde estão os resultados que ele quer proteger.

## Não-objetivos (por agora)

- Escolher linguagem/framework.
- Escrever código.
- Contornar mecanismos anti-abuso do jogo de forma agressiva.

## Critérios para sair da fase de descoberta

- [ ] Escolhido o **alcance** (D-002 em `DECISIONS.md`).
- [ ] Definida a **postura de risco** face aos ToS (D-004).
- [ ] Verificada, com o utilizador presente, a forma como o jogo comunica (web app, chamadas de rede) — só se a postura de risco o permitir.
- [ ] Escolhida a stack (D-001 reservado; ver DECISIONS).

## Quem

- Dono do projeto: o autor do repositório (contactos no perfil do GitHub).
- Destino provável: repositório público no GitHub → os docs têm de ser legíveis para terceiros e sem segredos.
