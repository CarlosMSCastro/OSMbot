from datetime import datetime

import pytest

from osmbot import logs


def _repo(tmp_path):
    repo = tmp_path / "OSMbot"
    (repo / "src" / "osmbot").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    return repo


def test_each_line_goes_to_the_day_file_of_this_pc(tmp_path):
    repo = _repo(tmp_path)
    logs.write(datetime(2026, 10, 8, 1, 2, 3), "Loja: vídeo 1", repo)
    logs.write(datetime(2026, 10, 8, 1, 3, 0), "Treino: vídeo 1 (Real Betis, GR)", repo)
    logs.write(datetime(2026, 10, 9, 0, 0, 1), "Bot ligado", repo)
    folder = repo / "logs" / logs.machine()
    assert (folder / "2026-10-08.log").read_text(encoding="utf-8").splitlines() == [
        "2026-10-08 01:02:03  Loja: vídeo 1", "2026-10-08 01:03:00  Treino: vídeo 1 (Real Betis, GR)"]
    assert (folder / "2026-10-09.log").exists()


def test_secrets_never_reach_the_repo_but_names_do():
    line = "erro com eyJhbGciOiJIUzI1.eyJleHAiOjE3MDAw.abcDEF access_token=abc123 de dono@exemplo.pt em Real Betis"
    cleaned = logs.clean(line)
    assert "eyJ" not in cleaned and "abc123" not in cleaned and "dono@exemplo.pt" not in cleaned
    assert "Real Betis" in cleaned  # names stay (owner's choice, D-022)


def test_a_broken_logs_folder_never_stops_the_bot(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    logs.write(datetime(2026, 10, 8), "x", blocker)  # not a folder: silently ignored


def test_without_a_known_repo_nothing_is_written():
    assert logs.repo_folder() is None
    logs.write(datetime(2026, 10, 8), "x")  # no error


def test_choosing_the_repo_remembers_it_and_copies_the_old_log_once(tmp_path):
    repo = _repo(tmp_path)
    old = tmp_path / "bot.log"
    old.write_text("2026-10-07 01:00:00  Bot ligado\n2026-10-07 02:00:00  Loja: vídeo 1\n"
                   "2026-10-08 00:09:22  Bot ligado\nlinha solta\n", encoding="utf-8")
    assert logs.choose_repo(f'"{repo}"') == repo.resolve()
    assert logs.repo_folder() == repo.resolve()
    assert logs.import_history(repo, old) == 2 and logs.import_history(repo, old) == 0
    assert (repo / "logs" / logs.machine() / "2026-10-07.log").read_text(encoding="utf-8").count("\n") == 2


def test_a_folder_that_is_not_the_repo_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        logs.choose_repo(str(tmp_path))


def test_the_bot_log_also_goes_to_the_repo(tmp_path, monkeypatch):
    from osmbot.game import loop

    repo = _repo(tmp_path)
    monkeypatch.setenv("OSMBOT_REPO", str(repo))
    monkeypatch.setattr(loop, "LOG_FILE", tmp_path / "bot.log")
    loop._log("Treinos: 1 falha(s) ao escrever")
    files = list((repo / "logs" / logs.machine()).glob("*.log"))
    assert len(files) == 1 and "Treinos: 1 falha(s)" in files[0].read_text(encoding="utf-8")


def test_the_menu_option_leaves_quietly_without_an_answer():
    said = []

    def no_input(prompt):
        raise EOFError

    logs.run_logs_folder(ask=no_input, show=said.append)
    assert "não definido" in said[0]
