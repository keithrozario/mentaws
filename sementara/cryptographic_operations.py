import secrets
import base64
import keyring
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken


def gen_key() -> str:
    """
    Use secrets.token_bytes to generate keyt, and return base64 encoded key (as string)
    """
    key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    return key


def setup_key(app_name: str, key_name: str) -> bool:
    """
    Store key onto keychain
    """
    keyring.set_password(app_name, key_name, gen_key())
    return True



def get_key(app_name: str, key_name: str) -> Fernet:
    """
    Args:
        app_name: Name of application in Keychain
        key_name: Name of key in KeyChain
    Return
        encryption_key: Fernet encryption key
    """
    key = keyring.get_password(app_name, key_name)
    encryption_key = Fernet(key.encode('utf-8'))
    return encryption_key


def decrypt(encrypted_string: str, app_name: str, key_name: str) -> str:
    """
    Args:
        encrypted_string: encrypted string
        app_name: Name of application in Keychain
        key_name: Name of key in KeyChain
    return:
        decrypted_string: string decrypted with single key
    """

    key = get_key(app_name, key_name)
    decrypted_string = key.decrypt(encrypted_string.encode('utf-8'))
    return decrypted_string.decode('utf-8')


def encrypt(plaintext: str, app_name: str, key_name: str) -> str:
    """
    Args:
        plaintext: plaintext to be encrypted
    return:
        encrypted_string: encrypted_string
    """

    key = get_key(app_name, key_name)
    encrypted_string = key.encrypt(plaintext.encode('utf-8'))

    return encrypted_string.decode('utf-8')