import os
import sys
import pathlib
import pytest
from httpx import AsyncClient, ASGITransport

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from app.main import app

@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    monkeypatch.setenv('TESTING', '1')

@pytest.mark.asyncio
async def test_register_login_and_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/auth/register", json={"username": "alice", "password": "pw"})
        assert r.status_code == 200
        r = await ac.post("/auth/register", json={"username": "bob", "password": "pw"})
        assert r.status_code == 200
        r = await ac.post("/auth/token", json={"username": "alice", "password": "pw"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r = await ac.post("/messages/", json={"receiver": "bob", "content": "hi"}, headers=headers)
        assert r.status_code == 200
        r = await ac.post("/auth/token", json={"username": "bob", "password": "pw"})
        token2 = r.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        r = await ac.get("/messages/", headers=headers2)
        assert r.status_code == 200
        data = r.json()
        assert any(m["content"] == "hi" for m in data)
