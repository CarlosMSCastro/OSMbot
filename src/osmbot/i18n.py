"""The window in Portuguese or English (D-031). Pure apart from remembering the choice.

The bot keeps writing everything in Portuguese (its log never changes language, so logs from every PC compare).
The window passes each text it shows through ``tr``: in English it swaps whole texts (``WORDS``) and texts with
names or numbers in them (``PATTERNS``); a text with no translation stays in Portuguese.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def _between(text: str) -> str:
    """'(mudou entre 05:50 e 06:00)' -> '(changed between 05:50 and 06:00)': when an event's change was seen."""
    return re.sub(r" \(mudou entre (\S+) e (\S+)\)", r" (changed between \1 and \2)", text)


LANGUAGES = {"pt": "Português", "en": "English"}
_language = "pt"


def config_file() -> Path:
    from osmbot.logs import CONFIG_FILE

    return CONFIG_FILE


def load_language() -> str:
    """The language chosen on this PC (Portuguese until one is chosen)."""
    global _language
    try:
        chosen = json.loads(config_file().read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError):
        chosen = None
    _language = chosen if chosen in LANGUAGES else "pt"
    return _language


def set_language(code: str, save: bool = True) -> None:
    global _language
    _language = code if code in LANGUAGES else "pt"
    if save:
        path = config_file()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        data["language"] = _language
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def language() -> str:
    return _language


def ordinal(number: str) -> str:
    n = int(number)
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


WORDS = {
    # menus, buttons, start screen, status
    "Bot": "Bot", "Iniciar": "Start", "Parar": "Stop", "Login": "Login", "Sair": "Quit", "Ver": "View",
    "Atualizar": "Refresh", "Avisos e erros": "Warnings and errors", "Pasta dos logs": "Logs folder",
    "Capturas das falhas": "Failure screenshots", "Ajuda": "Help", "Sobre o OSMbot": "About OSMbot",
    "Idioma / Language": "Idioma / Language", "Abrir": "Open",
    "A carregar o jogo…": "Loading the game…", "A parar…": "Stopping…", "A ler o jogo…": "Reading the game…",
    "Parado": "Stopped", "a trabalhar…": "working…", "Parado · Bot → Iniciar para voltar a trabalhar": "Stopped · Bot → Start to work again",
    "● Sessão iniciada": "● Logged in", "● Sem sessão: carrega em Login primeiro.": "● Not logged in: press Login first.",
    "Login: entra no jogo no Firefox e FECHA essa janela.": "Login: sign in to the game in Firefox and CLOSE that window.",
    "Trabalha por ti no Online Soccer Manager: treinos, vídeos, estádio, patrocinadores, amigável e análise antes do "
    "jogo, médico e advogado, e avisa das vagas na lista de transferências.":
        "Works for you in Online Soccer Manager: trainings, videos, stadium, sponsors, the friendly and the analysis "
        "before the match, doctor and lawyer, and it tells you about free transfer-list slots.",
    "O OSMbot já está aberto (vê o ícone junto ao relógio).": "OSMbot is already open (see the icon next to the clock).",
    "Hora": "Time", "Tipo": "Type", "Mensagem": "Message", "Erro": "Error", "Aviso": "Warning",
    "OSMbot — Avisos e erros": "OSMbot — Warnings and errors",
    # board titles and labels
    "DIÁRIAS": "DAILY", "BOSS COINS": "BOSS COINS", "A SEGUIR": "UP NEXT", "TREINOS": "TRAINING", "ESTÁDIO": "STADIUM",
    "AGORA": "NOW", "PRÉ-JOGO": "PRE-MATCH", "Valor plantel": "Squad value", "Dinheiro": "Money",
    "Fora da regra": "Out of your rule", "Aceite": "Accepted", "Vendas": "Sales", "Normal a este preço": "Usual at this price", "Valor do plantel": "Squad value", "Clube": "Club", "J": "P", "DG": "GD", "Valor": "Value", "× valor": "× value",
    "Jogadores": "Players", "Média": "Avg", "Pos": "Pos", "Força": "Strength", "Jogador": "Player", "Idade": "Age",
    "Preço": "Price", "Lucro": "Profit",
    "Campeões": "Champions", "Patrocinadores": "Sponsors", "Cansados": "Tired", "CASA": "HOME", "FORA": "AWAY", "em": "in",
    # club card
    "Treinos": "Training", "Campo": "Pitch", "Capacidade": "Capacity", "no máximo": "at max", "parado": "idle",
    "Médico": "Doctor", "Advogado": "Lawyer", "ninguém": "nobody", "pronto": "ready", "a levantar": "to collect",
    "ATA": "FWD", "MED": "MID", "DEF": "DEF", "GR": "GK", "—": "—",
    "Amigável": "Friendly", "Amigáveis": "Friendlies", "Análise": "Analysis", "Onze": "Line-up", "Posições": "Positions", "Em forma": "Fit",
    "Banco": "Bench", "Especialistas": "Specialists", "4 treinos": "4 trainings",
    "pré-eliminatória": "preliminary round", "32 avos-de-final": "round of 64", "16 avos-de-final": "round of 32",
    "oitavos-de-final": "round of 16", "quartos-de-final": "quarter-finals", "meias-finais": "semi-finals",
    "final": "final", "vencedor": "winner", "Pré-eliminatória": "Preliminary round", "32 avos-de-final ": "Round of 64",
    "Oitavos-de-final": "Round of 16", "Quartos-de-final": "Quarter-finals", "Meias-finais": "Semi-finals",
    "Final": "Final", "Vencedor": "Winner",
    # daily rewards
    "Início de sessão por reclamar": "Login reward to claim", "Prémio diário por reclamar": "Daily prize to claim",
    "Prémio diário": "Daily prize",
    # timeline
    "já": "now", "Vídeos da loja": "Shop videos", "Acelerar treinos": "Speed up trainings",
    "Vídeos de dinheiro": "Money videos", "Reward cumulativo": "Cumulative reward", "Novo dia (diárias)": "New day (daily)",
    "disponíveis": "available", "disponível": "available", "por reclamar": "to claim",
    "Vídeo de treino −2h": "Training video −2h", "Vídeo de dinheiro": "Money video", "Treinos recolhidos": "Trainings collected",
    "A treinar": "Training started", "Depósito na poupança": "Savings deposit", "Patrocinador assinado": "Sponsor signed", "Missões": "Missions",
    "Início de sessão": "Login reward", "Vídeos acumulados": "Cumulative videos",
    # what the bot is doing
    "à espera": "waiting", "por levantar": "to collect", "acaba em": "ends in", "não dá": "not allowed", "estádio": "stadium", "ler o jogo": "reading the game", "médico e advogado": "doctor and lawyer", "inventário": "inventory", "Treinador universal": "Universal trainer", "livre": "free", "Treino secreto": "Secret training", "Estágio": "Training camp", "Marcado para o próximo jogo": "Booked for the next match", "Não marcado": "Not booked", "Sem jogo nesta jornada": "No match this round",
    "patrocinadores": "sponsors", "pré-jogo": "pre-match", "recolher e pôr treinos": "collecting and starting trainings",
    "recompensas": "rewards", "poupança": "savings",
}

_PART = {"campo": "pitch", "treinos": "training", "capacidade": "capacity"}


def _w(text: str) -> str:
    return WORDS.get(text, text)


def _ordinal(number: str) -> str:
    """"1" -> "1st", "2" -> "2nd", "11" -> "11th"."""
    n = int(number)
    return number + ("th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


_TACKLE = {"Cuidadoso": "Careful", "Normal": "Normal", "Agressivo": "Aggressive", "Extremo": "Extreme"}
_REFEREE = {"muito rigoroso": "very strict", "rigoroso": "strict", "normal": "average", "brando": "lenient",
            "muito brando": "very lenient"}
def _an(word: str) -> str:
    return ("an " if word[:1] in "aeiou" else "a ") + word


_SPECIFIC = {"MO": "CAM", "MC": "CM", "DC": "CB", "PL": "ST", "MDC": "CDM", "GR": "GK", "ME": "LM", "EE": "LW",
             "DE": "LB", "MD": "RM", "ED": "RW", "DD": "RB"}
WORDS.update({code: name for code, name in _SPECIFIC.items() if code not in WORDS})  # the SALE hover's "Pos" column
def _days(span: str) -> str:
    """A time over a day in English: "2 dias e 3h00" → "2 days and 3h00" (game/dashboard.span)."""
    return re.sub(r"(\d+) (dias?) e ", lambda m: f"{m[1]} day{'s' if m[2] == 'dias' else ''} and ", span)


_ROLE = {"Capitão": "Captain", "Penáltis": "Penalties", "Livres": "Free kicks", "Cantos": "Corners"}
PATTERNS = [(re.compile(pattern), replace) for pattern, replace in (
    # pre-match warnings (THEORY.md section 21)
    (r"^(.+) (\d+) entra antes de (.+) (\d+)$", lambda m: f"{m[1]} {m[2]} comes on before {m[3]} {m[4]}"),
    (r"^(.+) (\d+) no banco, (.+) (\d+) a jogar$", lambda m: f"{m[1]} {m[2]} on the bench, {m[3]} {m[4]} playing"),
    (r"^(.+) \((\w+|\?)\) a jogar a (\w+)$",
     lambda m: f"{m[1]} ({_SPECIFIC.get(m[2], m[2])}) playing as {_SPECIFIC.get(m[3], m[3])}"),
    (r"^Desarme (\w+) com árbitro (.+): devia ser (.+)$",
     lambda m: f"Tackling {_TACKLE.get(m[1], m[1])} with {_an(_REFEREE.get(m[2], m[2]))} referee: should be "
               + " or ".join(_TACKLE.get(w, w) for w in m[3].split(" ou "))),
    (r"^Formação (.+?): devia ser de 5 defesas \(adversário mais forte\)$",
     lambda m: f"Formation {m[1]}: should have 5 defenders (stronger opponent)"),
    (r"^Formação (.+?): devia ser (.+)$", lambda m: f"Formation {m[1]}: should be {m[2]}"),
    (r"^4-4-2 B aceite: (.+)$", lambda m: "4-4-2 B accepted: " + re.sub(
        r"sem (\w+) (em forma|no plantel)", lambda w: f"no {'fit ' if w[2] == 'em forma' else ''}"
        f"{_SPECIFIC.get(w[1], w[1])}{' in the squad' if w[2] == 'no plantel' else ''}", m[1]).replace(" fora", " out")),
    (r"^(Capitão|Penáltis|Livres|Cantos): (.+), pela regra (.+)$",
     lambda m: f"{_ROLE[m[1]]}: {m[2]}, your rule says {m[3]}"),
    # card
    (r"(\d+)\.º Campeonato", lambda m: f"{ordinal(m[1])} in the league"),
    (r"ativo até (\d\d:\d\d)", lambda m: f"active until {m[1]}"),
    (r"🏆 (.+)", lambda m: f"🏆 {_w(m[1])}"),
    (r"[Ee]liminado nos (.+)", lambda m: f"Out in the {_w(m[1])}"),
    (r"vs (.+) \((\d+)\.º\)", lambda m: f"vs {m[1]} ({ordinal(m[2])})"),
    (r"(\w+) · TAÇA", lambda m: f"{_w(m[1])} · CUP"),
    (r"(\d+)\.º", lambda m: ordinal(m[1])),
    (r"(\d+) jogadores · média (.+)", lambda m: f"{m[1]} players · avg {m[2]}"),
    (r"(\d+) vagas? vazias? nos patrocinadores", lambda m: f"{m[1]} empty sponsor slot" + ("s" if m[1] != "1" else "")),
    (r"(\d+) vagas? livres? na lista de transferências",
     lambda m: f"{m[1]} free slot{'s' if m[1] != '1' else ''} on the transfer list"),
    (r"(.+) (\d+)%: se jogar contra o (.+), chega a ~(\d+)% contra o (.+)",
     lambda m: f"{m[1]} {m[2]}%: if he plays {m[3]}, he faces {m[5]} at ~{m[4]}%"),
    (r"(.+) à venda há (.+) \(normal ~(.+) a este preço\)",
     lambda m: f"{m[1]} on the list for {_days(m[2])} (usually ~{_days(m[3])} at this price)"),
    (r"(.+) à venda há (.+)", lambda m: f"{m[1]} on the list for {_days(m[2])}"),
    (r"^(.+): ~((?:\d+ dias? e )?\d+h\d\d)$", lambda m: f"{m[1]}: ~{_days(m[2])}"),  # the stale hover
    (r"(.+) vendido · (.+)", lambda m: f"{m[1]} sold · {m[2]}"),
    (r"(.+)/ronda", lambda m: f"{m[1]}/round"),
    (r"PRÉ-JOGO · (.+)", lambda m: f"PRE-MATCH · {m[1]}"),
    (r"(\d+) jogos?", lambda m: f"{m[1]} game{'s' if m[1] != '1' else ''}"),
    (r"(\d+) j", lambda m: f"{m[1]} g"),
    (r"1 jogo · não dá", lambda m: "1 game · not allowed"),
    (r"(\d+) jogos? · à espera", lambda m: f"{m[1]} game{'s' if m[1] != '1' else ''} · waiting"),
    (r"⚠ Cansados: (.+)", lambda m: f"⚠ Tired: " + re.sub(r"sem suplente (\w+)", lambda n: f"no cover {_w(n[1])}", m[1])),
    (r"(?:Força (\d+) · )?[Vv]alor do plantel (.+) · (\d+) jogadores · média (.+)",
     lambda m: (f"Strength {m[1]} · squad value" if m[1] else "Squad value") + f" {m[2]} · {m[3]} players · avg {m[4]}"),
    (r"Força (\d+)", lambda m: f"Strength {m[1]}"),
    (r"(▸ )?(\d+)\.º (.+) · (\d+) pts", lambda m: f"{m[1] or ''}{_ordinal(m[2])} {m[3]} · {m[4]} pts"),
    (r"Objetivo: (\d+)\.º( ou acima)?", lambda m: f"Goal: {_ordinal(m[1])}" + (" or better" if m[2] else "")),
    (r"(?s)SALE (\w+) que cabem no dinheiro:\n(.+)",
     lambda m: f"SALE {_w(m[1])} you can afford:\n" + re.sub(r"(?m)^(\w+) ", lambda p: f"{_w(p[1])} ", m[2]).replace(" anos)", " years)")),
    (r"Nenhum SALE (\w+) cabe no dinheiro", lambda m: f"No SALE {_w(m[1])} you can afford"),
    (rf"^(ATA|MED|DEF|{'|'.join(_SPECIFIC)}) (\d+) · (.+)$", lambda m: f"{_w(m[1])} {m[2]} · {m[3]}"),  # the SALE stripe's player
    (r"^lucro ~(.+)$", lambda m: f"profit ~{m[1]}"),
    (r"^((?:suplente|reforço|pechincha).*)$", lambda m: re.sub(r"lugar (\d+) vazio", r"place \1 empty", m[1].replace(" sem suplente", " with no backup")
     .replace("suplente", "backup").replace("reforço", "upgrade").replace("pechincha", "bargain"))),
    (r"^Lugar (\d+) do 11 vazio(.*)$", lambda m: f"Place {m[1]} of the eleven empty{m[2]}"),
    (r"^Onze com só (\d+) jogador(?:es)? (acima|abaixo) de (\d+) anos \(o jogo dá bónus negativo a um onze demasiado (jovem|velho)\)$",
     lambda m: f"Eleven with only {m[1]} player{'s' if m[1] != '1' else ''} {'over' if m[2] == 'acima' else 'under'} {m[3]} "
               f"(the game gives a penalty to a team too {'young' if m[4] == 'jovem' else 'old'})"),
    (r"^\? = esta liga não vendeu ao máximo nos últimos 3 dias$",
     lambda m: "? = this league has not sold at the maximum in the last 3 days"),
    # top bar, coins
    (r"Início de sessão \(dia (\d+)\)", lambda m: f"Login (day {m[1]})"),
    (r"Missões (\d+)/(\d+)", lambda m: f"Missions {m[1]}/{m[2]}"),
    (r"desde que o bot foi ligado \((.+)\)", lambda m: f"since the bot started ({m[1]})"),
    (r"A trabalhar desde (.+)", lambda m: f"Working since {m[1]}"),
    (r"Versão (.+)", lambda m: f"Version {m[1]}"),
    (r"Avisos e erros \((\d+)\)", lambda m: f"Warnings and errors ({m[1]})"),
    # timeline (future)
    (r"reabre às (.+)", lambda m: f"reopens at {m[1]}"),
    (r"Recolher treino (.+)", lambda m: f"Collect training {m[1]}"),
    (r"Treino (.+)", lambda m: f"Training {m[1]}"),
    (r"jogo · (casa|fora)( · taça)?", lambda m: f"match · {'home' if m[1] == 'casa' else 'away'}{' · cup' if m[2] else ''}"),
    (r"Jogo (.+)", lambda m: f"Match {m[1]}"),
    (r"(Amigável|Amigáveis|Análise) e (Amigável|Amigáveis|Análise)", lambda m: f"{_w(m[1])} and {_w(m[2])}"),
    (r"Amigáveis \((\d+)\)", lambda m: f"Friendlies ({m[1]})"),
    (r"(Treinos|Campo|Capacidade) (.+)", lambda m: f"{_w(m[1])} {m[2]}"),
    (r"(Médico|Advogado): levantar (.+)", lambda m: f"{_w(m[1])}: collect {m[2]}"),
    (r"(Médico|Advogado): (.+)", lambda m: f"{_w(m[1])}: {m[2]}"),
    # timeline (past)
    (r"Vídeos da loja ×(\d+)", lambda m: f"Shop videos ×{m[1]}"),
    (r"(Vídeo de treino −2h|Vídeo de dinheiro) ×(\d+)", lambda m: f"{_w(m[1])} ×{m[2]}"),
    (r"Estádio: (\w+) a subir", lambda m: f"Stadium: {_PART.get(m[1], m[1])} going up"),
    (r"(.+) pôs (.+) no (médico|advogado) \((.+)\)", lambda m: f"{m[1]} sent {m[2]} to the {'doctor' if m[3] == 'médico' else 'lawyer'} ({m[4]})"),
    (r"(.+) levantou o analista", lambda m: f"{m[1]} collected the analyst"),
    (r"(.+) levantou (.+)", lambda m: f"{m[1]} collected {m[2]}"),
    (r"(.+) enviou o analista a (.+) \((.+)\)", lambda m: f"{m[1]} sent the analyst to {m[2]} ({m[3]})"),
    # what the bot is doing
    (r"vídeo da loja (\d+)/(\d+)", lambda m: f"shop video {m[1]}/{m[2]}"),
    (r"vídeo de treino (.+)", lambda m: f"training video {m[1]}"),
    (r"vídeo de dinheiro (.+)", lambda m: f"money video {m[1]}"),
    # warnings and errors (the bot's log lines)
    (r"(.+) \(levantar\): o jogo não aceitou o pedido \((\d+)\); fica por fazer à mão até se ver o pedido certo",
     lambda m: f"{_w(m[1])} (collect): the game refused the request ({m[2]}); left to do by hand until the right request is seen"),
    (r"(.+): o jogo não aceitou o pedido \((\d+)\); fica por fazer à mão até se ver o pedido certo",
     lambda m: f"{_w(m[1])}: the game refused the request ({m[2]}); left to do by hand until the right request is seen"),
    (r"(.+): (\d+) slot\(s\) de venda livre\(s\) \((.+)\)", lambda m: f"{m[1]}: {m[2]} free sale slot(s) ({m[3]})"),
    (r"(.+): (.+) \((\w+)\) com (\d+)% de condição; convém descansar (\d+) jogos?",
     lambda m: f"{m[1]}: {m[2]} ({_w(m[3])}) at {m[4]}% fitness; better rest {m[5]} match{'es' if m[5] != '1' else ''}"),
    (r"Vídeos: erro \((.+)\); volto a tentar", lambda m: f"Videos: error ({m[1]}); retrying"),
    (r"(.+): erro \((.+)\); volto a tentar", lambda m: f"{_w(m[1])}: error ({m[2]}); retrying"),
    (r"(.+): (\d+) falha\(s\); volto a tentar", lambda m: f"{_w(m[1])}: {m[2]} failure(s); retrying"),
    (r"Treinos: (\d+) falha\(s\) ao escrever; volto a ver em (.+)", lambda m: f"Trainings: {m[1]} failed write(s); checking again in {m[2]}"),
    (r"(.+) (.+) fica à espera \((\d+)\)", lambda m: f"{m[1]} {m[2]} waits ({m[3]})"),
    (r"Não consegui ler o jogo \((.+)\)", lambda m: f"Could not read the game ({m[1]})"),
    (r"Loja: janela saltada", lambda m: "Shop: window skipped"),
    (r"(.+): sem boss coins para o amigável \((\d+)\); fica por fazer", lambda m: f"{m[1]}: not enough boss coins for the friendly ({m[2]}); not done"),
    (r"(.+): não sei quem é o próximo adversário; análise fica por fazer", lambda m: f"{m[1]}: next opponent unknown; analysis not done"),
    (r"(.+): nenhum clube disponível para amigável nesta jornada", lambda m: f"{m[1]}: no club available for a friendly this round"),
    (r"Lista de transferências: (.+) \((.+)\) à venda por (.+?)(?: \((\d+)% do máximo ≈ (.+)\))?$",
     lambda m: f"Transfer list: {m[1]} ({m[2]}) for sale at {m[3]}" + (f" ({m[4]}% of the maximum ≈ {m[5]})" if m[4] else "")),
    (r"Venda: (.+) \((.+)\) vendido por (.+?)(?: \((\d+)% do máximo ≈ (.+)\))?; à venda desde (.+), vendido até ([^,;]+)(?:, demorou ([^;]+))?(?:; lucro (.+?)(?: em (.+))?)?$",
     lambda m: f"Sale: {m[1]} ({m[2]}) sold for {m[3]}" + (f" ({m[4]}% of the maximum ≈ {m[5]})" if m[4] else "")
     + f"; for sale since {m[6].replace('antes de o bot começar a seguir', 'before the bot started following')}, sold by {m[7]}"
     + (f", took {m[8]}" if m[8] else "") + (f"; profit {m[9]}" + (f" in {m[10]}" if m[10] else "") if m[9] else "")),
    (r"Compra: (.+) \((.+)\) comprado por (.+?)(?: \((.+) × o valor\))?(?:, de (.+))?$",
     lambda m: f"Purchase: {m[1]} ({m[2]}) bought for {m[3]}" + (f" ({m[4]} × value)" if m[4] else "")
     + (f", from {m[5]}" if m[5] else "")),
    (r"Motor de transferências \((.+)\): (passou|sem descida de preços) entre (\S+) e (\S+); vendidos (\d+) de (\d+) à venda \(teus: (\d+) de (\d+)\)",
     lambda m: f"Transfer engine ({m[1]}): {'went round' if m[2] == 'passou' else 'no price drop'} between {m[3]} and {m[4]}; "
               f"sold {m[5]} of {m[6]} for sale (yours: {m[7]} of {m[8]})"),
    (r"SALE novos \((.+?)\): (\d+) · (.+?)(?: e mais (\d+))?$",
     lambda m: f"New SALE ({m[1]}): {m[2]} · {m[3].replace(' anos)', ' years)')}" + (f" and {m[4]} more" if m[4] else "")),
    (r"Evento: (.+)", lambda m: f"Event: {m[1]}"),
    (r"Indisponível: (.+)", lambda m: f"Unavailable: {m[1]}"),
    (r"Evento no jogo \((.+?)\): acabou, tudo normal(.*)", lambda m: f"Event in the game ({m[1]}): over, all back to normal" + _between(m[2])),
    (r"Evento no jogo \((.+?)\): (.+)", lambda m: f"Event in the game ({m[1]}): " + m[2].replace("treinador universal", "universal trainer")
     .replace("treinos", "trainings").replace("estádio", "stadium").replace("analista", "analyst").replace("médico", "doctor")
     .replace("advogado", "lawyer").replace("olheiro", "scout").replace("vagas de venda", "transfer list places").replace(" (mudou entre", " (changed between").replace(" e ", " and ")),
    (r"Calendário de eventos de (\S+): (\d+) · (.+)", lambda m: f"Events calendar for {m[1]}: {m[2]} · {m[3]}"),
    (r"Calendário de eventos: não consegui ler o fórum \((.+)\); tento amanhã",
     lambda m: f"Events calendar: could not read the forum ({m[1]}); trying again tomorrow"),
    (r"Calendário de eventos: o post do fórum mudou de formato; não percebi as datas",
     lambda m: "Events calendar: the forum post changed format; could not read the dates"),
    (r"Calendário de eventos: erro \((.+)\); tento amanhã", lambda m: f"Events calendar: error ({m[1]}); trying again tomorrow"),
    (r"Parou: (.+)", lambda m: f"Stopped: {m[1]}"),
    (r"Poupança: (.+) depositou (.+) antes do jogo \(poupança (.+)\)",
     lambda m: f"Savings: {m[1]} deposited {m[2]} before the match (savings {m[3]})"),
    (r"Poupança: (.+) depósito falhou \((\d+)\)", lambda m: f"Savings: {m[1]} deposit failed ({m[2]})"),
    (r"Poupança: (.+) o dinheiro não ficou todo na poupança", lambda m: f"Savings: {m[1]} not all the money went into savings"),
    (r"Poupança: o jogo recusou o depósito \((.+), (\d+)\); volto a tentar no próximo dia de jogo",
     lambda m: f"Savings: the game refused the deposit ({m[1]}, {m[2]}); trying again on the next match day"),
    # refused requests (D-032)
    (r"(Médico|Advogado) \(levantar\): o jogo recusou (.+) \((\d+)\); volto a tentar na próxima jornada",
     lambda m: f"{_w(m[1])} (collect): the game refused {m[2]} ({m[3]}); trying again next round"),
    (r"(Médico|Advogado): o jogo recusou (.+) \((.+), (\d+)\); volto a tentar na próxima jornada",
     lambda m: f"{_w(m[1])}: the game refused {m[2]} ({m[3]}, {m[4]}); trying again next round"),
    (r"(Médico|Advogado): (.+) fica à espera que acabe o tratamento em curso \((\d+)\)",
     lambda m: f"{_w(m[1])}: {m[2]} waits for the current treatment to end ({m[3]})"),
    (r"Análise: o jogo recusou enviar o analista a (.+) \((.+), (\d+)\); volto a tentar na próxima jornada",
     lambda m: f"Analysis: the game refused to send the analyst to {m[1]} ({m[2]}, {m[3]}); trying again next round"),
    (r"Análise \(levantar\): o jogo recusou \((.+), (\d+)\); volto a tentar na próxima jornada",
     lambda m: f"Analysis (collect): the game refused ({m[1]}, {m[2]}); trying again next round"),
    (r"Início de sessão: o jogo recusou (gastar .+ )?\((\d+)\); volto a tentar amanhã",
     lambda m: f"Login reward: the game refused{' to spend ' + m[1][7:].strip() if m[1] else ''} ({m[2]}); trying again tomorrow"),
    (r"(.+): sem dinheiro para melhorar; volto a tentar quando houver mais", lambda m: f"{m[1]}: not enough money to upgrade; trying again when there is more"),
)]


def tr(text: str) -> str:
    """The text in the chosen language (unchanged in Portuguese, or when there is no translation)."""
    if _language == "pt" or not text:
        return text
    if text in WORDS:
        return WORDS[text]
    for pattern, replace in PATTERNS:
        found = pattern.fullmatch(text)
        if found:
            return replace(found)
    return text
