# OSMbot

Exploração de um bot para o **Online Soccer Manager** (Gamebasics).

> **Estado (0.14.9):** o bot trabalha sozinho no Windows e no Mac, sem deixar o PC adormecer (treinos em rotação entre os titulares, primeiro quem tem mais a ganhar, com os de 30+ também considerados nos eventos de veteranos, e, no início de um evento de treinos, os treinos postos antes acabados com boss coins, depósito na poupança antes de cada jogo (e em cada dia da pré-época ou sem jogo), estádio (acelerado com boss coins nos eventos de estádio, até 40 por evento), patrocinadores, vídeos da loja, de treino e de dinheiro, recompensas diárias (as boss coins e o dinheiro do clube que ficam no inventário vão para a carteira, e a janela das boss coins por reclamar não trava os vídeos), itens do inventário usados antes de expirarem (treinador universal, sacos), 4 amigáveis ao longo do dia antes de cada jogo (8 no Intense Friendlies; também todos os dias da pré-época), análise do adversário e especialistas pela regra nas 4 h antes (e, no resto do tempo, o analista a passar pelos outros clubes da liga, para os registos), médico e advogado, aviso de vagas e de vendas na lista de transferências (e de quem está à venda há mais do dobro do normal para o preço), compras e lucro de cada venda no registo, histórico de transferências das ligas, registo do motor de transferências e dos jogadores "SALE", calendário de eventos lido do fórum e mostrado na janela, e registos para estudar treinos, amigáveis, jogos, médico e advogado), numa **janela de programa** em português ou inglês, com ícone junto ao relógio (o quadro de consola continua disponível). A janela mostra também a força das equipas (a do adversário estimada antes da análise e real depois), o objetivo da época com os 3 primeiros da tabela, a jornada (J29/38) com o calendário da época ao passar o rato (adversários com o emblema, taça, folgas e resultados), os ciclos que faltam em cada nível do estádio, a tabela do valor do plantel à volta do clube, os titulares cansados sem suplente, com opções "SALE", e a melhor compra "SALE" do momento no mercado do jogo, com a posição específica (revenda de jogadores de 10–40 M de valor ou reforço onde o titular da mesma posição específica está abaixo da média do 11, e primeiro um suplente quando uma posição não tem ninguém em forma fora do 11, a mais barata face ao valor; as 3 melhores ao passar o rato); avisa (a amarelo, com o porquê ao passar o rato) quando o banco (por lugares: GR, DEF, MED, ATA; diz também quem está num lugar de outra posição), a tática (estilo de jogo, instruções e barras pela regra de cada formação, desarme para o árbitro, formação pela força com os bónus do jogo e a casa, 4-3-3 B fora de casa (e aceite em casa), só o 5-2-3 contra um adversário claramente mais forte (mais de 12 %), contando os melhores do adversário quando o onze dele tem um lugar vazio, ou, com um lado sem laterais ou extremos em forma (ou a poupar para um jogo importante), as formações de 3 defesas ou de 2 PL) ou os especialistas fogem à regra (um suplente melhor do que o titular mas a poupar para um jogo importante fica só como nota, tal como um onze com menos de 3 jogadores acima ou abaixo de 26 anos), e avisa quem convém poupar no próximo jogo para não chegar cansado a um jogo importante (adversário mais forte ou rival direto), e diz quem está fora da sua posição específica; o treino secreto e o estágio aparecem no pré-jogo com os ícones do jogo. Cada jornada fica registada com o jogo real de todos os clubes: onze, notas, eventos ao minuto e a força de cada equipa nesse jogo; e cada jogo dos teus clubes com o relatório do comentador. O bot faz também a previsão dos jogos reais, reclama o prémio de fim de época e avisa no topo das missões que tens de fazer à mão. Ver [`CHANGELOG.md`](CHANGELOG.md) e [`docs/`](docs/).

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

`osmbot` sem argumentos (ou o `OSMbot.exe` da pasta portátil, que não abre consola) abre a **janela** (D-024; no Mac, duplo clique em `tools/OSMbot.command`):

- abre pequena, com **Abrir**, **Login** e **Sair**. Num PC novo, começa pelo Login;
- **Abrir** mostra "A carregar o jogo…", põe o bot a trabalhar e a janela cresce para o **quadro** (D-030): em cima as diárias (ao passar o rato: o prémio de hoje, as missões e o prémio do dia), o próximo evento (ao passar o rato, o calendário do mês), o inventário (ao passar o rato, o que expira e quando) e "A trabalhar desde"; um cartão por clube na cor do clube (próximo jogo, liga, taça, valor do plantel, dinheiro e vendas, patrocinadores, estádio, treinos, médico e advogado, pré-jogo); à direita as boss coins e a linha do tempo (o que vem a seguir por cima do "agora", o que o bot já fez por baixo). O quadro relê o jogo de 3 em 3 min;
- menu **Bot**: Iniciar, Parar (pára na pausa seguinte), Login, Sair. Menu **Ver**: Atualizar, Avisos e erros, Pasta dos logs, Capturas das falhas. Menu **Idioma / Language**: Português ou English (D-031). Menu **Ajuda**: Sobre;
- com o bot a trabalhar, fechar a janela (X) **só a esconde**: o **ícone junto ao relógio** (logótipo com bolinha verde a trabalhar, cinzenta parado) volta a abri-la. Para sair: Bot → Sair, ou o ícone → Sair. Sem notificações do Windows.

O resto é por comandos:

| Comando | O que faz |
|---|---|
| `osmbot menu` | O menu antigo, na consola (Iniciar, Login, Sair), com o quadro em texto |
| `osmbot login` | Abre o Firefox para entrares; fecha a janela para guardar a sessão |
| `osmbot ativo` | **Modo ativo**: recolhe e treina quando os treinos acabam, sobe o estádio (recolhendo cada obra acabada antes da seguinte), assina patrocinadores, vê os vídeos (loja, treino, dinheiro), reclama as recompensas diárias, faz 4 amigáveis ao longo do dia antes de cada jogo (8 durante um Intense Friendlies), a análise do adversário e os especialistas pela regra nas 4 h antes (o que ainda não estiver feito; o analista é levantado logo que acaba), usa os itens do inventário que vão expirar, regista os jogos das ligas, põe os lesionados no médico e os suspensos no advogado, e avisa de vagas na lista de transferências; quadro em tempo real. Ctrl+C para parar |
| `osmbot ativo --simular` | Uma passagem sem escrever nada |
| `osmbot ativo --sem-anuncios` / `--sem-quadro` | Sem vídeos / linhas simples em vez do quadro |
| `osmbot status`, `treinos`, `slots` | Só leitura |
| `osmbot recolher`, `treinar` | Escrevem na conta; `--simular` mostra o plano |
| `osmbot pasta-logs [pasta do repo]` | Mostra ou escolhe o repo para onde vai o registo (`logs/<PC>/`), se não for encontrado sozinho; copia o registo antigo |
| `osmbot recompensas` | Reclama as recompensas diárias (início de sessão, missões, vídeos acumulados); ficam no inventário (no modo ativo, o que vai expirar usa-se 4 h antes); `--simular` mostra o plano |

Só **uma máquina com o bot ligado de cada vez**. O registo fica em `~/.osmbot/bot.log` e também no repo, em `logs/<nome do PC>/AAAA-MM-DD.log` (D-022), para o ver noutra máquina depois do teu commit/push. O bot encontra o repo sozinho (D-023): o código de onde corre, ou uma pasta `OSMbot` ao lado da pasta do bot ou na pasta pessoal, `Documents` ou `Desktop`. Só se o repo estiver noutro sítio: `osmbot pasta-logs <pasta do repo>`.

## Mac

Corre a partir do código (sem pacote): `git pull` e duplo clique em `tools/OSMbot.command` (cria o venv na primeira vez e abre a janela; o ícone fica na barra de cima). Com o bot a trabalhar, o Mac não adormece nem apaga o ecrã (`caffeinate`, só enquanto o bot corre); **fechar a tampa adormece-o na mesma**, por isso deixa-o aberto e ligado à corrente. Se o macOS bloquear o atalho na primeira vez: botão direito → Abrir.

## Mac: app e .dmg

`python tools/build_mac.py --zip --dmg` (no Mac, com o venv ativado) cria, em `dist/mac/`, a `OSMbot.app` (Python, dependências e Firefox lá dentro), `OSMbot-<versão>-mac-portable.zip` e `OSMbot-<versão>-mac.dmg` (abre-se e arrasta-se o OSMbot para Aplicações). A app é do processador do Mac que a constrói e não é assinada pela Apple: na 1.ª vez, botão direito → Abrir. Comandos pelo Terminal: `OSMbot.app/Contents/MacOS/OSMbot status`. Ver D-061.

## Windows: pasta portátil e instalador

`python tools/build_portable.py --zip --installer` cria, em `dist/windows/` (fora do git), `OSMbot-<versão>-windows-portable.zip` (Python, dependências e Firefox lá dentro; abre-se `OSMbot.exe`, só a janela, sem consola; os comandos correm com `OSMbot-consola.exe`, p. ex. `OSMbot-consola.exe menu`) e `OSMbot-<versão>-windows-setup.exe` (instalador por utilizador, sem administrador; precisa do Inno Setup para ser construído). A sessão não viaja: fica em `%USERPROFILE%\.osmbot` de cada PC e faz-se *Login* uma vez em cada um. Ver `docs/DECISIONS.md` D-016.

## Documentação

- [`CLAUDE.md`](CLAUDE.md) — contexto para o Claude Code
- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — objetivo e critérios
- [`docs/DISCOVERY.md`](docs/DISCOVERY.md) — o que é possível
- [`docs/OPTIONS.md`](docs/OPTIONS.md) — opções consideradas
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — decisões
- [`docs/WORKLOG.md`](docs/WORKLOG.md) — diário de sessões
