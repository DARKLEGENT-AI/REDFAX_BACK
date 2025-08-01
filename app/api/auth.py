from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime
from starlette.status import WS_1008_POLICY_VIOLATION
from app.db.mongodb import get_user, create_user
from app.schemas import UserCreate, UserLogin
from app.options import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils.crypto import get_password_hash, verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
router = APIRouter(prefix="/auth", tags=["auth"])

def create_access_token(data: dict, expires: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
async def register(user: UserCreate):
    if await get_user(user.username):
        raise HTTPException(400, "User already exists")
    hashed = get_password_hash(user.password)
    await create_user(user.username, hashed)
    return {"message": "Registered"}

@router.post("/token")
async def login(user: UserLogin):
    db_user = await get_user(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": user.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    cred_exc = HTTPException(401, "Invalid credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = await get_user(username)
    if not user:
        raise cred_exc
    return user

async def get_current_user_ws(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise WebSocketException(code=WS_1008_POLICY_VIOLATION)
    except JWTError:
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION)
    user = await get_user(username)
    if not user:
        raise WebSocketException(code=WS_1008_POLICY_VIOLATION)
    return user