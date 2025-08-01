from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.options import *
from app.schemas import *
from app.api.auth     import router as auth_router
from app.api.messages import router as messages_router
from app.api.files    import router as files_router
from app.api.friends  import router as friends_router
from app.api.groups   import router as groups_router
from app.api.profile  import router as profile_router
from app.api.tasks    import router as tasks_router
from app.websockets.endpoint import router as ws_router

app = FastAPI(title="REDFAX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# подключаем все API‑роутэры
app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(files_router)
app.include_router(friends_router)
app.include_router(groups_router)
app.include_router(profile_router)
app.include_router(tasks_router)

# WebSocket
app.include_router(ws_router)