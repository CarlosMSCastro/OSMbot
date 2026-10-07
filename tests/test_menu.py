from osmbot import menu


def make(calls):
    return {
        "1": ("Iniciar", lambda: calls.append("1")),
        "3": ("Estado", lambda: calls.append("3")),
        "9": ("Falha", lambda: (_ for _ in ()).throw(SystemExit("Sem sessao guardada."))),
    }


def run(inputs, calls):
    shown, answers = [], iter(inputs)

    def ask(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    menu.run_menu(make(calls), ask=ask, show=shown.append, clear=False)
    return "\n".join(shown)


def test_choice_runs_the_action_and_returns_to_the_menu():
    calls = []
    run(["3", "", "1", "", "0"], calls)
    assert calls == ["3", "1"]


def test_invalid_choice_asks_again():
    calls = []
    text = run(["x", "7", "0"], calls)
    assert calls == [] and text.count("Opção inválida") == 2


def test_an_action_that_exits_does_not_close_the_menu():
    calls = []
    text = run(["9", "", "1", "", "0"], calls)
    assert "Sem sessao guardada." in text and calls == ["1"]


def test_end_of_input_leaves_quietly():
    run([], [])
    run(["1"], [])  # EOF at the "Enter para voltar" prompt


def test_menu_lists_every_action_and_exit():
    text = run(["0"], [])
    for expected in ("Iniciar", "Estado", "0  Sair", "Sessão"):
        assert expected in text


def test_the_default_menu_has_start_login_logs_folder_and_exit():
    assert [label for label, _ in menu._default_actions().values()] == ["Iniciar", "Login", "Pasta dos logs"]


def test_default_menu_only_has_start_login_and_exit():
    shown = menu.build_screen({"1": ("Iniciar", None), "2": ("Login", None)}, "Sessão: ok", 100)
    text = "\n".join(shown)
    assert "1  Iniciar" in text and "2  Login" in text and "0  Sair" in text and "Estado" not in text
    assert all(line.startswith(" ") for line in shown if line)  # centred, not stuck to the left edge


def run_with_keys(keys, calls, inputs=()):
    """The arrow-key menu: ``keys`` are the key presses, ``inputs`` the answers to "Enter para continuar"."""
    pressed, answers = iter(keys), iter(inputs)

    def key():
        try:
            return next(pressed)
        except StopIteration:
            raise KeyboardInterrupt

    def ask(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    menu.run_menu(make(calls), ask=ask, show=lambda text: None, clear=False, key=key)


def test_arrows_move_the_choice_and_enter_runs_it(capsys):
    calls = []
    run_with_keys(["down", "enter"], calls, inputs=[""])  # 2nd option = "Estado"
    assert calls == ["3"]


def test_the_choice_wraps_around_and_the_last_option_is_leave():
    calls = []
    run_with_keys(["up", "enter"], calls)  # up from the first option lands on "Sair"
    assert calls == []


def test_typing_the_number_or_pressing_escape_still_works():
    calls = []
    run_with_keys(["1", "", "esc"], calls, inputs=[""])
    assert calls == ["1"]


def test_selected_option_is_marked_and_the_hint_is_shown():
    actions = {"1": ("Iniciar", None), "2": ("Login", None)}
    lines = menu.build_screen(actions, "Sessão: ok", 100, selected=1)
    text = "\n".join(lines)
    assert "» 2  Login" in text and "» 1  Iniciar" not in text and "↑ ↓ para escolher" in text
    assert "»" not in "\n".join(menu.build_screen(actions, "Sessão: ok", 100))  # typed mode has no marker
