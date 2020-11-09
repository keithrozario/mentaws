import secrets
import base64
import sys

from typing import List

import keyring
from cryptography.fernet import Fernet, InvalidToken


def gen_key() -> str:
    """
    Use secrets.token_bytes to generate keyt, and return base64 encoded key (as string)
    """
    key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
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
    encryption_key = Fernet(key.encode("utf-8"))
    return encryption_key


def decrypt_keys(profiles: List[dict], app_name: str, key_name: str) -> dict:
    """
    Args:
        profiles: dictionary of format {'profile': <value>, 'aws_secret_access_key': <value>}
        app_name: app name of key in keychain
        key_name: key name in keychain
    return:
        decrypted_keys: dictionary of format {'profile': 'encrypted_aws_secret_access_key'}
        You'll be able to get the decrypted key, by accessing decrypted_keys.get(<profile_name>)
    """

    key = get_key(app_name, key_name)
    decrypted_keys = dict()

    try:
        for profile in profiles:
            if not profile['aws_secret_access_key'] == "":
                aws_secret_access_key = key.decrypt(profile['aws_secret_access_key'].encode("utf-8"))
                decrypted_keys[profile['profile']] = aws_secret_access_key.decode('utf-8')
            else: 
                decrypted_keys[profile['profile']] = ""
    except InvalidToken:
        sys.exit("Password Error!! Please check password and try again")

    return decrypted_keys



def encrypt_keys(profiles: List[dict], app_name: str, key_name: str) -> dict:
    """
    Args:
        profiles: dictionary of format {'profile': <value>, 'aws_secret_access_key': <value>}
        app_name: app name of key in keychain
        key_name: key name in keychain
    return:
        encrypted_keys: dictionary of format {'profile': 'encrypted_aws_secret_access_key'}
        You'll be able to get the encrypted key, by accessing encrypted_keys.get(<profile_name>)
    """

    key = get_key(app_name, key_name)
    encrypted_keys = dict()
    
    for profile in profiles:
        if not profile['aws_secret_access_key'] == "":
            encrypted_aws_secret_access_key = key.encrypt(profile['aws_secret_access_key'].encode("utf-8"))
            encrypted_keys[profile['profile']] = encrypted_aws_secret_access_key.decode('utf-8')
        else: 
            encrypted_keys[profile['profile']] = ""

    return encrypted_keys