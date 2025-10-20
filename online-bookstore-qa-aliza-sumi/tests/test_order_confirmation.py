import re
from bs4 import BeautifulSoup

def _txt(resp):
    s = resp.get_data(as_text=True)
    return re.sub(r"\s+", " ", s).strip()

def _soup(resp):
    return BeautifulSoup(resp.get_data(as_text=True), "html.parser")

def _ensure_cart_has_item(client, title="1984", qty=1):
    client.post("/clear-cart", follow_redirects=True)
    r = client.post("/add-to-cart", data={"title": title, "quantity": qty}, follow_redirects=True)
    assert r.status_code in (200, 302)

def _checkout(client, **kwargs):
    base = dict(
        name="Demo User",
        email="demo@bookstore.com",
        address="123 Demo Street",
        city="Demos",
        zip_code="12345",
        payment_method="credit_card",
        card_number="4242424242424242",
        expiry_date="12/30",
        cvv="123",
        discount_code=""
    )
    base.update(kwargs)
    return client.post("/process-checkout", data=base, follow_redirects=True)

def _success(txt: str) -> bool:
    t = txt.lower()
    return any(k in t for k in ["payment successful", "order confirmed", "order confirmation", "thank you"])

# FR-005.1: confirmation page shows itemized summary with prices and quantities
def test_fr005_confirmation_page_itemized_summary(client):
    _ensure_cart_has_item(client, "1984", 2)
    resp = _checkout(client)
    txt = _txt(resp)
    soup = _soup(resp)

    assert resp.status_code in (200, 302)
    assert _success(txt)

    # prices present
    assert soup.find(string=re.compile(r"\$\d+\.\d{2}")), "No currency values on confirmation"
    # at least one line item with a title
    assert soup.find(string=re.compile(r"1984", re.I)), "Expected item title not shown"

# FR-005.2: a unique order/transaction id is displayed
def test_fr005_confirmation_shows_order_id(client):
    _ensure_cart_has_item(client, "Moby Dick", 1)
    resp = _checkout(client)
    txt = _txt(resp)

    id_patterns = [
        r"(?:Order\s*#\s*|Order\s*Id\s*[:#]\s*)([A-Za-z0-9\-]{5,})",
        r"(?:Transaction\s*Id\s*[:#]\s*)([A-Za-z0-9\-]{5,})",
    ]
    assert any(re.search(p, txt, re.I) for p in id_patterns), "No order/transaction id on confirmation page"

# FR-005.3: email confirmation mock prints expected details to stdout
# We capture stdout via pytest's capsys fixture.
def test_fr005_email_confirmation_contains_key_details(client, capsys):
    _ensure_cart_has_item(client, "I Ching", 1)
    resp = _checkout(client)
    assert resp.status_code in (200, 302)

    out = capsys.readouterr().out  # read printed mock email
    # Look for a simple email skeleton in stdout
    assert "EMAIL SENT" in out or "To:" in out, "Mock email output not printed to stdout"
    # Contains recipient, order id, items, total, and shipping info (lenient checks)
    assert re.search(r"Order\s*(?:#|Id)", out, re.I), "Email missing order id"
    assert re.search(r"I\s*Ching", out, re.I), "Email missing item title"
    assert re.search(r"\$\d+\.\d{2}", out), "Email missing currency value"
    assert re.search(r"Address|Shipping", out, re.I), "Email missing shipping details"

# FR-005.4: invalid checkout should not claim success
def test_fr005_invalid_checkout_does_not_show_success(client):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client, name="", email="", address="", city="", zip_code="")
    txt = _txt(resp).lower()
    assert resp.status_code in (200, 302)
    assert "internal server error" not in txt
    assert not any(k in txt for k in ["payment successful", "order confirmed"]), \
        "Invalid checkout should not show success"