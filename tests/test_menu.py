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
