from fastapi import Request, HTTPException
from cryptography.fernet import Fernet
from configs.config import settings
from uuid import UUID
import base64


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

async def encrypt_id(id: str, request: Request):
    """Encrypt a UUID"""
    try:
        kjbhd_id = UUID(id)
        encrypted_id = encrypt(str(kjbhd_id))
        url = f'{request.base_url}landrope/attachment_file/document/{encrypted_id}'
        return url
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")