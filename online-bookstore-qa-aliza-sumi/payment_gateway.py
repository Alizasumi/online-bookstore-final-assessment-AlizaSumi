# online-bookstore-qa-aliza-sumi/payment_gateway.py

def process_payment(card_number: str, amount: float):
    """
    Mock payment:
      - Decline if the card ends with '1111' (your README rule)
      - Otherwise approve and return a fake transaction id
    """
    if not card_number or len(str(card_number)) < 4:
        return {"status": "error", "reason": "Invalid card"}

    if str(card_number).strip().endswith("1111"):
        return {"status": "declined", "reason": "Card declined"}

    return {
        "status": "approved",
        "transaction_id": f"TXN-{str(card_number)[-4:]}",
        "amount": float(amount),
    }