import os
import base64
from loguru import logger
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


ITERATIONS = 600_000
KEY_SIZE = 32
SALT_SIZE = 16
PASSWORD_ENCODING = "utf-8"


def get_fernet_with_salt(password, salt=None):
    """
    Generates a Fernet object derived from a password, and returns the object and salt.

    :param password: The password used for deriving the key.
    :param salt: Optional salt to use; if not provided, a new one will be generated.
    :return: A tuple containing the Fernet object and the salt.
    """
    if salt is None:
        salt = os.urandom(SALT_SIZE)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode(PASSWORD_ENCODING))
    fernet_key = base64.urlsafe_b64encode(key)
    fernet = Fernet(fernet_key)

    return fernet, salt


def encrypt_file(filepath, password):
    """
    Encrypts a file using Fernet symmetric encryption derived from a password.

    :param filepath: The path to the file to encrypt.
    :param password: The password to derive the encryption key.
    :return: The path to the encrypted file.
    """
    encrypted_filepath = filepath + ".enc"
    try:
        f, salt = get_fernet_with_salt(password)

        with open(filepath, "rb") as file:
            data = file.read()

        encrypted_data = f.encrypt(data)

        with open(encrypted_filepath, "wb") as file:
            file.write(salt + encrypted_data)

        logger.debug(f"File encrypted successfully: {encrypted_filepath}")
        return encrypted_filepath
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_file(encrypted_filepath, password):
    """
    Decrypts a file encrypted with Fernet symmetric encryption derived from a password.

    :param encrypted_filepath: The path to the encrypted file.
    :param password: The password to derive the decryption key.
    :return: The path to the decrypted file.
    """
    if encrypted_filepath.endswith(".enc"):
        decrypted_filepath = encrypted_filepath[:-4]
    else:
        decrypted_filepath = encrypted_filepath + ".decrypted"

    logger.info(f"Decrypting file: {encrypted_filepath} -> {decrypted_filepath}")

    try:
        with open(encrypted_filepath, "rb") as file:
            salt = file.read(SALT_SIZE)
            encrypted_data = file.read()

        f, _ = get_fernet_with_salt(password, salt)

        decrypted_data = f.decrypt(encrypted_data)

        with open(decrypted_filepath, "wb") as file:
            file.write(decrypted_data)

        logger.info(f"File decrypted successfully: {decrypted_filepath}")
        return decrypted_filepath
    except InvalidToken:
        logger.error("Invalid password or corrupted file.")
        raise
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise
