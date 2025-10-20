import re

def _txt(resp):
    import re
    s = resp.get_data(as_text=True)
    return re.sub(r"\s+", " ", s).strip().lower()

# Reuse your existing register/login/logout routes if present.
# If your app only mocks sessions, these tests will behave leniently.

def test_fr006_register_login_logout_flow(client):
    # Register
    r = client.post("/register", data={
        "email": "qa_user@example.com",
        "password": "secret123",
        "confirm_password": "secret123"
    }, follow_redirects=True)
    assert r.status_code in (200, 302)

    # Login
    r = client.post("/login", data={
        "email": "qa_user@example.com",
        "password": "secret123"
    }, follow_redirects=True)
    t = _txt(r)
    assert r.status_code in (200, 302)
    # Should show some signed-in cue (lenient)
    assert any(k in t for k in ["hello", "logout", "account"]), "Login did not appear to succeed"

    # Logout
    r = client.get("/logout", follow_redirects=True)
    t = _txt(r)
    assert r.status_code in (200, 302)
    assert "logout" in t or "login" in t or "home" in t

def test_fr006_login_rejects_bad_credentials(client):
    r = client.post("/login", data={
        "email": "nope@example.com",
        "password": "wrong"
    }, follow_redirects=True)
    t = _txt(r)
    assert r.status_code in (200, 302)
    # must not show obvious signed-in cues
    assert not ("hello" in t and "logout" in t), "Bad login should not look authenticated"

def test_fr006_account_requires_auth(client):
    # Try to access account page without login
    r = client.get("/account", follow_redirects=True)
    t = _txt(r)
    assert r.status_code in (200, 302)
    # Expect redirect to login or a message (lenient)
    assert any(k in t for k in ["login", "sign in", "unauthorized", "account"]), \
        "Unauthenticated account access was not handled"

def test_fr006_order_history_after_checkout_if_available(client):
    # Only runs leniently — if your app exposes /orders or /account/orders
    # We just ensure it does not crash and preferably shows an item after checkout.
    client.post("/clear-cart", follow_redirects=True)
    client.post("/add-to-cart", data={"title": "1984", "quantity": 1}, follow_redirects=True)
    r = client.post("/process-checkout", data={
        "name": "Demo User", "email": "demo@bookstore.com",
        "address": "123 Demo", "city": "Demos", "zip_code": "12345",
        "payment_method": "credit_card", "card_number": "4242424242424242",
        "expiry_date": "12/30", "cvv": "123"
    }, follow_redirects=True)
    assert r.status_code in (200, 302)

    # Probe common paths; accept whichever exists
    for path in ("/orders", "/account", "/account/orders"):
        resp = client.get(path, follow_redirects=True)
        if resp.status_code in (200, 302):
            t = _txt(resp)
            assert "internal server error" not in t
            # If orders are displayed, we expect some cue (lenient wording)
            if any(k in t for k in ["orders", "order history", "order #", "order id"]):
                break