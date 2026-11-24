from utils.date_reformat import format_date, format_season


def test_format_date():
    assert format_date("2025-05-18T12:00:00+00:00") == "18/05/2025"


def test_format_date_vide_ou_invalide():
    assert format_date(None) == "-"
    assert format_date("pas une date") == "pas une date"


def test_format_season():
    assert format_season({"year": 2025, "season": "spring"}) == "Printemps 2025"
    assert format_season(None) == "-"
    assert format_season({}) == "-"