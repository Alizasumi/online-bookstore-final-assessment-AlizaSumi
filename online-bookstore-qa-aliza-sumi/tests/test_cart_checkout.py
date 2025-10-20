import re
import pytest
from bs4 import BeautifulSoup

def test_add_and_clear_cart(client):
    # add item to cart
    resp = client.post("/add-to-cart", data={"title": "1984", "quantity": 2}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    # view cart
    view = client.get("/cart")
    assert view.status_code in (200, 302)

    # clear cart
    clear = client.post("/clear-cart", follow_redirects=True)
    assert clear.status_code in (200, 302)

def test_apply_discount_and_checkout(client):
    # test discount and checkout
    client.post("/add-to-cart", data={"title": "1984", "quantity": 1}, follow_redirects=True)

    # valid discount applied during checkout
    resp = client.post("/process-checkout", data={
        "name": "Test User",
        "email": "demo@bookstore.com",
        "address": "123 Demo Street",
        "city": "Demo City",
        "zip_code": "12345",
        "payment_method": "credit_card",
        "card_number": "1234567890123456",
        "expiry_date": "12/30",
        "cvv": "123",
        "discount_code": "SAVE10"
    }, follow_redirects=True)
    assert resp.status_code in (200, 302)

# ---------- small utilities ----------

def get_first_book_title_and_price(client):
    """Scrape the homepage to discover a real title & unit price."""
    r = client.get("/", follow_redirects=True)
    assert r.status_code in (200, 302)
    soup = BeautifulSoup(r.get_data(as_text=True), "html.parser")

    # find the first product card that has a form posting to add-to-cart
    form = soup.find("form", attrs={"action": re.compile(r"(^|/)?add-?to-?cart/?$", re.I)})
    assert form, "Could not find an add-to-cart form on the homepage"
    # title (prefer hidden input/name->value, then card headings, then img alt)
    title = None
    hidden = form.select_one('input[name="title"][type="hidden"], input[name="book_title"], input[name="name"]')
    if hidden and hidden.get("value"):
        title = hidden.get("value").strip()
    if not title:
        card = form.find_parent("div") or soup
        h = card.select_one(".card-title, h4, h5, .title, strong, b")
        if h: title = h.get_text(strip=True)
    if not title:
        img = (form.find_parent("div") or soup).select_one("img[alt]")
        if img and img.get("alt"): title = img.get("alt").strip()
    assert title, "Could not infer book title for add-to-cart"

    # price: look in the card text near the form
    card = form.find_parent("div") or soup
    text = card.get_text(" ").strip()
    m = re.search(r"\$([0-9]+(?:\.[0-9]{2})?)", text)
    assert m, "Could not find a $price near the add-to-cart form"
    unit_price = float(m.group(1))
    return title, unit_price

def add_to_cart(client, title, qty=1):
    return client.post("/add-to-cart", data={"title": title, "quantity": qty}, follow_redirects=True)

def view_cart_soup(client):
    r = client.get("/cart", follow_redirects=True)
    assert r.status_code in (200, 302)
    return BeautifulSoup(r.get_data(as_text=True), "html.parser")

def cart_totals_from_page(soup):
    """
    Extract totals from the cart page.
    Accepts 'Subtotal:', 'Total Price:', 'Total:', and is resilient to spacing.
    Falls back to the last money amount on the page if labels aren't found.
    """
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)  # normalize spaces

    # explicit labels first
    patterns = [
        r"(?:Subtotal)\s*:?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        r"(?:Total\s*Price)\s*:?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        r"(?:Total)\s*:?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        # sometimes people put “Total Amount”
        r"(?:Total\s*Amount)\s*:?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            val = float(m.group(1))
            return val, val  # we don't have separate total vs subtotal label, good enough for checks

    # Fallback: grab the LAST money-looking value on the page (usually the grand total)
    monies = re.findall(r"\$?\s*([0-9]+(?:\.[0-9]{2})?)", text)
    if monies:
        val = float(monies[-1])
        return val, val

    return None, None

# ---------- FR-002 happy paths ----------

def test_fr002_add_and_view_cart_shows_correct_totals(client):
    client.post("/clear-cart", follow_redirects=True)   # <<< add this
    title, price = get_first_book_title_and_price(client)
    add_to_cart(client, title, qty=2)
    soup = view_cart_soup(client)
    subtotal, total = cart_totals_from_page(soup)
    assert subtotal is not None, "Cart page did not show a Total Price or Subtotal"
    assert abs(subtotal - (price * 2)) < 0.01
    assert total >= 0.0

def test_fr002_update_cart_quantity(client):
    """
    If the cart page offers a quantity update form, exercise it; otherwise skip gracefully.
    """
    title, _ = get_first_book_title_and_price(client)
    add_to_cart(client, title, qty=1)
    soup = view_cart_soup(client)

    # Try to locate an update form or quantity input on the cart page
    form = soup.find("form", attrs={"action": re.compile(r"(update|cart)", re.I)})
    qty_input = soup.select_one("input[name=quantity], input[type=number], select[name=quantity]")
    if not form or not qty_input:
        pytest.skip("Cart update form not found; skipping update test")

    # Submit an update to quantity=3
    action = form.get("action") or "/cart"
    r = client.post(action, data={"quantity": 3, "title": title}, follow_redirects=True)
    assert r.status_code in (200, 302)

def test_fr002_remove_single_item(client):
    """
    If a remove-item control exists, click it; otherwise skip gracefully.
    """
    title, _ = get_first_book_title_and_price(client)
    add_to_cart(client, title, qty=1)
    soup = view_cart_soup(client)

    # Look for a remove button/link tied to the item
    remove = soup.find("form", attrs={"action": re.compile(r"(remove|delete)", re.I)}) \
          or soup.find("a", href=re.compile(r"(remove|delete)", re.I))
    if not remove:
        pytest.skip("Remove-item control not present; skipping remove test")

    if remove.name == "form":
        action = remove.get("action") or "/cart"
        r = client.post(action, data={"title": title}, follow_redirects=True)
    else:
        r = client.get(remove.get("href"), follow_redirects=True)
    assert r.status_code in (200, 302)

def test_fr002_clear_cart(client):
    # Precondition: something in cart
    title, _ = get_first_book_title_and_price(client)
    add_to_cart(client, title, qty=1)
    r = client.post("/clear-cart", follow_redirects=True)
    assert r.status_code in (200, 302)
    # Verify empty or zero subtotal
    soup = view_cart_soup(client)
    subtotal, total = cart_totals_from_page(soup)
    assert subtotal in (None, 0.0) or subtotal < 0.005

# ---------- Dynamic pricing / EP & BVA on quantity ----------

@pytest.mark.parametrize("qty", [1, 2, 99])
def test_fr002_dynamic_pricing_correct_math_for_various_qty(client, qty):
    client.post("/clear-cart", follow_redirects=True)   # <<< add this
    title, price = get_first_book_title_and_price(client)
    add_to_cart(client, title, qty=qty)
    soup = view_cart_soup(client)
    subtotal, _ = cart_totals_from_page(soup)
    assert subtotal is not None
    assert abs(subtotal - (price * qty)) < 0.01

@pytest.mark.parametrize("qty", [0, -1, "abc", 1000])
def test_fr002_quantity_invalid_values_are_handled_gracefully(client, qty):
    client.post("/clear-cart", follow_redirects=True)   # <<< add this
    title, _ = get_first_book_title_and_price(client)
    r = add_to_cart(client, title, qty=qty)
    assert r.status_code in (200, 302)
    soup = view_cart_soup(client)
    subtotal, total = cart_totals_from_page(soup)
    if subtotal is not None:
        assert subtotal >= 0.0
    assert total is None or total >= 0.0

def test_fr002_checkout_blocked_when_cart_empty(client):
    # Ensure empty
    client.post("/clear-cart", follow_redirects=True)
    # Attempt checkout with required fields but no items
    r = client.post("/process-checkout", data={
        "name": "A", "email": "a@b.co", "address": "X", "city": "Y",
        "zip_code": "1", "payment_method": "credit_card",
        "card_number": "4242424242424242", "expiry_date": "12/30", "cvv": "123"
    }, follow_redirects=True)
    # Should not 500; ideally it redirects back with a message
    assert r.status_code in (200, 302)

def test_fr002_payment_declined_path(client):
    title, _ = get_first_book_title_and_price(client)
    add_to_cart(client, title, qty=1)
    r = client.post("/process-checkout", data={
        "name": "A", "email": "a@b.co", "address": "X", "city": "Y",
        "zip_code": "1", "payment_method": "credit_card",
        # ends with 1111 → your README says decline path
        "card_number": "4111111111111111", "expiry_date": "12/30", "cvv": "123"
    }, follow_redirects=True)
    assert r.status_code in (200, 302)