"""
core/normalizer.py

Nettoie un nom de fichier d'anime et en extrait : titre, saison, épisode.

Ce module est PUR : il ne lit aucun fichier, n'a aucune dépendance externe et
ne touche ni à l'UI ni aux bases JSON. Il peut donc être testé seul, puis
branché plus tard dans le scanner et le detector (qui n'auraient plus qu'un
seul parseur à partager).

Usage rapide :
    from core.normalizer import parse, normalize_key, is_fankai

    p = parse("[Yarashii] The Executioner and Her Way of Life 01 - FHD.mkv")
    p.title    -> "The Executioner and Her Way of Life"
    p.episode  -> 1
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Résultat
# --------------------------------------------------------------------------


@dataclass
class ParsedName:
    raw: str
    title: str = ""                 # titre "de base" (sans saison, sans épisode)
    title_with_season: str = ""     # même titre mais AVEC la mention de saison telle qu'écrite
    alt_titles: list = field(default_factory=list)   # ex: "(Redo of Healer)"
    title_with_number: str | None = None  # si un nombre final a été pris pour un épisode (ambigu)
    season: int | None = None
    episode: int | None = None
    part: str | None = None         # "A" / "B" pour 1A / 1B
    kind: str = "episode"           # "episode" | "special" | "movie"
    year: int | None = None
    team: str | None = None
    languages: list = field(default_factory=list)    # VOSTFR, MULTI, VF...
    resolution: str | None = None
    ignored: bool = False
    ignore_reason: str | None = None

    def title_variants(self) -> list:
        """Titres candidats à tester contre MAL, du plus probable au moins probable."""
        out = []
        for t in [self.title, self.title_with_season, self.title_with_number, *self.alt_titles]:
            if t and t not in out:
                out.append(t)
        return out


# --------------------------------------------------------------------------
# Expressions régulières
# --------------------------------------------------------------------------

_EXT_RE = re.compile(r"\.(?:mkv|mp4|avi|webm|m4v|mov|ts|nfo|cue|flac|ass|srt)$", re.I)
_FANKAI_RE = re.compile(r"fan[\s._-]*kai|\bHxH\s*Kai\b", re.I)
_CREDITLESS_RE = re.compile(r"\b(?:NCED|NCOP|Creditless)\b", re.I)

_AUDIO_CH = r"(?:[\s.]\d(?:[\s.]\d)?)?"   # "5 1", "5.1", "2"
_TECH_RE = re.compile(
    r"\b(?:"
    r"\d{3,4}p|\d{3,4}\s?x\s?\d{3,4}|4K|[FU]?HD|"
    r"WEB(?:[- ]?(?:DL|Rip))?|Blu[- ]?Ray|BD(?:Rip|Remux)?|DVD(?:Rip)?|HDTV|Remux|"
    r"x26[45]|h\s?26[45]|HEVC|AVC|AV1|(?:Hi|Ma)?10\s?bits?|8\s?bits?|Hi10p?|Ma10p|"
    r"AAC" + _AUDIO_CH + r"|E?AC-?3|FLAC" + _AUDIO_CH + r"|Opus" + _AUDIO_CH + r"|DDP?\s?\d(?:[\s.]\d)?|DTS(?:-HD)?|"
    r"VOSTFR|VOSTA?|VFF|VFI|VF|MULTI|SUBFR|DUAL(?:\s?AUDIO)?|TRUEFRENCH|FRENCH|"
    r"NC|UNCENSORED|UNCUT|BATCH|REPACK\d?|PROPER"
    r")\b",
    re.I,
)
_LANG_WORDS = {"VOSTFR", "VOST", "VOSTA", "VF", "VFF", "VFI", "MULTI", "SUBFR", "DUAL", "FRENCH", "TRUEFRENCH"}
_RES_RE = re.compile(r"\b(?:\d{3,4}p|4K|FHD|UHD)\b", re.I)
_RES_NUMBERS = {480, 576, 720, 1080, 2160}

_PLATFORM_RE = re.compile(r"^[A-Z0-9]{2,5}$")           # (ADN) (CR) (NF)
_CRC_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
_YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")
_BR_EP_RE = re.compile(r"^(?:EP?\s*)?(\d{1,4})(?:v\d+)?$", re.I)
_BR_SPECIAL_A = re.compile(r"^(\d{1,3})\s*\(\s*(OAD|OVA|ONA|SP|SPECIAL)\s*\)$", re.I)
_BR_SPECIAL_B = re.compile(r"^(SP|OVA|OAD|ONA|SPECIAL)\s*(\d{1,3})$", re.I)

_SXE_RE = re.compile(r"\bS(\d{1,2})\s?E(?:P)?\s?(\d{1,4})(?:v\d+)?\b", re.I)
_NXNN_RE = re.compile(r"\b(\d{1,2})x(\d{2,3})\b", re.I)
_E_RE = re.compile(r"\b(?:EP(?:ISODE)?|E)\s?(\d{1,4})(?:v\d+)?\b", re.I)
_DASH_RE = re.compile(r"\s[-–—]\s*(\d{1,4})(?:v\d+)?(?=\s|$|[-–—])")
_SPECIAL_RE = re.compile(r"\b(OVA|OAD|ONA|SP|SPECIAL)\s?(\d{1,3})\b", re.I)
_BARE_RE = re.compile(r"\s(\d{1,3})([AaBb])?$")
_PURE_NUM_RE = re.compile(r"^(?:EP?\s?)?(\d{1,4})(?:v\d+)?$", re.I)
_TRAIL_YEAR_RE = re.compile(r"\s((?:19|20)\d{2})$")

_SEASON_PATTERNS = [
    re.compile(r"\s*\b(\d{1,2})(?:st|nd|rd|th)\s+Season\b", re.I),
    re.compile(r"\s*\bSeason\s*(\d{1,2})\b", re.I),
    re.compile(r"\s*\bSaison\s*(\d{1,2})\b", re.I),
    re.compile(r"\s*\bS(\d{1,2})\b", re.I),
]
# V et X volontairement exclus : trop ambigus ("Gundam X", "Dr. Stone X"...)
_ROMAN = {"II": 2, "III": 3, "IV": 4, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}
_ROMAN_RE = re.compile(r"\s+(II|III|IV|VI|VII|VIII|IX)$")
_MOVIE_RE = re.compile(r"\b(?:Movie|Gekijouban|Film)\b", re.I)


# --------------------------------------------------------------------------
# Utilitaires publics
# --------------------------------------------------------------------------


def is_fankai(text: str) -> bool:
    """True si le texte (nom de fichier ou chemin) désigne un montage Fan-Kai."""
    return bool(text and _FANKAI_RE.search(text))


def normalize_key(text: str) -> str:
    """
    Clé de comparaison : minuscules, sans accents, sans ponctuation ni espaces.
    Les caractères japonais sont conservés. 'C³' devient 'c3' (et non 'c').
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return re.sub(r"[\W_]+", "", t.casefold())


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t-–—_:~,")


# --------------------------------------------------------------------------
# Étapes internes
# --------------------------------------------------------------------------


def _handle_brackets(name: str, r: ParsedName):
    """Traite les [crochets]. Retourne (nom sans crochets, épisode, kind, tags)."""
    episode = None
    kind = "episode"
    tags = []

    def classify(m: re.Match) -> str:
        nonlocal episode, kind
        c = m.group(1).strip()
        at_start = name[: m.start()].strip() == ""

        if _CRC_RE.match(c):
            return " "
        if _YEAR_RE.match(c):
            r.year = r.year or int(c)
            return " "
        sp = _BR_SPECIAL_A.match(c)
        if sp:
            episode, kind = int(sp.group(1)), "special"
            return " "
        sp = _BR_SPECIAL_B.match(c)
        if sp:
            episode, kind = int(sp.group(2)), "special"
            return " "
        ep = _BR_EP_RE.match(c)
        if ep and int(ep.group(1)) not in _RES_NUMBERS:
            if episode is None:
                episode = int(ep.group(1))
            return " "
        if _TECH_RE.search(c):
            tags.append(c)
            return " "
        if at_start and r.team is None:
            r.team = c
        return " "

    cleaned = re.sub(r"\[([^\[\]]*)\]", classify, name)
    return cleaned, episode, kind, tags


def _handle_parens(name: str, r: ParsedName):
    """Traite les (parenthèses) : année, plateforme, tags techniques, titre alternatif."""
    episode = None
    tags = []

    def classify(m: re.Match) -> str:
        nonlocal episode
        c = m.group(1).strip()
        if _YEAR_RE.match(c):
            r.year = r.year or int(c)
        elif _PLATFORM_RE.match(c):
            tags.append(c)
        elif _TECH_RE.search(c):
            tags.append(c)
        elif re.fullmatch(r"\d{1,3}", c):
            episode = int(c)
        elif len(c) >= 5 and re.search(r"[^\W\d_]{3,}", c):
            r.alt_titles.append(_clean(c))
        return " "

    cleaned = re.sub(r"\(([^()]*)\)", classify, name)
    return cleaned, episode, tags


def _extract_episode(head: str, r: ParsedName, have_episode: bool):
    """Cherche l'épisode dans le texte avant les tags techniques. Retourne le titre restant."""
    # 1. S01E03
    m = _SXE_RE.search(head)
    if m:
        r.season = int(m.group(1))
        if not have_episode:
            r.episode = int(m.group(2))
        return head[: m.start()]
    # 2. 1x05
    m = _NXNN_RE.search(head)
    if m:
        r.season = int(m.group(1))
        if not have_episode:
            r.episode = int(m.group(2))
        return head[: m.start()]
    if have_episode:
        return head
    # 3. E01 / EP01 / Episode 5
    m = _E_RE.search(head)
    if m:
        r.episode = int(m.group(1))
        return head[: m.start()]
    # 4. "Titre - 05"
    m = _DASH_RE.search(head)
    if m:
        r.episode = int(m.group(1))
        return head[: m.start()]
    # 5. OVA 2 / SP06
    m = _SPECIAL_RE.search(head)
    if m:
        r.episode, r.kind = int(m.group(2)), "special"
        return head[: m.start()]
    # 6. fichier "01.mkv"
    m = _PURE_NUM_RE.match(head.strip())
    if m:
        r.episode = int(m.group(1))
        return ""
    # 7. numéro final collé au titre : "Titre 02", "Titre 1A"  (AMBIGU)
    m = _BARE_RE.search(head)
    if m:
        r.episode = int(m.group(1))
        r.part = m.group(2).upper() if m.group(2) else None
        r.title_with_number = _clean(head)
        return head[: m.start()]
    return head


def _extract_season(title: str, r: ParsedName) -> str:
    """Retire les marqueurs de saison du titre et renseigne r.season si absent."""
    for pat in _SEASON_PATTERNS:
        m = pat.search(title)
        if m:
            if r.season is None:
                r.season = int(m.group(1))
            title = title[: m.start()] + title[m.end():]
            break
    else:
        m = _ROMAN_RE.search(title)
        if m and len(title.split()) >= 2:
            if r.season is None:
                r.season = _ROMAN[m.group(1)]
            title = title[: m.start()]
    return title


# --------------------------------------------------------------------------
# API principale
# --------------------------------------------------------------------------


def parse(filename: str, folder_name: str | None = None) -> ParsedName:
    """
    Analyse un nom de fichier (avec ou sans extension).
    folder_name (optionnel) sert de secours quand le fichier ne contient pas le titre
    (ex : '01.mkv' dans un dossier 'Mon Anime S02 1080p').
    """
    r = ParsedName(raw=filename)

    if is_fankai(filename) or (folder_name and is_fankai(folder_name)):
        r.ignored, r.ignore_reason = True, "fan-kai"
        return r
    if _CREDITLESS_RE.search(filename):
        r.ignored, r.ignore_reason = True, "générique (NCED/NCOP)"
        return r

    name = _EXT_RE.sub("", filename.strip())
    name = name.replace("_", " ")
    name = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", name)       # points -> espaces (sauf 5.1)

    name, ep_b, kind_b, tags_b = _handle_brackets(name, r)
    name, ep_p, tags_p = _handle_parens(name, r)
    name = re.sub(r"\s+", " ", name).strip()

    # Tags techniques : le titre se trouve AVANT le premier tag.
    tech = list(_TECH_RE.finditer(name))
    head = name
    for m in tech:
        if m.start() > 0:
            head = name[: m.start()]
            break

    for src in [*(m.group(0) for m in tech), *tags_b, *tags_p]:
        up = re.sub(r"\W+", "", src).upper()
        if up in _LANG_WORDS and up not in r.languages:
            r.languages.append(up)
        if r.resolution is None and _RES_RE.search(src):
            r.resolution = _RES_RE.search(src).group(0)

    head = _clean(head)

    # Année collée en fin de titre : "... Sing 2025"
    ym = _TRAIL_YEAR_RE.search(head)
    if ym:
        r.year = r.year or int(ym.group(1))
        head = head[: ym.start()]

    have_ep = ep_b is not None
    if have_ep:
        r.episode, r.kind = ep_b, kind_b
    elif ep_p is not None:
        r.episode, have_ep = ep_p, True

    title = _extract_episode(head, r, have_ep)
    title = _clean(title)
    r.title_with_season = title
    title = _clean(_extract_season(title, r))

    if not title and folder_name:
        fp = parse(folder_name)
        if not fp.ignored:
            title = fp.title
            r.title_with_season = fp.title_with_season or fp.title
            r.season = r.season if r.season is not None else fp.season
            r.alt_titles = r.alt_titles or fp.alt_titles
            r.year = r.year or fp.year
            r.team = r.team or fp.team

    r.title = title
    if not r.title_with_season:
        r.title_with_season = title
    if r.kind == "episode" and _MOVIE_RE.search(title):
        r.kind = "movie"
    return r