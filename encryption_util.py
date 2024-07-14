# encryption_util.py
from cryptography.fernet import Fernet

# Generate and save a key
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Load the previously generated key
def load_key():
    return open("secret.key", "rb").read()

# Encrypt a message
def encrypt_message(message, key):
    fernet = Fernet(key)
    return fernet.encrypt(message.encode())

# Decrypt a message
def decrypt_message(encrypted_message, key):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_message).decode()
