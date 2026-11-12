# utils/date_reformat.py
from datetime import datetime


def format_date(value, with_time=False):
    """'2025-05-18T16:36:52+00:00' -> '18/05/2025' (ou '18/05/2025 18:36' avec with_time=True)."""
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return str(value)  # date partielle ou format inconnu : on l'affiche telle quelle
    if dt.tzinfo:
        dt = dt.astimezone()  # convertit l'heure UTC de MAL en heure locale
    return dt.strftime("%d/%m/%Y %H:%M" if with_time else "%d/%m/%Y")

SEASONS_FR = {"winter": "Hiver", "spring": "Printemps", "summer": "Été", "fall": "Automne"}


def format_season(start_season):
    """{'year': 2025, 'season': 'spring'} -> 'Printemps 2025'."""
    if not start_season:
        return "-"
    season = SEASONS_FR.get(start_season.get("season"), "")
    year = start_season.get("year", "")
    return f"{season} {year}".strip() or "-"