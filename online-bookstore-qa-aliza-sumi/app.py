from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import Book, Cart, User, Order, PaymentGateway, EmailService
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Global storage for users and orders (in production, use a database)
users = {}  # email -> User object
orders = {}  # order_id -> Order object

# Create demo user for testing
demo_user = User("demo@bookstore.com", "demo123", "Demo User", "123 Demo Street, Demo City, DC 12345")
users["demo@bookstore.com"] = demo_user

# Create a cart instance to manage the cart
cart = Cart()

# Create a global books list to avoid duplication
BOOKS = [
    Book("The Great Gatsby", "Fiction", 10.99, "/images/books/the_great_gatsby.jpg"),
    Book("1984", "Dystopia", 8.99, "/images/books/1984.jpg"),
    Book("I Ching", "Traditional", 18.99, "/images/books/I-Ching.jpg"),
    Book("Moby Dick", "Adventure", 12.49, "/images/books/moby_dick.jpg")
]

def get_book_by_title(title):
    """Helper function to find a book by title"""
    return next((book for book in BOOKS if book.title == title), None)


def get_current_user():
    """Helper function to get current logged-in user"""
    if 'user_email' in session:
        return users.get(session['user_email'])
    return None


def login_required(f):
    """Decorator to require login for certain routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    current_user = get_current_user()
    return render_template('index.html', books=BOOKS, cart=cart, current_user=current_user)


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    book_title = (request.form.get('title') or '').strip()

    # safe parse + clamp so bad input never crashes backend
    raw_qty = request.form.get('quantity', '1')
    try:
        qty = int(float(raw_qty))   # handles "1.0"; "abc" → except
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(qty, 99))

    book = get_book_by_title(book_title)
    if book:
        cart.add_book(book, qty)
        flash(f'Added {qty} "{book.title}" to cart!', 'success')
    else:
        flash('Book not found!', 'error')

    return redirect(url_for('index'))


@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    book_title = request.form.get('title')
    cart.remove_book(book_title)
    flash(f'Removed "{book_title}" from cart!', 'success')
    return redirect(url_for('view_cart'))


@app.route('/update-cart', methods=['POST'])
def update_cart():
    """
    Update the quantity of a book in the cart.
    This function handles HTTP POST requests to update the quantity of a book in the user's cart.
    If the quantity is set to 0 or less, the book is effectively removed from the cart.
    Args:
        None (uses form data from the request)
    Returns:
        Response: Redirects to the view_cart page after updating the cart.
    Form Parameters:
        title (str): The title of the book to update.
        quantity (int): The new quantity of the book. Defaults to 1.
    Flash Messages:
        - Confirmation of removal if quantity <= 0
        - Confirmation of update otherwise
    """
    book_title = (request.form.get('title') or '').strip()
    raw_qty = request.form.get('quantity', '1')
    try:
        qty = int(float(raw_qty))
    except (TypeError, ValueError):
        # keep current qty if junk, or default to 1 if not in cart
        qty = cart.items.get(book_title, CartItem(Book(book_title, "", 0, ""), 1)).quantity
    # allow 0 to mean remove; clamp positives to 99
    qty = 0 if qty <= 0 else min(qty, 99)

    cart.update_quantity(book_title, qty)
    if qty <= 0:
        flash(f'Removed "{book_title}" from cart!', 'success')
    else:
        flash(f'Updated "{book_title}" quantity to {qty}!', 'success')
    return redirect(url_for('view_cart'))


@app.route('/cart')
def view_cart():
    current_user = get_current_user()
    return render_template('cart.html', cart=cart, current_user=current_user)


@app.route('/clear-cart', methods=['POST'])
def clear_cart():
    cart.clear()
    flash('Cart cleared!', 'success')
    return redirect(url_for('view_cart'))


@app.route('/checkout')
def checkout():
    if cart.is_empty():
        flash('Your cart is empty!', 'error')
        return redirect(url_for('index'))
    
    current_user = get_current_user()
    total_price = cart.get_total_price()
    return render_template('checkout.html', cart=cart, total_price=total_price, current_user=current_user)


@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    """Process the checkout form with shipping and payment information"""
    if cart.is_empty():
        flash('Your cart is empty!', 'error')
        return redirect(url_for('index'))
    
    # Get form data
    shipping_info = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'address': request.form.get('address'),
        'city': request.form.get('city'),
        'zip_code': request.form.get('zip_code')
    }
    
    payment_info = {
        'payment_method': request.form.get('payment_method'),
        'card_number': request.form.get('card_number'),
        'expiry_date': request.form.get('expiry_date'),
        'cvv': request.form.get('cvv')
    }
    
    discount_code = (request.form.get('discount_code') or '').strip().upper()
    
    # Calculate total with discount
    total_amount = cart.get_total_price()
    discount_applied = 0
    
    if discount_code == 'SAVE10':
        discount_applied = total_amount * 0.10
        total_amount -= discount_applied
        flash(f'Discount applied! You saved ${discount_applied:.2f}', 'success')
    elif discount_code == 'WELCOME20':
        discount_applied = total_amount * 0.20
        total_amount -= discount_applied
        flash(f'Welcome discount applied! You saved ${discount_applied:.2f}', 'success')
    elif discount_code:
        flash('Invalid discount code', 'error')
    
    required_fields = ['name', 'email', 'address', 'city', 'zip_code']
    for field in required_fields:
        if not shipping_info.get(field):
            flash(f'Please fill in the {field.replace("_", " ")} field', 'error')
            return redirect(url_for('checkout'))
    
    if payment_info['payment_method'] == 'credit_card':
        if not payment_info.get('card_number') or not payment_info.get('expiry_date') or not payment_info.get('cvv'):
            flash('Please fill in all credit card details', 'error')
            return redirect(url_for('checkout'))
    
    # Process payment through mock gateway
    payment_result = PaymentGateway.process_payment(payment_info)
    
    if not payment_result['success']:
        flash(payment_result['message'], 'error')
        return redirect(url_for('checkout'))
    
    # Create order
    order_id = str(uuid.uuid4())[:8].upper()
    order = Order(
        order_id=order_id,
        user_email=shipping_info['email'],
        items=cart.get_items(),
        shipping_info=shipping_info,
        payment_info={
            'method': payment_info['payment_method'],
            'transaction_id': payment_result['transaction_id']
        },
        total_amount=total_amount
    )
    
    # Store order
    orders[order_id] = order
    
    # Add order to user if logged in
    current_user = get_current_user()
    if current_user:
        current_user.add_order(order)
    
    # Send confirmation email (mock)
    EmailService.send_order_confirmation(shipping_info['email'], order)
    
    # Clear cart
    cart.clear()
    
    # Store order in session for confirmation page
    session['last_order_id'] = order_id
    
    flash('Payment successful! Your order has been confirmed.', 'success')
    return redirect(url_for('order_confirmation', order_id=order_id))


@app.route('/order-confirmation/<order_id>')
def order_confirmation(order_id):
    """Display order confirmation page"""
    order = orders.get(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('index'))
    
    current_user = get_current_user()
    return render_template('order_confirmation.html', order=order, current_user=current_user)


# User Account Management Routes

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address', '')
        
        # Validate required fields
        if not email or not password or not name:
            flash('Please fill in all required fields', 'error')
            return render_template('register.html')
        
        if email in users:
            flash('An account with this email already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(email, password, name, address)
        users[email] = user
        
        # Log in the user
        session['user_email'] = email
        flash('Account created successfully! You are now logged in.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = users.get(email)
        if user and user.password == password:
            session['user_email'] = email
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_email', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/account')
@login_required
def account():
    """User account page"""
    current_user = get_current_user()
    return render_template('account.html', current_user=current_user)


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    current_user = get_current_user()
    
    current_user.name = request.form.get('name', current_user.name)
    current_user.address = request.form.get('address', current_user.address)
    
    new_password = request.form.get('new_password')
    if new_password:
        current_user.password = new_password
        flash('Password updated successfully!', 'success')
    else:
        flash('Profile updated successfully!', 'success')
    
    return redirect(url_for('account'))


if __name__ == '__main__':
    app.run(debug=True)
