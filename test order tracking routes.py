
from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))

    def __repr__(self):
        return f'<User {self.username}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<Product {self.name}>'


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Processing')
    payment_method = db.Column(db.String(50), default='Cash on Delivery')

    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    shipping_cost = db.Column(db.Float, default=100.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    shipping_address_line1 = db.Column(db.String(200))
    shipping_address_line2 = db.Column(db.String(200))
    shipping_city = db.Column(db.String(100))
    shipping_state = db.Column(db.String(100))
    shipping_postal_code = db.Column(db.String(20))
    shipping_country = db.Column(db.String(100), default='Philippines')
    shipping_phone = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processing_date = db.Column(db.DateTime)
    shipped_date = db.Column(db.DateTime)
    delivered_date = db.Column(db.DateTime)

    user = db.relationship('User', backref='orders')

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    product_name = db.Column(db.String(200), nullable=False)
    size = db.Column(db.String(10))
    color = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    order = db.relationship('Order', backref='items')
    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.product_name} x{self.quantity}>'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def create_order(user_id, cart_items, shipping_info, payment_method='Cash on Delivery'):
    try:
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        shipping = 100.00
        tax = subtotal * 0.12
        total = subtotal + shipping + tax

        order = Order(
            user_id=user_id,
            order_number=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status='Processing',
            payment_method=payment_method,
            subtotal=subtotal,
            shipping_cost=shipping,
            tax=tax,
            total=total,
            shipping_address_line1=shipping_info.get('address_line1'),
            shipping_address_line2=shipping_info.get('address_line2'),
            shipping_city=shipping_info.get('city'),
            shipping_state=shipping_info.get('state'),
            shipping_postal_code=shipping_info.get('postal_code'),
            shipping_country=shipping_info.get('country', 'Philippines'),
            shipping_phone=shipping_info.get('phone')
        )

        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                product_name=item['name'],
                size=item.get('size'),
                color=item.get('color'),
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)

        db.session.commit()
        return order

    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {e}")
        return None


@app.route('/')
def index():
    return '<h1>Ma Locozz Clothing Store</h1><a href="/test-setup">Click here to setup test data</a>'


@app.route('/orders/')
@login_required
def orders_list():
    current_user = get_current_user()
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('shop/my_orders.html', orders=orders)


@app.route('/orders/<int:order_id>')
@login_required
def track_order(order_id):
    current_user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('orders_list'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    timeline = []
    if order.status == 'Processing':
        timeline = [
            {'status': 'Order Placed', 'date': order.created_at, 'completed': True},
            {'status': 'Processing', 'date': None, 'completed': True},
            {'status': 'Shipped', 'date': None, 'completed': False},
            {'status': 'Delivered', 'date': None, 'completed': False}
        ]

    return render_template('shop/track_order.html', order=order, order_items=order_items, timeline=timeline)


@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    current_user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('index'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    subtotal = sum(item.price * item.quantity for item in order_items)

    items = [{
        'name': item.product_name,
        'size': item.size or 'N/A',
        'color': item.color or 'N/A',
        'quantity': item.quantity,
        'price': f"{item.price * item.quantity:.2f}"
    } for item in order_items]

    context = {
        'order_number': order.order_number,
        'order_id': order.id,
        'order_date': order.created_at.strftime('%B %d, %Y'),
        'payment_method': order.payment_method,
        'status': order.status,
        'items': items,
        'subtotal': f"{subtotal:.2f}",
        'shipping': f"{order.shipping_cost:.2f}",
        'tax': f"{order.tax:.2f}",
        'total': f"{order.total:.2f}",
        'customer_name': f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.username,
        'customer_email': current_user.email,
        'address_line1': order.shipping_address_line1 or '',
        'address_line2': order.shipping_address_line2 or '',
        'city': order.shipping_city or '',
        'state': order.shipping_state or '',
        'postal_code': order.shipping_postal_code or '',
        'country': order.shipping_country or 'Philippines',
        'phone': order.shipping_phone or ''
    }

    return render_template('shop/order_confirmation.html', **context)


@app.route('/test-setup')
def test_setup():
    try:
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='testpassword',
                first_name='Test',
                last_name='User'
            )
            db.session.add(user)

        # Create test product
        product = Product.query.filter_by(name='Essential Cotton Tee').first()
        if not product:
            product = Product(
                name='Essential Cotton Tee',
                description='Soft cotton t-shirt',
                price=299.99,
                stock=80
            )
            db.session.add(product)

        db.session.commit()

        session['user_id'] = user.id

        cart_items = [{
            'product_id': product.id,
            'name': product.name,
            'size': 'M',
            'color': 'White',
            'quantity': 1,
            'price': product.price
        }]

        shipping_info = {
            'address_line1': '123 Test Street',
            'city': 'Quezon City',
            'state': 'Metro Manila',
            'postal_code': '1100',
            'country': 'Philippines',
            'phone': '09123456789'
        }

        order = create_order(user.id, cart_items, shipping_info)

        if order:
            return redirect(url_for('order_confirmation', order_id=order.id))
        else:
            return "Failed to create order"

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created!")

    print("Starting Flask app...")
    print("Visit: http://127.0.0.1:5000/test-setup")
    app.run(debug=True)