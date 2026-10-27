"""API 路由集成测试（ASGI + SQLite）。"""

from app.models import User
from app.utils.password import hash_password


async def test_health(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["code"] == 200


async def test_register_login_me(client):
    r = await client.post(
        "/api/auth/register", json={"username": "apiuser", "password": "Pass1234"}
    )
    assert r.status_code == 200
    assert r.json()["code"] == 200

    r = await client.post("/api/auth/login", json={"username": "apiuser", "password": "Pass1234"})
    assert r.json()["code"] == 200
    token = r.json()["data"]["token"]

    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "apiuser"


async def test_register_invalid_password(client):
    r = await client.post("/api/auth/register", json={"username": "baduser", "password": "short"})
    assert r.status_code == 400
    assert r.json()["code"] == 400


async def test_users_requires_admin(client):
    await client.post("/api/auth/register", json={"username": "stu001", "password": "Pass1234"})
    r = await client.post("/api/auth/login", json={"username": "stu001", "password": "Pass1234"})
    token = r.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get("/api/users", headers=headers)
    assert r.status_code == 403


async def test_admin_list_users(client, db_session):
    admin = User(username="root01", password_hash=hash_password("Pass1234"), role="admin")
    db_session.add(admin)
    await db_session.commit()

    r = await client.post("/api/auth/login", json={"username": "root01", "password": "Pass1234"})
    token = r.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get("/api/users", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1


async def test_unauthorized_me(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
