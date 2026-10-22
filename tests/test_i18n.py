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
    assert tr("Amigável") == "Friendly" and tr("por levantar") == "to collect"
    assert tr("Real Betis pôs Rice no médico (8 h)") == "Real Betis sent Rice to the doctor (8 h)"
    assert tr("Real Betis pôs Rice no advogado (3 h)") == "Real Betis sent Rice to the lawyer (3 h)"
    assert tr("Real Betis enviou o analista a Clube B (15 min)") == "Real Betis sent the analyst to Clube B (15 min)"
    assert tr("Médico (levantar): o jogo não aceitou o pedido (404); fica por fazer à mão até se ver o pedido certo") \
        == "Doctor (collect): the game refused the request (404); left to do by hand until the right request is seen"
    assert tr("Clube A: Jogador 5 (MED) com 72% de condição; convém descansar 1 jogo") \
        == "Clube A: Jogador 5 (MID) at 72% fitness; better rest 1 match"
    assert tr("Poupança: Clube A depositou 1,2 M antes do jogo (poupança 6,2 M)") \
        == "Savings: Clube A deposited 1,2 M before the match (savings 6,2 M)"
    assert tr("Depósito na poupança") == "Savings deposit"
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


def test_the_new_sale_line_in_english(english):
    assert tr("SALE novos (Spain): 6 · DEF 88 J (25 anos) 12,3 M e mais 1") ==         "New SALE (Spain): 6 · DEF 88 J (25 years) 12,3 M and 1 more"


def test_the_purchase_profit_and_stale_lines_in_english(english):
    assert tr("Compra: F (C) comprado por 8,86 M (1,37 × o valor), de Fiorentina") ==         "Purchase: F (C) bought for 8,86 M (1,37 × value), from Fiorentina"
    assert tr("Venda: A (C) vendido por 20 M (100% do máximo ≈ 20 M); à venda desde 1/1 10:00, vendido até 1/1 11:00, "
              "demorou 1h00; lucro +8 M em 25h00").endswith("took 1h00; profit +8 M in 25h00")
    assert tr("K à venda há 95h00 (normal ~46h00 a este preço)") == "K on the list for 95h00 (usually ~46h00 at this price)"
    assert tr("K à venda há 95h00") == "K on the list for 95h00"
    assert tr("K à venda há 2 dias e 3h00") == "K on the list for 2 days and 3h00"
    assert tr("K: ~1 dia e 22h00") == "K: ~1 day and 22h00"
    assert tr("Normal a este preço") == "Usual at this price"
