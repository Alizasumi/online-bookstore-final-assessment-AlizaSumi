import uuid

def test_register_and_login(client):
    email = f"student_{uuid.uuid4().hex[:6]}@example.com"
    register = client.post("/register", data={"email": email, "password": "Password123!"}, follow_redirects=True)
    assert register.status_code in (200, 302)

    login = client.post("/login", data={"email": email, "password": "Password123!"}, follow_redirects=True)
    assert login.status_code in (200, 302)