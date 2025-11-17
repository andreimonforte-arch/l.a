import os
from flask import Flask, request, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Replace with your DB URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
def validate_product(product_code, name, category_id, size, color, price, quantity, id=None):
    errors = []
    if not product_code:
        errors.append("Product code is required.")
    return errors

def admin_required(f):
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))  # ADD THIS LINE
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

        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{product_code}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                image_url = f'/static/uploads/products/{unique_filename}'

        errors = validate_product(product_code, name, category_id, size, color, price, quantity)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('products/create.html', categories=categories, form_data=request.form)

        new_product = Product(
            product_code=product_code,
            name=name,
            description=description,
            image_url=image_url,  # ADD THIS LINE
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

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                if product.image_url:
                    old_filepath = os.path.join('static', product.image_url.lstrip('/static/'))
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except:
                            pass

                filename = secure_filename(file.filename)
                unique_filename = f"{product_code}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                product.image_url = f'/static/uploads/products/{unique_filename}'

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

if __name__ == '__main__':
    app.run(debug=True)
