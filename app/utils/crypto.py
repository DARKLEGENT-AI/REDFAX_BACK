from Crypto.Cipher import AES
import base64
from passlib.context import CryptContext

KEY = b"1234567890abcdef"  # 16 байт
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

## Двунаправленное шифрование ##
def encrypt_message(raw: str) -> str:
    cipher = AES.new(KEY, AES.MODE_EAX)
    nonce, ciphertext, tag = cipher.nonce, cipher.encrypt(raw.encode()), cipher.digest()
    return base64.b64encode(nonce + tag + ciphertext).decode()

def decrypt_message(enc: str) -> str:
    data = base64.b64decode(enc)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

## Однонаправленное шифрование (получения хеша) ##
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)