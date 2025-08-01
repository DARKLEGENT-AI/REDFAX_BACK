from Crypto.Cipher import AES
import base64
from passlib.context import CryptContext
from jose import jwt
from datetime import timedelta, datetime
from app.options import SECRET_KEY, ALGORITHM

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

def create_access_token(data: dict, expires: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)