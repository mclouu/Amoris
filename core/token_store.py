import keyring
from keyring.errors import PasswordDeleteError

SERVICE = "Amoris"
KEY = "mal_refresh_token"


def save_refresh_token(token: str):
    keyring.set_password(SERVICE, KEY, token)


def load_refresh_token():
    return keyring.get_password(SERVICE, KEY)


def clear():
    try:
        keyring.delete_password(SERVICE, KEY)
    except PasswordDeleteError:
        pass