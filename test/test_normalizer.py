import pytest

from core.normalizer import is_fankai, normalize_key, parse

# (nom de fichier réel, titre attendu, saison, épisode)
CASES = [
    ("The.Rising.Of.The.Shield.Hero.S01E01.mkv", "The Rising Of The Shield Hero", 1, 1),
    ("[Erai-raws] Bang Dream Yumemita - 01 [1080p][Multiple Subtitle].mkv", "Bang Dream Yumemita", None, 1),
    ("Re Zero Starting Life In Another World 02 Multi Bluray 1080p - Monkey D Lulu.mkv",
     "Re Zero Starting Life In Another World", None, 2),
    ("[Yarashii] The Executioner and Her Way of Life 01 - FHD.mkv", "The Executioner and Her Way of Life", None, 1),
    ("Umamusume - Road to the top E01.mkv", "Umamusume - Road to the top", None, 1),
    ("Overlord IV - 07.mkv", "Overlord", 4, 7),
    ("[Erai-raws] Re Zero kara Hajimeru Isekai Seikatsu 2nd Season - 05 [1080p][Multiple Subtitle].mkv",
     "Re Zero kara Hajimeru Isekai Seikatsu", 2, 5),
    ("Mob Psycho 100 - 05.mkv", "Mob Psycho 100", None, 5),
]


@pytest.mark.parametrize("filename, title, season, episode", CASES)
def test_parse_titre_saison_episode(filename, title, season, episode):
    p = parse(filename)
    assert not p.ignored
    assert (p.title, p.season, p.episode) == (title, season, episode)


def test_special_oad():
    p = parse("[VCB-Studio] Shinmai Maou no Testament [13(OAD)][Ma10p 1080p][x265 flac].mkv")
    assert p.kind == "special" and p.episode == 13


@pytest.mark.parametrize("filename", [
    "[Fan-Kai] Dragon Ball Z - 01.mkv",
    "NCED EP 01-06 Saiaku na hi demo Anata ga Suki [9DB8213C].mkv",
])
def test_fichiers_ignores(filename):
    assert parse(filename).ignored


def test_dossier_fankai_ignore_le_fichier():
    assert parse("01.mkv", folder_name="Dragon Ball Fankai").ignored


def test_is_fankai():
    assert is_fankai("Re Zero Fan-Kai") and not is_fankai("Saenai Heroine no Sodatekata Ai to Seishun no Service kai")


def test_normalize_key():
    assert normalize_key("Re:Zero kara") == normalize_key("Re Zero kara")
    assert normalize_key("C³") == "c3"  # et non "c" : évite les faux positifs sur la lettre c