# Online Bookstore Flask Application

## 📚 Academic Project - Software Testing Learning

**⚠️ ACADEMIC USE ONLY - FOR EDUCATIONAL PURPOSES**

## 🛍️ Application Overview

The Online Bookstore is a comprehensive e-commerce web application built with Flask that demonstrates modern software patterns, user authentication, payment processing, and order management scenarios ideal for software testing education.

## ⚠️ IMPORTANT NOTE FOR TESTING

**This application intentionally contains bugs, inefficiencies, and edge cases** to provide realistic testing scenarios for educational purposes. Students are expected to:

- **Discover Issues**: Find bugs through systematic testing
- **Document Problems**: Create detailed bug reports
- **Propose Solutions**: Suggest fixes for identified issues
- **Improve Performance**: Identify and optimize inefficient code
- **Enhance Security**: Find and address security vulnerabilities

The goal is to learn through discovery and problem-solving. Use various testing techniques including:
- Functional testing
- Performance testing  
- Security testing
- Usability testing
- Edge case testing

### 🚀 Features Implemented

#### 📖 Book Catalog (FR-001)
- Display featured books with details (title, category, price, cover image)
- Browse available inventory
- View book information

#### 🛒 Shopping Cart Functionality (FR-002)
- **Add to Cart**: Add books with specified quantities
- **View Cart**: Display cart contents with quantities and totals
- **Update Cart**: Modify item quantities
- **Remove Items**: Delete items from cart
- **Clear Cart**: Remove all items
- **Dynamic Pricing**: Real-time total calculations

#### 💳 Enhanced Checkout Process (FR-003)
- **Order Summary**: Complete itemized list with quantities and prices
- **Shipping Information**: Customer details collection (name, address, email)
- **Payment Methods**: Credit card and PayPal options
- **Discount Codes**: Promotional offers support (try `SAVE10` or `WELCOME20`)
- **Form Validation**: Required field validation and error handling
- **Mock Payment Processing**: Simulated payment gateway integration

#### 🔒 Secure Payment Processing (FR-004)
- **Payment Gateway Mock**: Simulated secure payment processing
- **Credit Card Validation**: Mock validation with test scenarios
- **Transaction IDs**: Generated for successful payments
- **Error Handling**: Payment failure scenarios (try card ending in 1111)
- **SSL/TLS Simulation**: Encrypted connection mock

#### 📧 Order Confirmation (FR-005)
- **Email Confirmation**: Mock email service with console output
- **Order Details**: Complete order summary display
- **Order Tracking**: Unique order ID generation
- **Confirmation Page**: Detailed order confirmation with next steps

#### 👤 User Account Management (FR-006)
- **User Registration**: Account creation with email and password
- **User Authentication**: Login/logout functionality
- **Profile Management**: Update personal information and password
- **Order History**: View past orders and order details
- **Session Management**: Persistent user sessions

#### 📱 Responsive Design (FR-007)
- **Mobile-First**: Optimized for mobile devices
- **Tablet Support**: Adapted layouts for tablets
- **Desktop Experience**: Full-featured desktop interface
- **Flexible Navigation**: Responsive navigation menus
- **Touch-Friendly**: Mobile-optimized interactions

## 🏗️ Technical Architecture

### Backend
- **Framework**: Flask (Python web framework)
- **Language**: Python 3.11+
- **Session Management**: Flask sessions for cart and user authentication
- **Template Engine**: Jinja2 for dynamic HTML rendering
- **Mock Services**: Payment gateway and email service simulation

### Frontend
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Custom styling with responsive grid layouts
- **JavaScript**: Enhanced form interactions and validation
- **Mobile-First**: Responsive design principles

### Mock Integrations
- **Payment Gateway**: Simulated payment processing with success/failure scenarios
- **Email Service**: Console-based email confirmation simulation
- **User Database**: In-memory user storage (for demo purposes)

### Project Structure
```
online-bookstore-flask/
│
├── app.py                 # Main Flask application with all routes
├── models.py             # Data models (Book, Cart, User, Order, etc.)
├── requirements.txt      # Python dependencies
├── README.md            # This comprehensive documentation
│
├── static/
│   ├── styles.css       # Enhanced responsive styling
│   ├── logo.png         # Store logo
│   └── images/
│       └── books/       # Book cover images
│
└── templates/
    ├── index.html           # Home page with user navigation
    ├── cart.html            # Shopping cart page
    ├── checkout.html        # Enhanced checkout form
    ├── order_confirmation.html  # Order confirmation page
    ├── login.html           # User login page
    ├── register.html        # User registration page
    └── account.html         # User account management
```

## 🧪 Testing Features

### User Authentication Testing
- **Demo Account**: 
  - Email: `demo@bookstore.com`
  - Password: `demo123`
- **Registration**: Test account creation flow
- **Login/Logout**: Session management testing

### Payment Processing Testing
- **Successful Payment**: Use any card number except those ending in 1111
- **Failed Payment**: Use card number ending in 1111 to test error handling
- **Payment Methods**: Test both credit card and PayPal options

### Discount Code Testing
- **SAVE10**: 10% discount
- **WELCOME20**: 20% discount
- **Invalid codes**: Test error handling

### Form Validation Testing
- **Required Fields**: Test empty field validation
- **Email Format**: Test email validation
- **Payment Information**: Test credit card field validation

### Responsive Design Testing
- **Mobile**: Test on various mobile screen sizes
- **Tablet**: Test tablet layouts and interactions
- **Desktop**: Full desktop functionality

## 📋 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

### Quick Start
1. **Clone or download** the project files
2. **Navigate** to the project directory
3. **Create virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the application**:
   ```bash
   python app.py
   ```
6. **Open browser** and go to `http://127.0.0.1:5000`

## ⚖️ Academic Integrity

This project is provided for educational purposes only. Students should:
- Use this code for learning testing concepts
- Create original test cases and documentation
- Properly cite any external testing frameworks or tools used
- Follow academic honesty policies

**Remember**: The goal is learning! Focus on understanding testing principles, creating thorough test cases, and documenting your testing process. Good luck with your software testing journey! 🎓
