import platform

import keyring
from cryptography.fernet import Fernet, InvalidToken
from mentaws import cryptographic_operations

app_name = "mentaws"
key_name = "test_key"

def test_keyring_on_os():

    """
    Can't test on Linux with Github actions because installing backend is quite complex
    """
    
    if not platform.system() == "Linux":
        key = cryptographic_operations.gen_key()
        assert len(key) == 44

        assert cryptographic_operations.setup_key(app_name=app_name, key_name=key_name) == True

        encryption_key = cryptographic_operations.get_key(app_name=app_name, key_name=key_name)
        assert isinstance(encryption_key, Fernet)

def test_encrypt_decrypt():

    """
    Can't test on Linux with Github actions because installing backend is quite complex
    """

    if not platform.system() == "Linux":
        test_string = "abc12345dsfafsafdfsdf3-12934019u423oyrewkbf1!@#%^IU^&(&%&*)_()_)()((*&*%$^%#$@#?>:{}|"

        key = cryptographic_operations.get_key(app_name=app_name, key_name=key_name)
        encrypted_string = key.encrypt(test_string.encode('utf-8')).decode('utf-8')

        decrypted_string = key.decrypt(encrypted_string.encode('utf-8'))
        assert decrypted_string.decode('utf-8') == test_string
