from cryptography.fernet import Fernet
from cryptography.hazmat.backends.openssl import backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import InvalidToken


def get_key(password: bytes, salt: bytes, n=2 ** 18, r=8, p=1, length=32) -> Fernet:
    """
    :param password: Password in bytes
    :param salt: salt in bytes
    :param n: cost
    :param r: block_size
    :param p: Parallelization factor
    :param length: Length of key in bytes
    :return: Fernet key for encryption
    """

    kdf = Scrypt(salt=salt, length=length, n=n, r=r, p=p, backend=backend)
    key = base64.urlsafe_b64encode(kdf.derive(password))
    encryption_key = Fernet(key)

    return encryption_key


def encrypt_creds_file(
    password: str, salt: str, platform_config: dict, creds: bytes = "", initialize: bool = False
):

    creds_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )
    encrypted_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["encrypted_file_name"]
    )
    key = get_key(password=password.encode("utf-8"), salt=salt.encode("utf-8"))

    if initialize:
        with open(creds_file_path, "rb") as input_file:
            creds = input_file.read()
    else:
        # use the creds passed into the function
        pass

    enc_data = key.encrypt(creds)
    with open(encrypted_file_path, "wb") as output_file:
        output_file.write(enc_data)

    return


def decrypt_creds_file(password: str, salt: str, platform_config: dict) -> str:

    encrypted_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["encrypted_file_name"]
    )
    key = get_key(password=password.encode("utf-8"), salt=salt.encode("utf-8"))

    with open(encrypted_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()
        try:
            data = key.decrypt(encrypted_data).decode("utf-8")
        except InvalidToken:
            raise InvalidPasswordError("Decryption Password is not valid")

    return data