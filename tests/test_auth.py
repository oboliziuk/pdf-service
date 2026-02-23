import pytest

USER = {
    "name": "John",
    "surname": "Doe",
    "email": "john@example.com",
    "date_of_birth": "1990-01-01",
    "password": "secret123",
}


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/register", json=USER)
    assert response.status_code == 200
    assert "password" not in response.json()


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/register", json=USER)
    response = await client.post("/login", json={
        "email": USER["email"],
        "password": USER["password"],
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/register", json=USER)
    response = await client.post("/login", json={
        "email": USER["email"],
        "password": "wrongpassword",
    })
    assert response.status_code == 401
