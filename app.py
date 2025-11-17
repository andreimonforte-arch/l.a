from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import csv
from io import StringIO, BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None


@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    return dict(cart_count=cart_count)


# ==================== MODELS ====================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Product {self.product_code} - {self.name}>'


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.first_name} {self.last_name}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    is_deleted = db.Column(db.Boolean, default=False)
    order_details = db.relationship('OrderDetail', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'


class OrderDetail(db.Model):
    __tablename__ = 'order_details'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_details', lazy=True)

    def __repr__(self):
        return f'<OrderDetail {self.id}>'


# ==================== DECORATORS ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'Admin':
            flash('Admin access required for this action.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== HELPER FUNCTIONS ====================
def get_cart():
    return session.get('cart', {})


def save_cart(cart):
    session['cart'] = cart
    session.modified = True


def calculate_cart_total(cart):
    total = 0
    for item_id, item_data in cart.items():
        total += item_data['price'] * item_data['quantity']
    return total


def validate_category(name, current_id=None):
    errors = []
    if not name or len(name) < 2 or len(name) > 50:
        errors.append("Category name must be between 2 and 50 characters.")
    existing = Category.query.filter_by(name=name, is_deleted=False).first()
    if existing and (not current_id or existing.id != current_id):
        errors.append("Category name already exists.")
    return errors


def validate_product(product_code, name, category_id, size, color, price, quantity, current_id=None):
    errors = []
    if not product_code or len(product_code) < 3 or len(product_code) > 20:
        errors.append("Product code must be between 3 and 20 characters.")
    if not name or len(name) < 2 or len(name) > 100:
        errors.append("Product name must be between 2 and 100 characters.")
    if not category_id:
        errors.append("Please select a category.")
    else:
        category = Category.query.filter_by(id=category_id, is_deleted=False).first()
        if not category:
            errors.append("Selected category does not exist.")
    if not size or len(size) > 20:
        errors.append("Size is required and must be less than 20 characters.")
    if not color or len(color) > 30:
        errors.append("Color is required and must be less than 30 characters.")
    try:
        p = float(price)
        if p < 0:
            errors.append("Price must be a positive number.")
    except ValueError:
        errors.append("Price must be a valid number.")
    try:
        q = int(quantity)
        if q < 0:
            errors.append("Quantity must be a positive number.")
    except ValueError:
        errors.append("Quantity must be a valid number.")
    existing = Product.query.filter_by(product_code=product_code, is_deleted=False).first()
    if existing and (not current_id or existing.id != current_id):
        errors.append("Product code already exists.")
    return errors


@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'Admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('shop'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return redirect(url_for('dashboard' if user and user.role == 'Admin' else 'shop'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            if user.role == 'Admin':
                flash(f'Admin access granted. Welcome, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('shop'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@app.route('/admin/login')
def admin_login():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        otp = request.form.get('otp', '').strip()

        errors = []

        if not otp or len(otp) != 6:
            errors.append("Please enter the 6-digit OTP code.")
        elif session.get('otp_email') != email or session.get('otp_code') != otp:
            errors.append("Invalid or expired OTP. Please verify your email again.")

        if not username or len(username) < 3 or len(username) > 50:
            errors.append("Username must be between 3 and 50 characters.")
        if not email or '@' not in email:
            errors.append("Please provide a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already exists.")

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', form_data=request.form)

        new_user = User(username=username, email=email, role='User')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session.pop('otp_email', None)
        session.pop('otp_code', None)
        session.pop('otp_expires', None)
        session.pop('otp_attempts', None)

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/send-otp', methods=['POST'])
def send_otp():
    import random
    import string

    email = request.form.get('email', '').strip()

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'Invalid email address'}), 400

    otp_code = ''.join(random.choices(string.digits, k=6))
    expiry_time = datetime.now() + timedelta(minutes=10)

    print(f"\n{'=' * 60}")
    print(f"🔐 OTP DEBUG MODE - EMAIL NOT SENT")
    print(f"{'=' * 60}")
    print(f"📧 To: {email}")
    print(f"🔑 OTP Code: {otp_code}")
    print(f"⏰ Expires at: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    session['otp_email'] = email
    session['otp_code'] = otp_code
    session['otp_expires'] = expiry_time.isoformat()
    session['otp_attempts'] = 0
    session.modified = True

    return jsonify({
        'success': True,
        'message': f'DEBUG MODE: Your OTP is {otp_code}. Check the Flask console!',
        'otp': otp_code
    })


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if 'user_id' in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email, is_active=True).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('reset_password', token=token, _external=True)
            flash(f'Password reset link: {reset_url}', 'info')
            flash('Check the message above for your reset link (in production, this will be emailed)', 'success')
        else:
            flash('If that email exists, a reset link has been sent.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if 'user_id' in session:
        return redirect(url_for('login'))

    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        errors = []

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/reset_password.html', token=token, email=email)

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('auth/reset_password.html', token=token, email=email)


# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.filter_by(is_deleted=False).count()
    total_categories = Category.query.filter_by(is_deleted=False).count()
    low_stock = Product.query.filter(Product.is_deleted == False, Product.quantity < 10).count()
    total_value = db.session.query(db.func.sum(Product.price * Product.quantity)).filter_by(is_deleted=False).scalar() or 0
    recent_products = Product.query.filter_by(is_deleted=False).order_by(Product.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', total_products=total_products, total_categories=total_categories,
                         low_stock=low_stock, total_value=total_value, recent_products=recent_products)


# Shop Routes
@app.route('/shop')
@login_required
def shop():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    query = Product.query.filter_by(is_deleted=False)

    if search:
        query = query.filter((Product.product_code.like(f'%{search}%')) | (Product.name.like(f'%{search}%')) |
                           (Product.color.like(f'%{search}%')) | (Product.size.like(f'%{search}%')))
    if category_filter:
        query = query.filter_by(category_id=int(category_filter))

    pagination = query.order_by(Product.name).paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    cart_count = sum(item['quantity'] for item in get_cart().values())
    return render_template('shop/browse.html', products=pagination.items, pagination=pagination,
                         search=search, category_filter=category_filter, categories=categories, cart_count=cart_count)


@app.route('/shop/product/<int:id>')
@login_required
def shop_product_detail(id):
    product = Product.query.get_or_404(id)
    if product.is_deleted:
        flash('Product not found.', 'danger')
        return redirect(url_for('shop'))
    return render_template('shop/product_detail.html', product=product,
                         cart_count=sum(item['quantity'] for item in get_cart().values()))


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.is_deleted:
        return jsonify({'success': False, 'message': 'Product not available'}), 404

    quantity = int(request.form.get('quantity', 1))
    if quantity <= 0 or quantity > product.quantity:
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400

    cart = get_cart()
    item_id = str(product_id)
    if item_id in cart:
        if cart[item_id]['quantity'] + quantity > product.quantity:
            return jsonify({'success': False, 'message': f'Only {product.quantity} items available'}), 400
        cart[item_id]['quantity'] += quantity
    else:
        cart[item_id] = {'product_id': product.id, 'name': product.name, 'price': product.price,
                        'quantity': quantity, 'product_code': product.product_code, 'size': product.size,
                        'color': product.color}

    save_cart(cart)
    flash(f'Added {product.name} to cart!', 'success')
    return jsonify({'success': True, 'cart_count': sum(item['quantity'] for item in cart.values())})


@app.route('/cart')
@login_required
def view_cart():
    cart_items = []
    for item_id, item_data in get_cart().items():
        product = Product.query.get(int(item_id))
        if product and not product.is_deleted:
            cart_items.append({'product': product, 'quantity': item_data['quantity'],
                             'subtotal': item_data['price'] * item_data['quantity']})
    return render_template('shop/cart.html', cart_items=cart_items, total=calculate_cart_total(get_cart()),
                         cart_count=sum(item['quantity'] for item in get_cart().values()))


@app.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    cart = get_cart()
    item_id = str(product_id)
    if item_id not in cart:
        return jsonify({'success': False}), 404

    quantity = int(request.form.get('quantity', 0))
    if quantity <= 0:
        del cart[item_id]
        save_cart(cart)
        return jsonify({'success': True})

    product = Product.query.get(product_id)
    if quantity > product.quantity:
        return jsonify({'success': False, 'message': f'Only {product.quantity} items available'}), 400

    cart[item_id]['quantity'] = quantity
    save_cart(cart)
    return jsonify({'success': True, 'subtotal': cart[item_id]['price'] * quantity,
                   'total': calculate_cart_total(cart), 'cart_count': sum(item['quantity'] for item in cart.values())})


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = get_cart()
    if str(product_id) in cart:
        del cart[str(product_id)]
        save_cart(cart)
        flash('Item removed from cart.', 'info')
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('shop'))

    cart_items = []
    for item_id, item_data in cart.items():
        product = Product.query.get(int(item_id))
        if product and not product.is_deleted:
            cart_items.append({'product': product, 'quantity': item_data['quantity'],
                             'subtotal': item_data['price'] * item_data['quantity']})

    user = User.query.get(session['user_id'])
    customer = Customer.query.filter_by(user_id=user.id, is_deleted=False).first()

    if request.method == 'POST':
        errors = []
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if not first_name or not last_name:
            errors.append('First and last name required.')
        if not email or '@' not in email:
            errors.append('Valid email required.')
        if not phone:
            errors.append('Phone required.')
        if not address:
            errors.append('Address required.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('shop/checkout.html', cart_items=cart_items, total=calculate_cart_total(cart),
                                 cart_count=sum(item['quantity'] for item in cart.values()), form_data=request.form)

        if not customer:
            customer = Customer(first_name=first_name, last_name=last_name, email=email, phone=phone,
                              address=address, user_id=user.id)
            db.session.add(customer)
        else:
            customer.first_name = first_name
            customer.last_name = last_name
            customer.email = email
            customer.phone = phone
            customer.address = address
        db.session.commit()

        order = Order(customer_id=customer.id, total_amount=calculate_cart_total(cart), status='Pending')
        db.session.add(order)
        db.session.flush()

        for item_id, item_data in cart.items():
            product = Product.query.get(int(item_id))
            if product.quantity < item_data['quantity']:
                db.session.rollback()
                flash(f'Insufficient stock for {product.name}', 'danger')
                return redirect(url_for('view_cart'))
            db.session.add(OrderDetail(order_id=order.id, product_id=product.id,
                                      quantity=item_data['quantity'], price=item_data['price']))
            product.quantity -= item_data['quantity']

        db.session.commit()
        session.pop('cart', None)
        flash(f'Order #{order.id} placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))

    return render_template('shop/checkout.html', cart_items=cart_items, total=calculate_cart_total(cart),
                         cart_count=sum(item['quantity'] for item in cart.values()), customer=customer)


@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    if customer.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('shop'))
    return render_template('shop/order_confirmation.html', order=order)


@app.route('/orders')
@login_required
def my_orders():
    customer = Customer.query.filter_by(user_id=session['user_id'], is_deleted=False).first()
    orders = Order.query.filter_by(customer_id=customer.id, is_deleted=False).order_by(
        Order.order_date.desc()).all() if customer else []
    return render_template('shop/orders.html', orders=orders,
                         cart_count=sum(item['quantity'] for item in get_cart().values()))


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    if customer.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_orders'))
    return render_template('shop/order_detail.html', order=order,
                         cart_count=sum(item['quantity'] for item in get_cart().values()))


@app.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    if customer.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_orders'))
    if order.status not in ['Pending', 'Processing']:
        flash('Cannot cancel this order.', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))

    for detail in order.order_details:
        product = Product.query.get(detail.product_id)
        if product:
            product.quantity += detail.quantity
    order.status = 'Cancelled'
    db.session.commit()
    flash(f'Order #{order.id} cancelled successfully.', 'success')
    return redirect(url_for('my_orders'))


@app.route('/categories')
@login_required
def list_categories():
    return render_template('categories/list.html',
                         categories=Category.query.filter_by(is_deleted=False).order_by(Category.name).all())


@app.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        errors = validate_category(name)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categories/create.html', form_data=request.form)
        db.session.add(Category(name=name, description=request.form.get('description', '').strip()))
        db.session.commit()
        flash(f'Category "{name}" created!', 'success')
        return redirect(url_for('list_categories'))
    return render_template('categories/create.html')


@app.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    if category.is_deleted:
        flash('Category not found.', 'danger')
        return redirect(url_for('list_categories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        errors = validate_category(name, id)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categories/edit.html', category=category, form_data=request.form)
        category.name = name
        category.description = request.form.get('description', '').strip()
        db.session.commit()
        flash(f'Category "{name}" updated!', 'success')
        return redirect(url_for('list_categories'))
    return render_template('categories/edit.html', category=category)


@app.route('/categories/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    active_products = Product.query.filter_by(category_id=id, is_deleted=False).count()
    if active_products > 0:
        flash(f'Cannot delete. Category has {active_products} products.', 'danger')
        return redirect(url_for('list_categories'))
    category.is_deleted = True
    db.session.commit()
    flash(f'Category "{category.name}" deleted!', 'success')
    return redirect(url_for('list_categories'))


@app.route('/products')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    query = Product.query.filter_by(is_deleted=False)

    if search:
        query = query.filter((Product.product_code.like(f'%{search}%')) | (Product.name.like(f'%{search}%')) |
                           (Product.color.like(f'%{search}%')) | (Product.size.like(f'%{search}%')))
    if category_filter:
        query = query.filter_by(category_id=int(category_filter))

    pagination = query.order_by(Product.name).paginate(page=page, per_page=10, error_out=False)
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    return render_template('products/list.html', products=pagination.items, pagination=pagination,
                         search=search, category_filter=category_filter, categories=categories)


@app.route('/products/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    if request.method == 'POST':
        product_code = request.form.get('product_code', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', '')
        size = request.form.get('size', '').strip()
        color = request.form.get('color', '').strip()
        price = request.form.get('price', '')
        quantity = request.form.get('quantity', '')

        errors = validate_product(product_code, name, category_id, size, color, price, quantity)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('products/create.html', categories=categories, form_data=request.form)

        new_product = Product(product_code=product_code, name=name, description=description,
                            category_id=int(category_id), size=size, color=color,
                            price=float(price), quantity=int(quantity))
        db.session.add(new_product)
        db.session.commit()
        flash(f'Product "{name}" created!', 'success')
        return redirect(url_for('list_products'))
    return render_template('products/create.html', categories=categories)


@app.route('/products/<int:id>')
@login_required
def view_product(id):
    product = Product.query.get_or_404(id)
    if product.is_deleted:
        flash('Product not found.', 'danger')
        return redirect(url_for('list_products'))
    return render_template('products/view.html', product=product)


@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if product.is_deleted:
        flash('Product not found.', 'danger')
        return redirect(url_for('list_products'))

    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    if request.method == 'POST':
        product_code = request.form.get('product_code', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', '')
        size = request.form.get('size', '').strip()
        color = request.form.get('color', '').strip()
        price = request.form.get('price', '')
        quantity = request.form.get('quantity', '')

        errors = validate_product(product_code, name, category_id, size, color, price, quantity, id)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('products/edit.html', product=product, categories=categories, form_data=request.form)

        product.product_code = product_code
        product.name = name
        product.description = description
        product.category_id = int(category_id)
        product.size = size
        product.color = color
        product.price = float(price)
        product.quantity = int(quantity)
        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Product "{name}" updated!', 'success')
        return redirect(url_for('view_product', id=id))
    return render_template('products/edit.html', product=product, categories=categories)


@app.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.is_deleted = True
    db.session.commit()
    flash(f'Product "{product.name}" deleted!', 'success')
    return redirect(url_for('list_products'))


@app.route('/products/export')
@login_required
def export_products():
    products = Product.query.filter_by(is_deleted=False).order_by(Product.name).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Product Code', 'Name', 'Category', 'Size', 'Color', 'Price', 'Quantity', 'Total Value'])
    for product in products:
        writer.writerow([product.product_code, product.name, product.category.name, product.size, product.color,
                        f'{product.price:.2f}', product.quantity, f'{product.price * product.quantity:.2f}'])
    output.seek(0)
    return send_file(BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True,
                    download_name=f'products_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')


@app.route('/users')
@admin_required
def list_users():
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    return render_template('users/list.html', users=users)


@app.route('/users/<int:id>/toggle_role', methods=['POST'])
@admin_required
def toggle_user_role(id):
    user = User.query.get_or_404(id)
    if user.id == session['user_id']:
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('list_users'))
    user.role = 'User' if user.role == 'Admin' else 'Admin'
    db.session.commit()
    flash(f'User {user.username} role changed to {user.role}.', 'success')
    return redirect(url_for('list_users'))


@app.route('/users/<int:id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(id):
    user = User.query.get_or_404(id)
    if user.id == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('list_users'))
    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} has been deactivated.', 'success')
    return redirect(url_for('list_users'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
