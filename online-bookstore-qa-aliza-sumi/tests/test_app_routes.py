import re
from bs4 import BeautifulSoup  # pip install beautifulsoup4

def test_homepage(client):
    resp = client.get("/")
    assert resp.status_code == 200 or resp.status_code == 302

def test_login_page(client):
    resp = client.get("/login")
    assert resp.status_code in (200, 302)

def test_register_page(client):
    resp = client.get("/register")
    assert resp.status_code in (200, 302)

def test_cart_page(client):
    resp = client.get("/cart")
    assert resp.status_code in (200, 302)

def test_checkout_page(client):
    resp = client.get("/checkout")
    assert resp.status_code in (200, 302)

def test_catalog_renders_featured_books(client):
    resp = client.get("/")
    assert resp.status_code in (200, 302)

    html = resp.data.decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # ---- robust product discovery: one form per product ----
    price_pat = re.compile(r"\$\d+\.\d{2}")

    # 1) each product has its own add-to-cart form  (your route uses hyphen)
    forms = soup.find_all("form", attrs={"action": re.compile(r"(^|/)?add-?to-?cart/?$", re.I)})
    assert len(forms) == 4, f"Expected 4 add-to-cart forms, found {len(forms)}"

    # 2) for each form, find the nearest visual container (the product card block)
    cards = []
    for f in forms:
        card = f.find_parent("div", class_=re.compile(r"(book-card|card|product|item|col)", re.I))
        if card is None:
            card = f.find_parent("div")
        cards.append(card)

    # 3) de-duplicate AFTER the loop (some layouts nest)
    seen = set()
    unique_cards = []
    for c in cards:
        key = id(c)
        if key not in seen:
            seen.add(key)
            unique_cards.append(c)
    cards = unique_cards

    # 4) now assert we have 4 product tiles
    assert len(cards) == 4, f"Expected 4 product tiles, found {len(cards)}"

    # 5) per-card checks
    for c in cards:
        # title (selectors → image alt → hidden input → fallback text)
        title_text = None

        title_el = c.select_one(".card-title, h5, h4, .title, strong, b")
        if title_el and title_el.get_text(strip=True):
            title_text = title_el.get_text(strip=True)

        if not title_text:
            img = c.select_one("img[alt]")
            if img and img.get("alt"):
                title_text = img.get("alt").replace("Cover", "").strip()

        if not title_text:
            hidden = c.select_one('input[name="title"][type="hidden"], input[name="book_title"], input[name="name"]')
            if hidden and hidden.get("value"):
                title_text = hidden.get("value").strip()

        if not title_text:
            ban = re.compile(r"^(qty|quantity|add to cart|cart|price|\$?\d)", re.I)
            for line in (c.get_text("\n") or "").split("\n"):
                line = line.strip()
                if line and not ban.match(line):
                    title_text = line
                    break

        assert title_text, "Missing title in a card"

        # category
        has_category = bool(c.select_one(".category, .genre, .text-muted, small, em, i"))
        assert has_category, "Missing category/genre"

        # price anywhere in the tile
        assert price_pat.search(c.get_text()), "Missing or bad price format"

        # quantity input
        assert c.select_one("input[type=number], select"), "Missing quantity input"

        # add-to-cart control
        assert c.select_one("button, input[type=submit], a.btn, .btn"), "Missing Add to Cart control"

        # cover image present
        img = c.select_one("img")
        assert img and img.get("src"), "Missing cover image src"

def test_catalog_handles_invalid_query(client):
    """App should handle unknown query params gracefully"""
    resp = client.get("/?category=__nope__&page=9999", follow_redirects=True)
    # OK if 200 (page still renders) or redirect, just not 500
    assert resp.status_code in (200, 302)

def test_detail_unknown_book_does_not_crash(client):
    """If someone tries to access a non-existent book ID, app must not 500."""
    resp = client.get("/book/999999", follow_redirects=True)
    assert resp.status_code in (200, 302, 404)        
