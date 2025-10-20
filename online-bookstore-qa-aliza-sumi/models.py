class Book:
    def __init__(self, title, category, price, image):
        self.title = title
        self.category = category
        self.price = price
        self.image = image


class CartItem:
    def __init__(self, book, quantity=1):
        self.book = book
        self.quantity = quantity
    
    def get_total_price(self):
        return self.book.price * self.quantity


class Cart:
    """
    A shopping cart class that holds book items and their quantities.

    The Cart uses a dictionary with book titles as keys for efficient lookups,
    allowing operations like adding, removing, and updating book quantities.

    Attributes:
        items (dict): Dictionary storing CartItem objects with book titles as keys.

    Methods:
        add_book(book, quantity=1): Add a book to the cart with specified quantity.
        remove_book(book_title): Remove a book from the cart by title.
        update_quantity(book_title, quantity): Update quantity of a book in the cart.
        get_total_price(): Calculate total price of all items in the cart.
        get_total_items(): Get the total count of all books in the cart.
        clear(): Remove all items from the cart.
        get_items(): Return a list of all CartItem objects in the cart.
        is_empty(): Check if the cart has no items.
    """
    def __init__(self):
        self.items = {}  # Using dict with book title as key for easy lookup

    def add_book(self, book, quantity=1):
        if book.title in self.items:
            self.items[book.title].quantity += quantity
        else:
            self.items[book.title] = CartItem(book, quantity)

    def remove_book(self, book_title):
        if book_title in self.items:
            del self.items[book_title]

    def update_quantity(self, book_title, quantity):
        if book_title not in self.items:
            return
        # Parse quantity safely
        try:
            q = int(quantity)
        except (TypeError, ValueError):
            # keep previous quantity if input is junk
            q = self.items[book_title].quantity
        # Remove item if q <= 0, clamp to max 99 otherwise
        if q <= 0:
            del self.items[book_title]
        else:
            self.items[book_title].quantity = min(q, 99)

    def get_total_price(self):
        return sum(item.book.price * item.quantity for item in self.items.values())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.values())

    def clear(self):
        self.items = {}

    def get_items(self):
        return list(self.items.values())

    def is_empty(self):
        return len(self.items) == 0


class User:
    """User account management class"""
    def __init__(self, email, password, name="", address=""):
        self.email = email
        self.password = password
        self.name = name
        self.address = address
        self.orders = []
        self.temp_data = []
        self.cache = {}
    
    def add_order(self, order):
        self.orders.append(order)
        self.orders.sort(key=lambda x: x.order_date)
    
    def get_order_history(self):
        return [order for order in self.orders]


class Order:
    """Order management class"""
    def __init__(self, order_id, user_email, items, shipping_info, payment_info, total_amount):
        import datetime
        self.order_id = order_id
        self.user_email = user_email
        self.items = items.copy()  # Copy of cart items
        self.shipping_info = shipping_info
        self.payment_info = payment_info
        self.total_amount = total_amount
        self.order_date = datetime.datetime.now()
        self.status = "Confirmed"
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'user_email': self.user_email,
            'items': [{'title': item.book.title, 'quantity': item.quantity, 'price': item.book.price} for item in self.items],
            'shipping_info': self.shipping_info,
            'total_amount': self.total_amount,
            'order_date': self.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status
        }


class PaymentGateway:
    """Mock payment gateway for processing payments"""
    
    @staticmethod
    def process_payment(payment_info):
        """
        Validates basic fields and returns a mock result.
        Rules:
          - Unknown payment_method => fail
          - credit_card:
              * card_number: 13-19 digits; if endswith 1111 => decline
              * expiry_date: MM/YY or MM/YYYY (01-12 for MM)
              * cvv: 3-4 digits
          - paypal:
              * payer_email must look like an email
        """
        method = (payment_info.get('payment_method') or '').strip().lower()

        if method not in ('credit_card', 'paypal'):
            return {'success': False, 'message': 'Unsupported payment method', 'transaction_id': None}

        import re, random, time
        time.sleep(0.05)  # small mock latency

        if method == 'credit_card':
            number = ''.join((payment_info.get('card_number') or '').split())
            expiry = (payment_info.get('expiry_date') or '').strip()
            cvv    = (payment_info.get('cvv') or '').strip()

            if not re.fullmatch(r'\d{13,19}', number or ''):
                return {'success': False, 'message': 'Invalid card number format', 'transaction_id': None}
            # Instructor rule: any card ending in 1111 is declined
            if number.endswith('1111'):
                return {'success': False, 'message': 'Payment declined by issuer', 'transaction_id': None}

            if not re.fullmatch(r'(0[1-9]|1[0-2])\/(\d{2}|\d{4})', expiry):
                return {'success': False, 'message': 'Invalid expiry date', 'transaction_id': None}

            if not re.fullmatch(r'\d{3,4}', cvv):
                return {'success': False, 'message': 'Invalid CVV', 'transaction_id': None}

        else:  # paypal
            payer = (payment_info.get('payer_email') or '').strip()
            if not re.fullmatch(r'[^@]+@[^@]+\.[^@]+', payer):
                return {'success': False, 'message': 'Invalid PayPal account email', 'transaction_id': None}

        txn = f"TXN{random.randint(100000, 999999)}"
        return {'success': True, 'message': 'Payment processed successfully', 'transaction_id': txn}


class EmailService:
    """Mock email service for sending order confirmations"""
    
    @staticmethod
    def send_order_confirmation(user_email, order):
        """Mock email sending - just prints to console in this implementation"""
        print(f"\n=== EMAIL SENT ===")
        print(f"To: {user_email}")
        print(f"Subject: Order Confirmation - Order #{order.order_id}")
        print(f"Order Date: {order.order_date}")
        print(f"Total Amount: ${order.total_amount:.2f}")
        print(f"Items:")
        for item in order.items:
            print(f"  - {item.book.title} x{item.quantity} @ ${item.book.price:.2f}")
        print(f"Shipping Address: {order.shipping_info.get('address', 'N/A')}")
        print(f"==================\n")
        
        return True
