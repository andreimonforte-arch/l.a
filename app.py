import base64
import csv
import hashlib
import hmac
import os
import uuid
import random
import smtplib
import string
from datetime import datetime
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from io import StringIO, BytesIO
from typing import Callable

from jinja2 import TemplateNotFound

from admin_login import app
from flask import send_from_directory

import dotenv
import requests
import sqlalchemy.orm.attributes
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

dotenv.load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'images', 'products')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

VALID_SIZES = {
    'XS', 'S', 'M', 'L', 'XL', '2XL',
    '28', '30', '32', '34', '36', '38', '40',
    'OS'
}


def get_image_mimetype(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    mime_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
                  '.webp': 'image/webp'}
    return mime_types.get(ext, 'image/jpeg')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    size_quantities = db.Column(db.JSON, nullable=False, default=dict)
    color = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    @property
    def total_quantity(self):
        return sum(self.size_quantities.values()) if self.size_quantities else 0


class Size(db.Model):
    __tablename__ = 'size'

    id = db.Column(db.Integer, primary_key=True)
    size_value = db.Column(db.String(20), nullable=False)
    size_type = db.Column(db.String(20), nullable=False)  # 'shirt' or 'pant'


    product_sizes = db.relationship('ProductSize', backref='size', lazy=True)


    __table_args__ = (db.UniqueConstraint('size_value', 'size_type', name='unique_size_type'),)


class ProductSize(db.Model):
    __tablename__ = 'product_size'

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    size_id = db.Column(db.Integer, db.ForeignKey('size.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    orders = db.relationship('Order', backref='customer', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending', index=True)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), nullable=False, default='Unpaid', index=True)
    payment_reference = db.Column(db.String(255), index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    order_details = db.relationship('OrderDetail', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderDetail(db.Model):
    __tablename__ = 'order_details'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    size = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_details', lazy=True)


def login_required(f: Callable) -> Callable:
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
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash('Admin access required for this action.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


def get_cart():
    return session.get('cart', {})


def save_cart(cart):
    session['cart'] = cart
    session.modified = True


def calculate_cart_total(cart):
    total = 0
    for item_data in cart.values():
        total += item_data.get('price', 0) * item_data.get('quantity', 0)
    return round(total, 2)


def extract_size_quantities_from_form(form):
    size_quantities = {}
    for size in VALID_SIZES:
        qty_field = f'size_{size}'
        if qty_field in form:
            qty_str = form[qty_field].strip()
            if qty_str:
                try:
                    qty = int(qty_str)
                    if qty > 0:
                        size_quantities[size] = qty
                except ValueError:
                    pass
    return size_quantities


def validate_category(name, current_id=None):
    errors = []
    name = name.strip()
    if not name or len(name) < 2 or len(name) > 50:
        errors.append("Category name must be between 2 and 50 characters.")
    existing = Category.query.filter(Category.name.ilike(name), Category.is_deleted == False).first()
    if existing and (not current_id or existing.id != current_id):
        errors.append("Category name already exists.")
    return errors


def validate_product(product_code, name, category_id, color, price, size_quantities, current_id=None):
    errors = []
    product_code = product_code.strip()
    if not product_code or len(product_code) < 3 or len(product_code) > 50:
        errors.append("Product code must be between 3 and 50 characters.")
    existing = Product.query.filter(Product.product_code.ilike(product_code), Product.is_deleted == False).first()
    if existing and (not current_id or existing.id != current_id):
        errors.append("Product code already exists.")

    name = name.strip()
    if not name or len(name) < 2 or len(name) > 200:
        errors.append("Product name must be between 2 and 200 characters.")

    try:
        cat_id = int(category_id)
        category = Category.query.filter_by(id=cat_id, is_deleted=False).first()
        if not category:
            errors.append("Selected category does not exist.")
    except (ValueError, TypeError):
        errors.append("Invalid category selected.")

    color = color.strip()
    if not color or len(color) > 50:
        errors.append("Color is required and must be less than 50 characters.")

    try:
        price_val = float(price)
        if price_val < 0 or price_val > 999999.99:
            errors.append("Price must be between 0 and 999,999.99.")
    except (ValueError, TypeError):
        errors.append("Price must be a valid number.")

    # Fixed size_quantities validation
    if size_quantities is None or not isinstance(size_quantities, dict):
        errors.append("Size quantities must be provided.")
    else:
        total_qty = 0
        has_valid_quantity = False
        for size, qty in size_quantities.items():
            if size not in VALID_SIZES:
                errors.append(f"Invalid size: {size}. Valid sizes are: {', '.join(VALID_SIZES)}")
                continue
            try:
                qty_val = int(qty)
                if qty_val < 0:
                    errors.append(f"Quantity for {size} cannot be negative.")
                else:
                    total_qty += qty_val
                    if qty_val > 0:
                        has_valid_quantity = True
            except (ValueError, TypeError):
                errors.append(f"Quantity for {size} must be a valid integer.")

        if not has_valid_quantity and not errors:
            errors.append("At least one size quantity must be greater than 0.")

        if total_qty > 999999:
            errors.append("Total quantity must not exceed 999,999.")

    return errors




def save_product_image(image_file, product_code):
    if not image_file or not image_file.filename:
        return None

    ext = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else 'jpg'
    filename = f"{product_code.replace(' ', '_')}_{int(time.time())}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image_file.save(filepath)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filename
        os.remove(filepath)
        return None
    except Exception as e:
        app.logger.error(f"Image save error: {e}")
        return None


@app.context_processor
def inject_cart_count():
    cart = get_cart()
    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    return dict(cart_count=cart_count, valid_sizes=VALID_SIZES)


@app.context_processor
def inject_category_icon():
    def get_category_icon(category_name):
        icons = {
            'Shirts': '<svg class="icon" viewBox="0 0 24 24"><path d="M16 3h5v5M8 3H3v5M21 8l-3 3-2-2M6 8L3 11l2 2M12 6v12M6 18h12"/></svg>',
            'Pants': '<svg class="icon" viewBox="0 0 24 24"><path d="M12 2v20M8 2h8M6 22l2-10M18 22l-2-10M4 8h16"/></svg>',
            'Shoes': '<svg class="icon" viewBox="0 0 24 24"><path d="M2 18c0-2 4-4 4-6V8c0-1 1-2 2-2h8c1 0 2 1 2 2v4c0 2 4 4 4 6M6 18h12c1 0 2 1 2 2v2H4v-2c0-1 1-2 2-2z"/></svg>',
            'Accessories': '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
        }
        return icons.get(category_name,
                         '<svg class="icon" viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L3 14.59V3h11.59l7.17 7.17a2 2 0 0 1 0 2.83z"/></svg>')

    return dict(get_category_icon=get_category_icon)


@app.context_processor
def utility_processor():
    def get_product_image_url(product):
        """Get the URL for a product image, with fallback"""
        if product.image_filename:
            image_path = os.path.join(app.static_folder, 'uploads', 'products', product.image_filename)
            if os.path.exists(image_path):
                return url_for('static', filename=f'uploads/products/{product.image_filename}')
        return url_for('static', filename='images/placeholder.jpg')

    return dict(get_product_image_url=get_product_image_url)


def send_email(to_email, subject, html_body):
    try:
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', 587))
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_username)

        if not mail_username or not mail_password:
            raise Exception("Email configuration missing. Set MAIL_USERNAME and MAIL_PASSWORD in .env")

        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = mail_sender
        message['To'] = to_email
        message.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(message)
        return True
    except Exception as e:
        app.logger.error(f"Email error: {e}")
        return False


@app.route('/')
def index():
    if 'user_id' in session:
        user = get_current_user()
        return redirect(url_for('dashboard' if user and user.role == 'Admin' else 'shop'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = get_current_user()
        return redirect(url_for('dashboard' if user.role == 'Admin' else 'shop'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')


        user = User.query.filter_by(username=username).first()

        # Always check password to prevent timing attacks
        if user:
            password_valid = user.check_password(password)
        else:
            # Run a dummy hash check to maintain consistent timing
            from werkzeug.security import check_password_hash
            check_password_hash('dummy_hash', password)
            password_valid = False

        # Check all conditions
        if user and password_valid and user.is_active:
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash_message = f'Admin access granted. Welcome, {user.username}!' if user.role == 'Admin' else f'Welcome back, {user.username}!'
            flash(flash_message, 'success')
            return redirect(url_for('dashboard' if user.role == 'Admin' else 'shop'))
        elif user and password_valid and not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
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

        otp_expires = session.get('otp_expires')
        if otp_expires and datetime.fromisoformat(otp_expires) < datetime.now():
            errors.append("OTP has expired. Please request a new one.")

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
    email = request.form.get('email', '').strip()
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'Invalid email address'}), 400

    otp_attempts = session.get('otp_attempts', 0)
    if otp_attempts >= 5:
        return jsonify({'success': False, 'message': 'Too many OTP requests. Try again later.'}), 429

    otp_code = ''.join(random.choices(string.digits, k=6))
    expiry_time = datetime.now() + timedelta(minutes=10)
    session['otp_email'] = email
    session['otp_code'] = otp_code
    session['otp_expires'] = expiry_time.isoformat()
    session['otp_attempts'] = otp_attempts + 1
    session.modified = True

    if os.getenv('OTP_DEBUG_MODE', 'False').lower() == 'true':
        app.logger.info(f"OTP DEBUG for {email}: {otp_code}")
        return jsonify({'success': True, 'message': f'DEBUG MODE: OTP is {otp_code}', 'debug': True})

    html_body = f"""
    <!DOCTYPE html><html><head><style>
    body{{font-family:Arial,sans-serif;padding:20px}}.otp{{background:#667eea;color:white;padding:20px;font-size:32px;text-align:center;letter-spacing:5px;border-radius:10px;margin:20px 0}}
    </style></head><body>
    <h2>Email Verification</h2>
    <p>Your OTP Code:</p>
    <div class="otp">{otp_code}</div>
    <p><strong>Expires in 10 minutes</strong></p>
    </body></html>
    """

    if send_email(email, 'Your OTP Code - Ma Locozz Clothing Store', html_body):
        return jsonify({'success': True, 'message': 'OTP sent to your email.'})
    else:
        return jsonify({'success': True, 'message': f'Email failed. DEBUG OTP: {otp_code}', 'debug': True,
                        'error': 'Email config error'})


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
            token = URLSafeTimedSerializer(app.config['SECRET_KEY']).dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            html_body = f"""
            <h2>Password Reset</h2>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_url}" style="background:#667eea;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Reset Password</a>
            <p><strong>This link expires in 1 hour.</strong></p>
            """
            send_email(email, 'Password Reset - Ma Locozz Clothing Store', html_body)
            flash('If that email exists, a reset link has been sent.', 'success')
        else:
            flash('If that email exists, a reset link has been sent.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if 'user_id' in session:
        return redirect(url_for('login'))

    try:
        email = URLSafeTimedSerializer(app.config['SECRET_KEY']).loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(password)
                db.session.commit()
                flash('Your password has been reset successfully! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('User not found.', 'danger')

    return render_template('auth/reset_password.html', token=token, email=email)


from datetime import datetime


@app.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.filter_by(is_deleted=False).count()
    total_categories = Category.query.filter_by(is_deleted=False).count()
    all_products = Product.query.filter_by(is_deleted=False).all()
    low_stock_count = sum(1 for p in all_products if p.total_quantity < 10)
    total_value = sum(p.price * p.total_quantity for p in all_products)
    recent_products = Product.query.filter_by(is_deleted=False).order_by(Product.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_products=total_products,
                           total_categories=total_categories,
                           low_stock=low_stock_count,
                           total_value=total_value,
                           recent_products=recent_products,
                           config=app.config,
                           now=datetime.now())


@app.route('/shop')
@login_required
def shop():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    query = Product.query.filter_by(is_deleted=False)
    if search:
        query = query.filter((Product.product_code.ilike(f'%{search}%')) | (Product.name.ilike(f'%{search}%')) |
                             (Product.color.ilike(f'%{search}%')))
    if category_filter:
        try:
            query = query.filter_by(category_id=int(category_filter))
        except ValueError:
            pass
    pagination = query.order_by(Product.name).paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    return render_template('shop/browse.html', products=pagination.items, pagination=pagination,
                           search=search, category_filter=category_filter, categories=categories)


@app.route('/shop/product/<int:id>')
@login_required
def shop_product_detail(id):
    product = db.session.get(Product, id)
    if not product or product.is_deleted:
        flash('Product not found.', 'danger')
        return redirect(url_for('shop'))
    return render_template('shop/product_detail.html', product=product, valid_sizes=VALID_SIZES)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product or product.is_deleted:
        flash('Product not available', 'danger')
        return redirect(url_for('shop'))

    size = request.form.get('size', '').strip().upper()
    if not size or size not in VALID_SIZES:
        flash('Please select a valid size', 'warning')
        return redirect(request.referrer or url_for('shop'))

    current_qty = product.size_quantities.get(size, 0) if product.size_quantities else 0

    try:
        requested_quantity = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Invalid quantity', 'danger')
        return redirect(request.referrer or url_for('shop'))

    if requested_quantity <= 0 or requested_quantity > current_qty:
        flash(f'Only {current_qty} available in size {size}', 'warning')
        return redirect(request.referrer or url_for('shop'))

    cart = get_cart()
    item_key = f"{product_id}_{size}"

    if item_key in cart:
        if cart[item_key]['quantity'] + requested_quantity > current_qty:
            flash(f'Only {current_qty} available in size {size}', 'warning')
            return redirect(request.referrer or url_for('shop'))
        cart[item_key]['quantity'] += requested_quantity
    else:
        cart[item_key] = {
            'product_id': product.id,
            'name': product.name,
            'price': float(product.price),
            'quantity': requested_quantity,
            'product_code': product.product_code,
            'size': size,
            'color': product.color
        }

    save_cart(cart)
    flash(f'Added {product.name} (Size: {size}) to cart!', 'success')

    return redirect(request.referrer or url_for('view_cart'))


@app.route('/cart')
@login_required
def view_cart():
    cart_items = []
    cart = get_cart()

    validation_errors = []
    for item_key, item_data in list(cart.items()):
        product = db.session.get(Product, item_data.get('product_id'))
        size = item_data.get('size')

        if not product or product.is_deleted or not size:
            del cart[item_key]
            continue

        available_qty = product.size_quantities.get(size, 0)
        if item_data['quantity'] > available_qty:
            validation_errors.append(f"{product.name} (Size: {size}) quantity reduced to {available_qty}")
            item_data['quantity'] = available_qty

    if validation_errors:
        flash(", ".join(validation_errors), 'warning')
        save_cart(cart)

    for item_key, item_data in cart.items():
        product = db.session.get(Product, item_data['product_id'])
        if product and not product.is_deleted:
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'size': item_data['size'],
                'subtotal': item_data['price'] * item_data['quantity']
            })

    return render_template('shop/cart.html', cart_items=cart_items, total=calculate_cart_total(cart))


@app.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    size = request.form.get('size', '').strip()
    item_key = f"{product_id}_{size}"
    cart = get_cart()

    if item_key not in cart:
        return jsonify({'success': False}), 404

    try:
        quantity = int(request.form.get('quantity', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400

    if quantity <= 0:
        del cart[item_key]
        save_cart(cart)
        return jsonify({'success': True})

    product = db.session.get(Product, product_id)
    available_qty = product.size_quantities.get(size, 0) if product else 0

    if quantity > available_qty:
        return jsonify({'success': False, 'message': f'Only {available_qty} available'}), 400

    cart[item_key]['quantity'] = quantity
    save_cart(cart)
    return jsonify({
        'success': True,
        'subtotal': cart[item_key]['price'] * quantity,
        'total': calculate_cart_total(cart),
        'cart_count': sum(item.get('quantity', 0) for item in cart.values())
    })


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    size = request.form.get('size', '').strip()
    if not size:
        flash('Size is required', 'error')
        return redirect(url_for('view_cart'))

    cart = get_cart()
    item_key = f"{product_id}_{size}"

    if item_key in cart:
        del cart[item_key]
        save_cart(cart)
        flash('Item removed from cart', 'success')
    else:
        flash('Item not found in cart', 'error')

    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('shop'))

    user = get_current_user()
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
            return render_template('shop/checkout.html', form_data=request.form, customer=customer)


        try:
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

            total_amount = calculate_cart_total(cart)
            order = Order(
                customer_id=customer.id,
                total_amount=total_amount,
                status='Pending',
                payment_status='Unpaid'
            )
            db.session.add(order)
            db.session.flush()

            # Process order details and update inventory
            for item_key, item_data in cart.items():
                product = db.session.get(Product, item_data['product_id'])
                size = item_data.get('size')
                quantity = item_data['quantity']

                if not product or not size or size not in product.size_quantities:
                    raise ValueError(f"Invalid product or size: {item_key}")

                available_qty = product.size_quantities[size]
                if available_qty < quantity:
                    raise ValueError(f"Insufficient stock for {product.name} (Size: {size})")


                db.session.add(OrderDetail(
                    order_id=order.id,
                    product_id=product.id,
                    size=size,
                    quantity=quantity,
                    price=item_data['price']
                ))

                # Update inventory
                product.size_quantities[size] -= quantity
                sqlalchemy.orm.attributes.flag_modified(product, 'size_quantities')

            db.session.commit()
            session['pending_order_id'] = order.id
            return redirect(url_for('select_payment_method', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            flash(str(e), 'danger')
            return redirect(url_for('view_cart'))

    # Prepare cart items for display
    cart_items = []
    for item_key, item_data in cart.items():
        product = db.session.get(Product, item_data['product_id'])
        size = item_data.get('size')
        if product and not product.is_deleted and size:
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'size': size,
                'subtotal': item_data['price'] * item_data['quantity']
            })

    return render_template('shop/checkout.html', cart_items=cart_items, total=calculate_cart_total(cart),
                           customer=customer)


@app.route('/payment/select/<int:order_id>')
@login_required
def select_payment_method(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('shop'))

    customer = db.session.get(Customer, order.customer_id)
    user = get_current_user()

    if customer.user_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('shop'))

    if order.payment_status == 'Paid':
        flash('This order has already been paid.', 'info')
        return redirect(url_for('order_confirmation', order_id=order.id))

    return render_template('shop/payment_select.html', order=order)


@app.route('/payment/process/<int:order_id>', methods=['POST'])
@login_required
def process_payment(order_id):
    payment_method = request.form.get('payment_method')
    order = db.session.get(Order, order_id)

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('shop'))

    customer = db.session.get(Customer, order.customer_id)
    user = get_current_user()

    if customer.user_id != user.id:
        flash('Unauthorized access to order.', 'danger')
        return redirect(url_for('shop'))

    # Validate payment method - includes Maya (new PayMaya brand) and PayMaya for backward compatibility
    valid_methods = ['credit_card', 'gcash', 'maya', 'paymaya', 'bank_transfer', 'cash', 'cod', 'debit']
    if payment_method not in valid_methods:
        flash('Invalid payment method.', 'danger')
        return redirect(url_for('select_payment_method', order_id=order.id))

    order.payment_method = payment_method

    # Route based on payment method type
    # E-wallet APIs: GCash, Maya/PayMaya require external payment API processing
    if payment_method in ['gcash', 'maya', 'paymaya']:
        return redirect(url_for('create_payment_api', order_id=order.id, payment_method=payment_method))

    # Traditional methods: Set as pending for manual processing/verification
    # Includes COD, debit cards, credit cards, bank transfers, and cash
    elif payment_method in ['credit_card', 'bank_transfer', 'cash', 'cod', 'debit']:
        order.payment_status = 'Pending'
        db.session.commit()
        return redirect(url_for('order_confirmation', order_id=order.id))

    else:
        flash('Invalid payment method.', 'danger')
        return redirect(url_for('select_payment_method', order_id=order.id))


@app.route('/payment/create/<int:order_id>/<payment_method>', methods=['GET'])
@login_required
def create_payment_api(order_id, payment_method):
    order = db.session.get(Order, order_id)

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('shop'))

    customer = db.session.get(Customer, order.customer_id)
    user = get_current_user()

    if customer.user_id != user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('shop'))

    # For now, simulate payment processing
    # In production, integrate with actual GCash/PayMaya API

    if payment_method in ['gcash', 'paymaya']:
        # Set order as paid (or pending payment confirmation)
        order.payment_status = 'Pending'
        db.session.commit()

        flash(f'Payment via {payment_method.title()} initiated successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    else:
        flash('Invalid payment method.', 'danger')
        return redirect(url_for('select_payment_method', order_id=order.id))


@app.route('/payment/success')
@login_required
def payment_success():
    order_id = request.args.get('order_id')
    if order_id:
        order = db.session.get(Order, order_id)
        if order:
            customer = db.session.get(Customer, order.customer_id)
            user = get_current_user()
            if customer.user_id == user.id:
                order.payment_status = 'Paid'
                order.status = 'Processing'
                db.session.commit()
                session.pop('cart', None)
                session.pop('pending_order_id', None)
                flash(f'Payment successful! Order #{order.id} is being processed.', 'success')
                return redirect(url_for('order_confirmation', order_id=order.id))

    flash('Payment completed successfully!', 'success')
    return redirect(url_for('my_orders'))


@app.route('/payment/failed')
@login_required
def payment_failed():
    order_id = request.args.get('order_id')
    if order_id:
        order = db.session.get(Order, order_id)
        if order:
            customer = db.session.get(Customer, order.customer_id)
            user = get_current_user()
            if customer.user_id == user.id:
                order.payment_status = 'Failed'
                db.session.commit()
    flash('Payment failed. Please try again.', 'danger')
    return redirect(url_for('select_payment_method', order_id=order_id) if order_id else url_for('my_orders'))


@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    try:
        order = db.session.get(Order, order_id)
        if not order:
            flash('Order not found.', 'danger')
            return redirect(url_for('shop'))

        # Verify the order belongs to the current user
        if order.user_id != session.get('user_id'):
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('my_orders'))

        # Debug: Print order details
        print(f"Order ID: {order.id}")
        print(f"Order Details Count: {len(order.order_details)}")
        print(f"Template path: shop/order_confirmation.html")

        # Clear cart
        session.pop('cart', None)
        session.pop('pending_order_id', None)

        # Try to render template
        try:
            return render_template('shop/order_confirmation.html', order=order)
        except TemplateNotFound as e:
            print(f"Template not found: {e}")
            flash('Template not found. Please contact support.', 'danger')
            return redirect(url_for('my_orders'))
        except Exception as template_error:
            print(f"Template rendering error: {template_error}")
            import traceback
            traceback.print_exc()
            flash(f'Template error: {str(template_error)}', 'danger')
            return redirect(url_for('my_orders'))

    except Exception as e:
        print(f"ERROR in order_confirmation: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred loading the confirmation page.', 'danger')
        return redirect(url_for('my_orders'))

@app.route('/orders')
@login_required
def my_orders():
    user = get_current_user()
    customer = Customer.query.filter_by(user_id=user.id, is_deleted=False).first()
    if not customer:
        flash('No customer profile found.', 'warning')
        return redirect(url_for('shop'))

    orders = Order.query.filter_by(customer_id=customer.id, is_deleted=False).order_by(
        Order.order_date.desc()).all()
    return render_template('shop/orders.html', orders=orders)


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('my_orders'))

    customer = db.session.get(Customer, order.customer_id)
    user = get_current_user()

    if customer.user_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_orders'))

    return render_template('shop/order_detail.html', order=order)


@app.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('my_orders'))

    customer = db.session.get(Customer, order.customer_id)
    user = get_current_user()

    if customer.user_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_orders'))

    if order.status not in ['Pending', 'Processing']:
        flash('Cannot cancel this order.', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))

    try:
        # Restore inventory
        for detail in order.order_details:
            product = db.session.get(Product, detail.product_id)
            if product and detail.size in product.size_quantities:
                product.size_quantities[detail.size] += detail.quantity
                sqlalchemy.orm.attributes.flag_modified(product, 'size_quantities')

        order.status = 'Cancelled'
        db.session.commit()
        flash(f'Order #{order.id} cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling order.', 'danger')

    return redirect(url_for('my_orders'))


@app.route('/categories')
@login_required
def list_categories():
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    return render_template('categories/list.html', categories=categories)


@app.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        errors = validate_category(name)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categories/create_product.html', form_data=request.form)

        category = Category(name=name, description=request.form.get('description', '').strip())
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{name}" created!', 'success')
        return redirect(url_for('list_categories'))
    return render_template('categories/create_product.html')


@app.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(id):
    category = db.session.get(Category, id)
    if not category or category.is_deleted:
        flash('Category not found.', 'danger')
        return redirect(url_for('list_categories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        errors = validate_category(name, id)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categories/edit_product.html', category=category, form_data=request.form)

        category.name = name
        category.description = request.form.get('description', '').strip()
        db.session.commit()
        flash(f'Category "{name}" updated!', 'success')
        return redirect(url_for('list_categories'))

    return render_template('categories/edit_product.html', category=category)


@app.route('/categories/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    category = db.session.get(Category, id)
    if not category or category.is_deleted:
        flash('Category not found.', 'danger')
        return redirect(url_for('list_categories'))

    active_products = Product.query.filter_by(category_id=id, is_deleted=False).count()
    if active_products > 0:
        flash(f'Cannot delete. Category has {active_products} products.', 'danger')
        return redirect(url_for('list_categories'))

    category.is_deleted = True
    db.session.commit()
    flash(f'Category "{category.name}" deleted!', 'success')
    return redirect(url_for('list_categories'))


@app.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def delete_product(id):
    product = db.session.get(Product, id)
    if not product or product.is_deleted:
        flash('Product not found.', 'danger')
        return redirect(url_for('list_products'))

    product.is_deleted = True
    db.session.commit()
    flash(f'Product "{product.name}" deleted successfully!', 'success')
    return redirect(url_for('list_products'))

@app.route('/products/<int:id>')
def view_product(id):
    product = Product.query.filter_by(id=id, is_deleted=False).first_or_404()
    return render_template('products/view.html', product=product)
@app.route('/products')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    query = Product.query.filter_by(is_deleted=False)
    if search:
        query = query.filter((Product.product_code.ilike(f'%{search}%')) | (Product.name.ilike(f'%{search}%')) |
                             (Product.color.ilike(f'%{search}%')))
    if category_filter:
        try:
            query = query.filter_by(category_id=int(category_filter))
        except ValueError:
            pass
    pagination = query.order_by(Product.name).paginate(page=page, per_page=10, error_out=False)
    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()
    return render_template('products/list.html', products=pagination.items, pagination=pagination,
                           search=search, category_filter=category_filter, categories=categories)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/products/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    if request.method == 'POST':
        # Get form data
        product_code = request.form.get('product_code', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', '')
        color = request.form.get('color', '').strip()
        price = request.form.get('price', '')

        # Get size quantities - Store as JSON
        size_quantities = {}
        has_any_quantity = False

        for key, value in request.form.items():
            if key.startswith('shirt_sizes[') or key.startswith('pant_sizes['):
                # Extract size type and value
                if key.startswith('shirt_sizes['):
                    size_type = 'shirt'
                    size_value = key.split('[')[1].split(']')[0]
                else:
                    size_type = 'pant'
                    size_value = key.split('[')[1].split(']')[0]

                quantity = int(value) if value.isdigit() else 0
                if quantity > 0:
                    size_quantities[f"{size_type}_{size_value}"] = quantity
                    has_any_quantity = True

        # Validation errors list
        errors = []

        # Basic field validation
        if not product_code:
            errors.append("Product Code is required")
        elif Product.query.filter_by(product_code=product_code, is_deleted=False).first():
            errors.append("Product Code already exists")

        if not name:
            errors.append("Product Name is required")

        if not category_id:
            errors.append("Category is required")
        else:
            try:
                cat_id = int(category_id)
                if not Category.query.filter_by(id=cat_id, is_deleted=False).first():
                    errors.append("Valid Category is required")
            except (ValueError, TypeError):
                errors.append("Valid Category is required")

        if not color:
            errors.append("Color is required")

        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append("Price must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Valid Price is required")

        # Size quantities validation
        if not has_any_quantity:
            errors.append("At least one size quantity must be greater than 0")

        # Image validation
        image_file = request.files.get('product_image')
        image_filename = None
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                errors.append("Invalid image file type")
            else:
                # Save image
                ext = image_file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # If validation errors, render form again with errors
        if errors:
            categories = Category.query.filter_by(is_deleted=False).all()
            return render_template('products/create_product.html',
                                   categories=categories,
                                   errors=errors,
                                   form_data=request.form)

        # Create product with size_quantities as JSON
        product = Product(
            product_code=product_code,
            name=name,
            description=description,
            category_id=int(category_id),
            color=color,
            price=float(price),
            image_filename=image_filename,
            size_quantities=size_quantities  # Store as JSON
        )

        db.session.add(product)
        db.session.commit()

        flash('Product created successfully!', 'success')
        return redirect(url_for('list_products'))

    # GET request
    categories = Category.query.filter_by(is_deleted=False).all()
    return render_template('products/create_product.html', categories=categories)

@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Handle form submission
            product.product_code = request.form.get('product_code')
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.category_id = request.form.get('category_id')
            product.color = request.form.get('color')
            product.price = float(request.form.get('price', 0))

            # Collect all size quantities
            size_quantities = {}
            all_sizes = ['XS', 'S', 'M', 'L', 'XL', '2XL', '28', '30', '32', '34', '36', '38', '40', 'OS']

            for size in all_sizes:
                quantity = request.form.get(f'size_{size}', 0)
                try:
                    qty = int(quantity) if quantity else 0
                    if qty > 0:
                        size_quantities[size] = qty
                except (ValueError, TypeError):
                    pass

            product.size_quantities = size_quantities

            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    from werkzeug.utils import secure_filename
                    import os
                    import time

                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"

                    upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'products')
                    os.makedirs(upload_folder, exist_ok=True)

                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)

                    product.image_filename = filename

            product.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('view_product', id=product.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
            print(f"Error in edit_product: {e}")

    # GET request - show form
    categories = Category.query.all()

    # Change this line to look in products folder:
    return render_template('products/edit_product.html', product=product, categories=categories)


@app.route('/products/export')
@login_required
def export_products():
    products = Product.query.filter_by(is_deleted=False).order_by(Product.name).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Product Code', 'Name', 'Category', 'Color', 'Price', 'Size Breakdown',
                     'Total Quantity', 'Total Value'])
    for product in products:
        size_breakdown = str(product.size_quantities) if product.size_quantities else 'N/A'
        total_qty = product.total_quantity
        writer.writerow([product.product_code, product.name, product.category.name, product.color,
                         f'{product.price:.2f}', size_breakdown, total_qty,
                         f'{product.price * total_qty:.2f}'])
    output.seek(0)
    return send_file(BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True,
                     download_name=f'products_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')


from flask import send_from_directory
import os


@app.route('/product-image/<int:id>')
def product_image(id):
    """Serve product images with fallback"""
    product = Product.query.get_or_404(id)

    if product.image_filename:
        image_path = os.path.join(app.root_path, 'static', 'uploads', 'products', product.image_filename)
        if os.path.exists(image_path):
            return send_from_directory(
                os.path.join(app.root_path, 'static', 'uploads', 'products'),
                product.image_filename
            )

    # Return placeholder if image doesn't exist
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),'placeholder.jpg')


@app.route('/users')
@admin_required
def list_users():
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    return render_template('users/list.html', users=users)


@app.route('/users/<int:id>/toggle_role', methods=['POST'])
@admin_required
def toggle_user_role(id):
    user = db.session.get(User, id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('list_users'))

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
    user = db.session.get(User, id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('list_users'))

    if user.id == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('list_users'))

    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} has been deactivated.', 'success')
    return redirect(url_for('list_users'))


@app.route('/test-email')
def test_email():
    try:
        mail_username = os.getenv('MAIL_USERNAME')
        if not mail_username:
            return '<h1>❌ Email Configuration Missing</h1><p>Set MAIL_USERNAME in .env</p>', 400

        html_body = f"""
        <!DOCTYPE html><html><head><style>
        body{{font-family:Arial,sans-serif;padding:20px}}.success{{background:#d4edda;border:2px solid #28a745;padding:30px;border-radius:10px}}
        </style></head><body>
        <div class="success">
        <h1>✅ Email Test Successful!</h1>
        <p>Check your inbox at: {mail_username}</p>
        </div></body></html>
        """

        if send_email(mail_username, 'Test Email - Ma Locozz Clothing Store', html_body):
            return f'''
            <!DOCTYPE html><html><body>
            <h1>✅ Email Test Initiated!</h1>
            <p>Check your inbox at: {mail_username}</p>
            </body></html>
            '''
        else:
            raise Exception("Failed to send email")
    except Exception as e:
        return f'<h1>❌ Email Test Failed</h1><p>Error: {str(e)}</p>', 500


if __name__ == '__main__':
    app.run(debug=True)
