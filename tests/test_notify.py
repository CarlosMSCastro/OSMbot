from osmbot.notify.rules import due, enabled, error, opponent, played, pregame, sale

NOW = 1_000_000.0
STEPS = [("Amigáveis (3)", True, None), ("Análise", False, None), ("Onze", False, "fora da regra"),
         ("Tática", True, None), ("Banco", False, None), ("4 treinos", False, None)]


def club(**changes):
    base = {"key": "1_9", "name": "Neman", "match": NOW + 1800,
            "prep": {"steps": STEPS, "why": {"Onze": ["Formação 5-3-2: devia ser 4-3-3 A", "outra"]}},
            "next": {"opponent": "Rival", "camp": False}}
    return {**base, **changes}


def test_pregame_lists_orange_and_unticked_steps_but_not_the_analysis_nor_the_4_trainings():
    alert = pregame(club(), NOW)
    assert alert.kind == "pre_jogo" and alert.key == f"pre:1_9:{int(NOW + 1800)}"
    assert alert.text.splitlines() == ["Neman: jogo em 30 min", "🟠 Onze: Formação 5-3-2: devia ser 4-3-3 A",
                                       "⚪ Banco: por marcar"]


def test_pregame_waits_for_the_last_hour_and_stays_quiet_when_all_is_right():
    assert pregame(club(match=NOW + 2 * 3600), NOW) is None
    assert pregame(club(match=NOW - 5), NOW) is None
    assert pregame(club(prep={"steps": [("Onze", True, None)], "why": {}}), NOW) is None
    assert pregame(club(prep={"steps": [("Análise", False, None)]}), NOW) is None


def test_the_opponent_camp_secret_training_or_both():
    assert opponent(club()) is None
    assert opponent(club(next={"opponent": "Rival", "camp": True})).text == "Neman: Rival fez estágio"
    secret = club(prep={"steps": [("Análise", False, "treino secreto")]})
    assert opponent(secret).text.startswith("Neman: Rival fez treino secreto")
    both = club(prep={"steps": [("Análise", False, "treino secreto")]}, next={"opponent": "Rival", "camp": True})
    assert opponent(both).text == "Neman: Rival fez estágio e treino secreto"


def test_messages_have_no_result_and_events_are_off_by_default():
    assert played("Neman", "1_9_5").text == "Neman: o jogo já passou"
    assert sale("Neman", "Mir", "2,25 M", "1").text == "Neman: Mir vendido por 2,25 M"
    assert enabled(None, "venda") and enabled(None, "erro") and not enabled(None, "evento")
    assert not enabled({"venda": False}, "venda") and enabled({"evento": True}, "evento")


def test_due_sends_each_fact_once_and_only_the_kinds_that_are_on():
    sent = set()
    alerts = [played("Neman", "a"), sale("Neman", "Mir", "1 M", "s1"), error("sessão expirada", "x")]
    assert [a.kind for a in due(alerts, {"jogo": False}, sent)] == ["venda", "erro"]
    assert due(alerts, {"jogo": False}, sent) == []  # again: nothing new
    assert [a.kind for a in due([None, played("Neman", "b")], None, sent)] == ["jogo"]


def test_log_lines_become_sales_played_matches_and_errors():
    from osmbot.notify.rules import from_log_line

    line = "Venda: Pushnyakov (Neman) vendido por 2,25 M (100% do máximo ≈ 2,25 M); à venda desde 17/11 13:19"
    assert from_log_line(line).text == "Neman: Pushnyakov vendido por 2,25 M"
    played_ = from_log_line("Jogo: Neman 1-0 Rival (fora) · força do jogo 522/522 · melhor nota Mir 8")
    assert played_.kind == "jogo" and played_.text == "Neman: o jogo contra Rival já passou"
    assert "1-0" not in played_.text  # no spoilers
    assert from_log_line("Amigável: Neman 2-0 Rival") is None and from_log_line("Compra: Mir (Neman) comprado por 6 M") is None
    assert from_log_line("Parou: erro (X) em loop.py:5", True).kind == "erro"
    assert from_log_line("Vídeos: erro (shop_ads: x); volto a tentar", True) is None  # the bot retries it: counted, not sent


def test_the_dispatcher_sends_once_waits_for_a_connected_chat_and_limits_errors():
    from osmbot.notify.dispatch import Dispatcher

    sent, clock = [], [NOW]
    config = {"token": "T", "chat_id": 7, "avisos": {}}
    dispatcher = Dispatcher(lambda t, c, text, **kw: sent.append((t, c, text)), lambda: config, lambda: clock[0], None, False)
    sale_line = "Venda: Mir (Neman) vendido por 1 M (100%); x"
    dispatcher.line(sale_line)
    dispatcher.line(sale_line)  # same line again: nothing
    assert sent == [("T", 7, "💰 <b>Neman</b>\nMir vendido por <b>1 M</b>")]
    dispatcher.snapshot({"clubs": [club()]})
    dispatcher.snapshot({"clubs": [club()]})
    assert len(sent) == 2 and sent[1][2].startswith("⏰ <b>Neman</b> · jogo em 30 min")  # the pre-match warning, once
    dispatcher.line("Parou: erro um", True)
    dispatcher.line("Parou: erro dois", True)  # within 5 minutes: held back
    assert len(sent) == 3 and sent[2][2] == "🔴 <b>Erro</b>\n<code>Parou: erro um</code>"
    clock[0] += 400
    dispatcher.line("Parou: erro três", True)
    assert len(sent) == 4
    config.update(token=None)  # not connected: silent
    dispatcher.line("Venda: Ana (Neman) vendido por 2 M (1%); x")
    assert len(sent) == 4


def test_the_dispatcher_remembers_what_it_sent_between_runs(tmp_path):
    from osmbot.notify.dispatch import Dispatcher

    sent, store = [], tmp_path / "n.json"
    config = {"token": "T", "chat_id": 7}
    line = "Venda: Mir (Neman) vendido por 1 M (100%); x"
    Dispatcher(lambda *a, **kw: sent.append(a), lambda: config, lambda: NOW, store, False).line(line)
    Dispatcher(lambda *a, **kw: sent.append(a), lambda: config, lambda: NOW, store, False).line(line)  # a restart
    assert len(sent) == 1


def test_messages_are_dressed_for_telegram_and_carry_the_clubs_logo():
    from osmbot.notify.dispatch import Dispatcher

    assert sale("A & B", "Mir <1>", "2 M", "k").html == "💰 <b>A &amp; B</b>\nMir &lt;1&gt; vendido por <b>2 M</b>"
    assert "<b>Onze</b>" in pregame(club(), NOW).html and pregame(club(), NOW).club == "Neman"
    seen = []
    dispatcher = Dispatcher(lambda t, c, text, **kw: seen.append(kw), lambda: {"token": "T", "chat_id": 1}, lambda: NOW, None, False)
    dispatcher.snapshot({"clubs": [{**club(match=None), "logo": "https://x/logo.png"}]})
    dispatcher.line("Venda: Mir (Neman) vendido por 1 M (1%); x")
    assert seen == [{"html": True, "photo": "https://x/logo.png"}]


def test_errors_the_bot_retries_reach_the_phone_only_when_they_keep_failing():
    from osmbot.notify.dispatch import Dispatcher
    from osmbot.notify.rules import REPEAT_COOLDOWN, REPEAT_COUNT

    sent, clock = [], [NOW]
    dispatcher = Dispatcher(lambda t, c, text, **kw: sent.append(text), lambda: {"token": "T", "chat_id": 7}, lambda: clock[0], None, False)
    for _ in range(REPEAT_COUNT - 1):
        clock[0] += 600
        dispatcher.line("Vídeos: erro (shop_ads: os boss coins não subiram); volto a tentar", True)
    assert sent == []  # 4 in 40 min: the bot is coping
    clock[0] += 600
    dispatcher.line("Vídeos: erro (shop_ads: os boss coins não subiram); volto a tentar", True)
    assert len(sent) == 1 and sent[0].startswith("🔴 <b>Vídeos</b> falhou 5 vezes em 3 h")
    clock[0] += 600
    dispatcher.line("Vídeos: erro (x); volto a tentar", True)
    assert len(sent) == 1  # then silence for 6 hours
    dispatcher.line("Rede: erro (502); nova tentativa em 0h01", True)
    assert len(sent) == 1  # another kind starts its own count
    clock[0] += REPEAT_COOLDOWN + 1  # the failures of 6 h ago no longer count
    dispatcher.line("Vídeos: erro (y); volto a tentar", True)
    assert len(sent) == 1
    for _ in range(REPEAT_COUNT):
        clock[0] += 60
        dispatcher.line("Vídeos: erro (z); volto a tentar", True)
    assert len(sent) == 2
