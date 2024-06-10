from cryptography.fernet import Fernet
import base64
from configs.config import settings


key = settings.KEY_ENCRYPT_DOC.encode()
if len(key) > 32:
    key = key[:32]  
elif len(key) < 32:
    key = key.ljust(32, b'\0')  
key64 = base64.urlsafe_b64encode(key)
cipher_suite = Fernet(key64)    

def encrypt(text: str) -> str:
    encrypted_text = cipher_suite.encrypt(text.encode())
    return encrypted_text.decode()

def decrypt(text: str) -> str:
    decrypted_text = cipher_suite.decrypt(text.encode())
    return decrypted_text.decode()