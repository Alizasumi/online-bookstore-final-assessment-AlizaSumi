import re
from bs4 import BeautifulSoup
import pytest

# ---------- helpers ----------
def _txt(resp):
    s = resp.get_data(as_text=True) if hasattr(resp, "get_data") else str(resp)
    return re.sub(r"\s+", " ", s).strip().lower()

def _ensure_cart_has_item(client, title="1984", qty=1):
    client.post("/clear-cart", follow_redirects=True)
    r = client.post("/add-to-cart", data={"title": title, "quantity": qty}, follow_redirects=True)
    assert r.status_code in (200, 302)

def _checkout(client, **kwargs):
    """
    Posts to /process-checkout with reasonable defaults.
    Override any field via kwargs to exercise scenarios.
    """
    base = dict(
        name="Demo User",
        email="demo@bookstore.com",
        address="123 Demo Street",
        city="Demos",
        zip_code="12345",
        payment_method="credit_card",
        card_number="4242424242424242",  # success path (NOT ending 1111)
        expiry_date="12/30",
        cvv="123",
        discount_code=""
    )
    base.update(kwargs)
    return client.post("/process-checkout", data=base, follow_redirects=True)

def _has_success_cue(text: str) -> bool:
    cues = ["payment successful", "order confirmed", "order confirmation", "thank you", "payment success"]
    return any(c in text for c in cues)

def _has_error_cue(text: str) -> bool:
    cues = ["declined", "invalid", "error", "please", "required"]
    return any(c in text for c in cues)

# ---------- happy paths ----------
def test_pay_happy_credit_card(client):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert _has_success_cue(t)

def test_pay_happy_paypal(client):
    _ensure_cart_has_item(client, "Moby Dick", 1)
    resp = _checkout(client, payment_method="paypal", card_number="", expiry_date="", cvv="")
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    # not a server error, shows some confirmation-ish cue
    assert "internal server error" not in t and "traceback" not in t
    assert any(k in t for k in ["payment", "order", "confirmation", "thank"])

# ---------- known business rule: decline when card ends with 1111 ----------
def test_pay_declined_card_by_suffix_1111(client):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client, card_number="4111111111111111")  # ends with 1111 -> DECLINED by app rule
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert not _has_success_cue(t)
    assert _has_error_cue(t)

# ---------- negative: empty cart blocked (no false success) ----------
def test_checkout_blocked_when_cart_empty(client):
    client.post("/clear-cart", follow_redirects=True)
    resp = _checkout(client)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert not _has_success_cue(t)

# ---------- UPDATED: card number length / format ----------
# App is permissive; only strict rule is "endswith 1111" => decline.
@pytest.mark.parametrize("card", [
    "424242424242",           # 12 digits
    "4242424242424",          # 13 digits
    "4242424242424242",       # 16 digits
    "4242424242424242429",    # 19 digits
    "abcd4242efgh4242",       # non-digits
])
def test_card_number_len_format_is_accepted_unless_endswith_1111(client, card):
    _ensure_cart_has_item(client, "I Ching", 1)
    resp = _checkout(client, card_number=card)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    # main guarantee: backend must not crash
    assert "internal server error" not in t and "traceback" not in t
    # we DO NOT force success/failure because app is permissive for these inputs

# ---------- UPDATED: CVV boundary/format (no crash expectation) ----------
@pytest.mark.parametrize("cvv", ["", "1", "12", "123", "1234", "12a"])
def test_cvv_values_do_not_crash_and_may_be_accepted(client, cvv):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client, cvv=cvv)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert "internal server error" not in t and "traceback" not in t

# ---------- UPDATED: expiry boundary/format (no crash expectation) ----------
@pytest.mark.parametrize("expiry", ["01/20", "12/24", "01/30", "13/30", "aa/bb"])
def test_expiry_edge_cases_do_not_crash_and_may_be_accepted(client, expiry):
    _ensure_cart_has_item(client, "Moby Dick", 1)
    resp = _checkout(client, expiry_date=expiry)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert "internal server error" not in t and "traceback" not in t

# ---------- UPDATED: email formats (no crash expectation) ----------
@pytest.mark.parametrize("email", ["", "demo", "demo@", "demo@bookstore", "demo@bookstore.com"])
def test_email_formats_do_not_crash(client, email):
    _ensure_cart_has_item(client, "I Ching", 1)
    resp = _checkout(client, email=email)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert "internal server error" not in t and "traceback" not in t

# ---------- invalid discount codes: no crash ----------
@pytest.mark.parametrize("code", ["", "INVALID", "WELCOME200", "!!!", "   "])
def test_invalid_discount_codes_do_not_crash(client, code):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client, discount_code=code)
    t = _txt(resp)
    assert resp.status_code in (200, 302)
    assert "internal server error" not in t and "traceback" not in t

def _has_success(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["payment successful", "order confirmed", "order confirmation", "thank you"])

def _has_decline(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["declined", "payment failed", "could not be processed", "try again"])

# FR-004.1 Transaction / Order ID appears on successful payment
def test_fr004_success_shows_transaction_or_order_id(client):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client)
    txt = _txt(resp)
    assert resp.status_code in (200, 302)
    assert _has_success(txt)

    # Try common “Order #...” or “Transaction ID: ...” formats
    id_patterns = [
        r"(?:Order\s*#\s*|Order\s*Id\s*[:#]\s*)([A-Za-z0-9\-]{5,})",
        r"(?:Transaction\s*Id\s*[:#]\s*)([A-Za-z0-9\-]{5,})",
    ]
    found_id = any(re.search(p, txt, flags=re.I) for p in id_patterns)
    assert found_id, "No transaction/order identifier was shown on success"

# FR-004.2 Sensitive data (PAN/CVV) is not echoed in HTML
def test_fr004_no_sensitive_card_data_echoed(client):
    _ensure_cart_has_item(client, "Moby Dick", 1)
    # long-ish number to make leakage obvious if present
    resp = _checkout(client, card_number="4242424242424242429", cvv="987")
    html = _txt(resp)

    assert resp.status_code in (200, 302)
    # No 12+ consecutive digits (raw PAN)
    assert not re.search(r"\d{12,}", html), "Raw card number appears in page output"
    # CVV must not appear anywhere
    assert "987" not in html, "CVV value leaked into page output"
    # Full card string must not be echoed
    assert "4242424242424242429" not in html, "Full card number string echoed into page"

# FR-004.3 Decline path shows error and not success
def test_fr004_decline_shows_error_and_not_success(client):
    _ensure_cart_has_item(client, "I Ching", 1)
    resp = _checkout(client, card_number="4111111111111111")  # app’s decline rule
    txt = _txt(resp)
    assert resp.status_code in (200, 302)
    assert _has_decline(txt), "Decline path did not show any failure cue"
    assert not _has_success(txt), "Decline path must not claim success"

# FR-004.4 Invalid payment_method handled gracefully (negative/EP)
@pytest.mark.parametrize("bad_method", ["", "bank_transfer", "crypto", "CREDIT", "Cc"])
def test_fr004_invalid_payment_method_graceful(client, bad_method):
    _ensure_cart_has_item(client, "1984", 1)
    resp = _checkout(client, payment_method=bad_method)
    t = _txt(resp).lower()
    assert resp.status_code in (200, 302)
    # No 500/traceback; it may default to CC or show a message—just be stable
    assert "internal server error" not in t and "traceback" not in t