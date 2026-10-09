import json

import pytest

from osmbot import i18n
from osmbot.i18n import load_language, set_language, tr


@pytest.fixture
def english():
    set_language("en", save=False)
    yield
    set_language("pt", save=False)


def test_portuguese_is_left_alone():
    set_language("pt", save=False)
    assert tr("Vídeos da loja") == "Vídeos da loja"


def test_whole_texts_and_texts_with_names_and_numbers(english):
    assert tr("Vídeos da loja") == "Shop videos"
    assert tr("2.º Campeonato") == "2nd in the league" and tr("11.º Campeonato") == "11th in the league"
    assert tr("🏆 Quartos-de-final") == "🏆 Quarter-finals"
    assert tr("vs Clube B (14.º)") == "vs Clube B (14th)"
    assert tr("✓ Amigável") == "✓ Friendly" and tr("◉ Análise por levantar") == "◉ Analysis to collect"
    assert tr("Real Betis pôs Rice no médico (8 h)") == "Real Betis sent Rice to the doctor (8 h)"
    assert tr("Médico (levantar): o jogo não aceitou o pedido (404); fica por fazer à mão até se ver o pedido certo") \
        == "Doctor (collect): the game refused the request (404); left to do by hand until the right request is seen"
    assert tr("Clube A: Jogador 5 (MED) com 72% de condição; convém descansar 1 jogo") \
        == "Clube A: Jogador 5 (MID) at 72% fitness; better rest 1 match"
    assert tr("um texto sem tradução") == "um texto sem tradução"


def test_the_choice_is_remembered_on_this_pc(tmp_path, monkeypatch):
    from osmbot import logs

    monkeypatch.setattr(logs, "CONFIG_FILE", tmp_path / "config.json")
    (tmp_path / "config.json").write_text(json.dumps({"repo": "x"}), encoding="utf-8")
    set_language("en")
    assert json.loads((tmp_path / "config.json").read_text(encoding="utf-8")) == {"repo": "x", "language": "en"}
    set_language("pt", save=False)
    assert load_language() == "en" and i18n.language() == "en"
    set_language("pt", save=False)
