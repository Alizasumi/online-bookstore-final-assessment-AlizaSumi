import os, sys, io, cProfile, pstats
from importlib import import_module
import importlib.util

def get_app():
    """
    Dynamically import the Flask app from the correct project folder
    even when running profiling from another directory.
    """

    APP_PATH = os.path.abspath("../online-bookstore-qa-aliza-sumi/app.py")
    APP_DIR = os.path.dirname(APP_PATH)

    # Ensure app folder is importable and set CWD so relative imports work
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    os.chdir(APP_DIR)

    if not os.path.exists(APP_PATH):
        raise FileNotFoundError(f"app.py not found at: {APP_PATH}")

    spec = importlib.util.spec_from_file_location("app", APP_PATH)
    app_module = importlib.util.module_from_spec(spec)
    sys.modules["app"] = app_module
    spec.loader.exec_module(app_module)

    app_obj = getattr(app_module, "app", None)
    if app_obj is None and hasattr(app_module, "create_app"):
        app_obj = app_module.create_app(testing=True)

    try:
        app_obj.config.update(TESTING=True)
    except Exception:
        pass
    return app_obj

def main():
    app = get_app()
    # if you want to force testing config:
    try:
        app.config.update(TESTING=True)
    except Exception:
        pass

    client = app.test_client()

    # ---- realistic smoke flow ----
    pr = cProfile.Profile()
    pr.enable()

    client.get("/")
    client.get("/cart")
    client.post("/add-to-cart", data={"title": "1984", "quantity": 1}, follow_redirects=True)
    client.get("/checkout")
    client.post(
        "/process-checkout",
        data={
            "name": "Demo User",
            "email": "demo@bookstore.com",
            "address": "123 Demo Street",
            "city": "Demos",
            "zip_code": "12345",
            "payment_method": "credit_card",
            "card_number": "4242424242424242",
            "expiry_date": "12/30",
            "cvv": "123",
        },
        follow_redirects=True,
    )

    pr.disable()

    # ---- print and save top offenders ----
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(25)
    text = s.getvalue()
    print(text)

    os.makedirs("profiling", exist_ok=True)
    with open("profiling/checkout.profile.txt", "w", encoding="utf-8") as f:
        f.write(text)

if __name__ == "__main__":
    main()