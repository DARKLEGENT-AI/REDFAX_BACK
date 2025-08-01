from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, username: str, ws: WebSocket):
        await ws.accept()
        self.active[username] = ws

    def disconnect(self, username: str):
        self.active.pop(username, None)

    async def send_personal(self, to: str, data: dict):
        ws = self.active.get(to)
        if ws:
            await ws.send_json(data)

    async def broadcast(self, users: list[str], data: dict):
        for u in users:
            if u in self.active:
                await self.active[u].send_json(data)


manager = ConnectionManager()