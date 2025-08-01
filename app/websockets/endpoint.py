from fastapi import APIRouter, WebSocket, WebSocketException
from app.api.auth import *
from app.utils.crypto import *
from app.websockets.manager import *
from typing import Dict
from app.schemas import *
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

### WEBRTC ЗВОНКИ ###

active_connections_ws: Dict[str, WebSocket] = {}

async def push_personal_message(to_user: str, payload: dict):
    ws = active_connections_ws.get(to_user)
    if ws:
        await ws.send_text(json.dumps(payload))

async def push_group_message(group_members: List[str], from_user: str, payload: dict):
    for member in group_members:
        if member != from_user and member in active_connections_ws:
            await active_connections_ws[member].send_text(json.dumps(payload))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        current_user = await get_current_user_ws(websocket)
    except WebSocketException:
        return

    username = current_user["username"]
    await websocket.accept()
    active_connections_ws[username] = websocket
    print(f"🔗 {username} подключился")

    try:
        while True:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                to_user = msg.get("to")
                payload = msg.get("data")

                if not to_user or not payload:
                    print(f"⚠️ Пустой to или data от {username}: {msg}")
                    continue

                if to_user in active_connections_ws:
                    print(f"➡️ Пересылка от {username} к {to_user}")
                    await active_connections_ws[to_user].send_text(json.dumps({
                        "from": username,
                        "data": payload
                    }))
                else:
                    print(f"❌ {to_user} не в сети")
            except Exception as e:
                print(f"💥 Ошибка при обработке сообщения от {username}: {e}")
                break  # выходим из while
    except WebSocketDisconnect:
        print(f"🔌 {username} отключился")
    finally:
        active_connections_ws.pop(username, None)