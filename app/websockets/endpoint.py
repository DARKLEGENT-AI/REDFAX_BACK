from fastapi import APIRouter, WebSocket, WebSocketException, Depends
from app.api.auth import *
from app.utils.crypto import *
from app.websockets.manager import *

router = APIRouter()

@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    user = await get_current_user_ws(ws)
    uname = user["username"]
    await manager.connect(uname, ws)
    try:
        while True:
            msg = await ws.receive_json()
            to = msg.get("to")
            data = msg.get("data")
            if to and data:
                await manager.send_personal(to, {"from": uname, "data": data})
    except WebSocketException:
        pass
    finally:
        manager.disconnect(uname)