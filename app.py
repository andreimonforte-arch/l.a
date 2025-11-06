from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime
import csv
from io import StringIO, BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Models
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
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


# Authentication Decorators
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
        if not user or user.role != 'admin':
            flash('Admin access required for this action.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# Validation Functions
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            # Redirect admins to admin login
            if user.role == 'admin':
                flash('Please use Admin Login for administrator accounts.', 'warning')
                return redirect(url_for('admin_login'))

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.role == 'admin':
            return redirect(url_for('dashboard'))
        else:
            session.clear()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            if user.role != 'admin':
                flash('Access Denied: Admin privileges required.', 'danger')
                return render_template('auth/admin_login.html')

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Admin access granted. Welcome, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('auth/admin_login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

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

        new_user = User(username=username, email=email, role='user')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


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
        description = request.form.get('description', '').strip()

        errors = validate_category(name)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categories/create.html', form_data=request.form)

        new_category = Category(name=name, description=description)
        db.session.add(new_category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', 'success')
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
        description = request.form.get('description', '').strip()

        errors = validate_category(name, id)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('categories/edit.html', category=category, form_data=request.form)

        category.name = name
        category.description = description
        db.session.commit()

        flash(f'Category "{name}" updated successfully!', 'success')
        return redirect(url_for('list_categories'))

    return render_template('categories/edit.html', category=category)


@app.route('/categories/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)

    active_products = Product.query.filter_by(category_id=id, is_deleted=False).count()
    if active_products > 0:
        flash(f'Cannot delete category. It has {active_products} active product(s).', 'danger')
        return redirect(url_for('list_categories'))

    category.is_deleted = True
    db.session.commit()

    flash(f'Category "{category.name}" deleted successfully!', 'success')
    return redirect(url_for('list_categories'))


@app.route('/products')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    per_page = 10

    query = Product.query.filter_by(is_deleted=False)

    if search:
        query = query.filter(
            (Product.product_code.like(f'%{search}%')) |
            (Product.name.like(f'%{search}%')) |
            (Product.color.like(f'%{search}%')) |
            (Product.size.like(f'%{search}%'))
        )

    if category_filter:
        query = query.filter_by(category_id=int(category_filter))

    query = query.order_by(Product.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.filter_by(is_deleted=False).order_by(Category.name).all()

    return render_template('products/list.html',
                           products=pagination.items,
                           pagination=pagination,
                           search=search,
                           category_filter=category_filter,
                           categories=categories)


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

        new_product = Product(
            product_code=product_code,
            name=name,
            description=description,
            category_id=int(category_id),
            size=size,
            color=color,
            price=float(price),
            quantity=int(quantity)
        )

        db.session.add(new_product)
        db.session.commit()

        flash(f'Product "{name}" created successfully!', 'success')
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

        flash(f'Product "{name}" updated successfully!', 'success')
        return redirect(url_for('view_product', id=id))

    return render_template('products/edit.html', product=product, categories=categories)


@app.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.is_deleted = True
    db.session.commit()

    flash(f'Product "{product.name}" deleted successfully!', 'success')
    return redirect(url_for('list_products'))


@app.route('/products/export')
@login_required
def export_products():
    products = Product.query.filter_by(is_deleted=False).order_by(Product.name).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Product Code', 'Name', 'Category', 'Size', 'Color', 'Price', 'Quantity', 'Total Value'])

    for product in products:
        writer.writerow([
            product.product_code,
            product.name,
            product.category.name,
            product.size,
            product.color,
            f'{product.price:.2f}',
            product.quantity,
            f'{product.price * product.quantity:.2f}'
        ])

    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'products_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@app.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.filter_by(is_deleted=False).count()
    total_categories = Category.query.filter_by(is_deleted=False).count()
    low_stock = Product.query.filter(Product.is_deleted == False, Product.quantity < 10).count()
    total_value = db.session.query(db.func.sum(Product.price * Product.quantity)).filter_by(
        is_deleted=False).scalar() or 0

    recent_products = Product.query.filter_by(is_deleted=False).order_by(Product.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_products=total_products,
                           total_categories=total_categories,
                           low_stock=low_stock,
                           total_value=total_value,
                           recent_products=recent_products)


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

    user.role = 'user' if user.role == 'admin' else 'admin'
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
    app.run(debug=True)
