# profiling/timeit_snippets.py
from random import randint, seed
import timeit

def build_cart(n=2000):
    items = [{"price": randint(5, 50), "qty": randint(1, 3)} for _ in range(n)]
    return sum(i["price"] * i["qty"] for i in items)

def slow_build_cart(n=2000):
    items = [{"price": randint(5, 50), "qty": randint(1, 3)} for _ in range(n)]
    total = 0
    for i in range(len(items)):
        total += items[i]["price"] * items[i]["qty"]
    return total

def run_once(label, fn, n_calls=50):
    # Re-seed for repeatability across runs
    seed(42)
    secs = timeit.timeit(lambda: fn(2000), number=n_calls)
    print(f"{label}: {secs:.4f}s for {n_calls} calls  ({secs/n_calls*1000:.2f} ms/call)")

if __name__ == "__main__":
    print("=== synthetic microbenchmarks (repeatable) ===")
    run_once("fast  build_cart", build_cart, n_calls=50)
    run_once("slow  build_cart", slow_build_cart, n_calls=50)