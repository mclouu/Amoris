import pytest

from core import mal_client


def test_update_episodes_envoie_le_bon_patch(monkeypatch):
    calls = []
    monkeypatch.setattr(
        mal_client, "_request",
        lambda method, url, form=None, **kw: calls.append((method, url, form)) or {},
    )
    mal_client.update_episodes(56653, 7, status="watching")
    assert calls == [("PATCH", f"{mal_client.API}/anime/56653/my_list_status",
                      {"num_watched_episodes": 7, "status": "watching"})]


def test_liste_vide_ne_remplace_jamais_le_cache(monkeypatch):
    monkeypatch.setattr(mal_client, "fetch_my_list", lambda: [])
    monkeypatch.setattr(mal_client, "save_list_cache",
                        lambda items: pytest.fail("le cache ne doit pas être écrit"))
    with pytest.raises(mal_client.MalApiError) as err:
        mal_client.refresh_list_cache()
    assert err.value.code == "empty_list"