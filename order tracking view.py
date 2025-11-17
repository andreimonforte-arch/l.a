from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, Order, OrderItem, Product, User, Customer

db.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    current_user = get_current_user()

    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('shop'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    subtotal = sum(item.price * item.quantity for item in order_items)
    shipping = order.shipping_cost or 100.00
    tax = order.tax or (subtotal * 0.12)
    total = subtotal + shipping + tax

    items = []
    for item in order_items:
        items.append({
            'name': item.product_name,
            'size': item.size or 'N/A',
            'color': item.color or 'N/A',
            'quantity': item.quantity,
            'price': f"{item.price * item.quantity:.2f}"
        })

    context = {
        'order_number': order.order_number or f"ORD{order.id:06d}",
        'order_id': order.id,
        'order_date': order.created_at.strftime('%B %d, %Y'),
        'payment_method': order.payment_method or 'Cash on Delivery',
        'status': order.status or 'Processing',
        'items': items,
        'subtotal': f"{subtotal:.2f}",
        'shipping': f"{shipping:.2f}",
        'tax': f"{tax:.2f}",
        'total': f"{total:.2f}",
        'customer_name': f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.username,
        'customer_email': current_user.email,
        'address_line1': order.shipping_address_line1,
        'address_line2': order.shipping_address_line2 or '',
        'city': order.shipping_city,
        'state': order.shipping_state,
        'postal_code': order.shipping_postal_code,
        'country': order.shipping_country or 'Philippines',
        'phone': order.shipping_phone
    }

    return render_template('shop/order_confirmation.html', **context)


@app.route('/orders/<int:order_id>')
@login_required
def track_order(order_id):
    current_user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('my_orders'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    timeline = []

    if order.status in ['Pending', 'Processing']:
        timeline = [
            {'status': 'Order Placed', 'date': order.created_at, 'completed': True},
            {'status': 'Processing', 'date': order.processing_date, 'completed': order.status == 'Processing'},
            {'status': 'Shipped', 'date': None, 'completed': False},
            {'status': 'Delivered', 'date': None, 'completed': False}
        ]
    elif order.status == 'Shipped':
        timeline = [
            {'status': 'Order Placed', 'date': order.created_at, 'completed': True},
            {'status': 'Processing', 'date': order.processing_date, 'completed': True},
            {'status': 'Shipped', 'date': order.shipped_date, 'completed': True},
            {'status': 'Delivered', 'date': None, 'completed': False}
        ]
    elif order.status == 'Delivered':
        timeline = [
            {'status': 'Order Placed', 'date': order.created_at, 'completed': True},
            {'status': 'Processing', 'date': order.processing_date, 'completed': True},
            {'status': 'Shipped', 'date': order.shipped_date, 'completed': True},
            {'status': 'Delivered', 'date': order.delivered_date, 'completed': True}
        ]
    elif order.status == 'Cancelled':
        timeline = [
            {'status': 'Order Placed', 'date': order.created_at, 'completed': True},
            {'status': 'Cancelled', 'date': order.cancelled_date, 'completed': True}
        ]

    context = {
        'order': order,
        'order_items': order_items,
        'timeline': timeline
    }

    return render_template('shop/track_order.html', **context)


@app.route('/my-orders')
@login_required
def my_orders():
    current_user = get_current_user()
    orders = Order.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(Order.created_at.desc()).all()

    return render_template('shop/my_orders.html', orders=orders)


def create_order(user_id, cart_items, shipping_info, payment_method='Cash on Delivery'):

    try:
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        shipping = 100.00
        tax = subtotal * 0.12
        total = subtotal + shipping + tax

        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"

        order = Order(
            user_id=user_id,
            order_number=order_number,
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
            shipping_phone=shipping_info.get('phone'),
            processing_date=datetime.now()
        )

        db.session.add(order)
        db.session.flush()  # Get order ID

        # Create order items
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

            # Update product quantity
            product = Product.query.get(item['product_id'])
            if product:
                product.quantity -= item['quantity']

        db.session.commit()
        return order

    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {e}")
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard') if user.role == 'Admin' else url_for('shop'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/shop')
@login_required
def shop():
    products = Product.query.filter_by(is_deleted=False).all()
    return render_template('shop/browse.html', products=products)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)