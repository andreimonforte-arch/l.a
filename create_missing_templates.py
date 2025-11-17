import os

os.makedirs('templates/shop', exist_ok=True)

checkout_template = '''{% extends "base.html" %}

{% block title %}Checkout{% endblock %}

{% block content %}
<div class="container">
    <h2 class="mb-4"><i class="fas fa-lock"></i> Secure Checkout</h2>

    <div class="row">
        <div class="col-lg-8">
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-user"></i> Delivery Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST" action="{{ url_for('checkout') }}" id="checkout-form">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">First Name *</label>
                                <input type="text" class="form-control" name="first_name" 
                                       value="{{ customer.first_name if customer else (form_data.first_name if form_data else '') }}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Last Name *</label>
                                <input type="text" class="form-control" name="last_name" 
                                       value="{{ customer.last_name if customer else (form_data.last_name if form_data else '') }}" required>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email *</label>
                                <input type="email" class="form-control" name="email" 
                                       value="{{ customer.email if customer else (form_data.email if form_data else '') }}" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone Number *</label>
                                <input type="tel" class="form-control" name="phone" 
                                       value="{{ customer.phone if customer else (form_data.phone if form_data else '') }}" 
                                       placeholder="09XX-XXX-XXXX" required>
                            </div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Delivery Address *</label>
                            <textarea class="form-control" name="address" rows="3" required>{{ customer.address if customer else (form_data.address if form_data else '') }}</textarea>
                            <small class="text-muted">Please provide complete address including street, barangay, city, and province</small>
                        </div>

                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> 
                            <strong>Note:</strong> Orders will be processed within 1-2 business days. 
                            Delivery typically takes 3-7 business days depending on your location.
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="col-lg-4">
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-box"></i> Order Summary</h5>
                </div>
                <div class="card-body">
                    {% for item in cart_items %}
                    <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">{{ item.product.name }}</h6>
                            <small class="text-muted">{{ item.product.size }} | {{ item.product.color }}</small>
                            <p class="mb-0"><small>Qty: {{ item.quantity }} × ₱{{ "%.2f"|format(item.product.price) }}</small></p>
                        </div>
                        <div class="text-end">
                            <strong>₱{{ "%.2f"|format(item.subtotal) }}</strong>
                        </div>
                    </div>
                    {% endfor %}

                    <div class="d-flex justify-content-between mb-2">
                        <span>Subtotal:</span>
                        <span>₱{{ "%.2f"|format(total) }}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Shipping:</span>
                        <span class="text-success">FREE</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Tax:</span>
                        <span>₱0.00</span>
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between mb-3">
                        <h5>Total:</h5>
                        <h5 class="text-success">₱{{ "%.2f"|format(total) }}</h5>
                    </div>

                    <button type="submit" form="checkout-form" class="btn btn-success w-100 btn-lg mb-2">
                        <i class="fas fa-check-circle"></i> Place Order
                    </button>
                    <a href="{{ url_for('view_cart') }}" class="btn btn-outline-secondary w-100">
                        <i class="fas fa-arrow-left"></i> Back to Cart
                    </a>
                </div>
            </div>

            <div class="card shadow-sm">
                <div class="card-body">
                    <h6><i class="fas fa-shield-alt text-success"></i> Secure Payment</h6>
                    <p class="small text-muted mb-2">We accept:</p>
                    <div class="d-flex gap-2">
                        <span class="badge bg-light text-dark">Cash on Delivery</span>
                        <span class="badge bg-light text-dark">Bank Transfer</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('checkout-form').addEventListener('submit', function(e) {
    const btn = this.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
});
</script>
{% endblock %}
'''

# Template for orders.html
orders_template = '''{% extends "base.html" %}

{% block title %}My Orders{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-history"></i> My Orders</h2>
        <a href="{{ url_for('shop') }}" class="btn btn-primary">
            <i class="fas fa-shopping-bag"></i> Continue Shopping
        </a>
    </div>

    {% if orders %}
    <div class="row">
        {% for order in orders %}
        <div class="col-lg-12 mb-4">
            <div class="card shadow-sm">
                <div class="card-header bg-light">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <p class="mb-0"><strong>Order #{{ order.id }}</strong></p>
                            <small class="text-muted">{{ order.order_date.strftime('%B %d, %Y') }}</small>
                        </div>
                        <div class="col-md-3">
                            <p class="mb-0"><small class="text-muted">Status</small></p>
                            {% if order.status == 'Pending' %}
                            <span class="badge bg-warning text-dark">{{ order.status }}</span>
                            {% elif order.status == 'Processing' %}
                            <span class="badge bg-info">{{ order.status }}</span>
                            {% elif order.status == 'Completed' %}
                            <span class="badge bg-success">{{ order.status }}</span>
                            {% else %}
                            <span class="badge bg-danger">{{ order.status }}</span>
                            {% endif %}
                        </div>
                        <div class="col-md-3">
                            <p class="mb-0"><small class="text-muted">Total</small></p>
                            <h5 class="mb-0 text-success">₱{{ "%.2f"|format(order.total_amount) }}</h5>
                        </div>
                        <div class="col-md-3 text-end">
                            <a href="{{ url_for('order_detail', order_id=order.id) }}" class="btn btn-sm btn-primary">
                                <i class="fas fa-eye"></i> View Details
                            </a>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        {% for detail in order.order_details[:3] %}
                        <div class="col-md-4 mb-3">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-tshirt fa-2x text-primary me-3"></i>
                                <div>
                                    <p class="mb-0"><strong>{{ detail.product.name }}</strong></p>
                                    <small class="text-muted">Qty: {{ detail.quantity }} × ₱{{ "%.2f"|format(detail.price) }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                        {% if order.order_details|length > 3 %}
                        <div class="col-md-4 mb-3">
                            <div class="d-flex align-items-center">
                                <div class="alert alert-info mb-0 py-2 px-3">
                                    <i class="fas fa-plus-circle"></i> +{{ order.order_details|length - 3 }} more items
                                </div>
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    {% else %}
    <div class="text-center py-5">
        <i class="fas fa-shopping-bag fa-5x text-muted mb-4"></i>
        <h3>No orders yet</h3>
        <p class="text-muted">Start shopping to place your first order!</p>
        <a href="{{ url_for('shop') }}" class="btn btn-primary btn-lg">
            <i class="fas fa-shopping-bag"></i> Start Shopping
        </a>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

cart_template = '''{% extends "base.html" %}

{% block title %}Shopping Cart{% endblock %}

{% block content %}
<div class="container">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-shopping-cart"></i> Shopping Cart</h2>
        <a href="{{ url_for('shop') }}" class="btn btn-outline-primary">
            <i class="fas fa-arrow-left"></i> Continue Shopping
        </a>
    </div>

    {% if cart_items %}
    <div class="row">
        <div class="col-lg-8">
            <div class="card shadow-sm">
                <div class="card-body">
                    {% for item in cart_items %}
                    <div class="row align-items-center border-bottom py-3" id="cart-item-{{ item.product.id }}">
                        <div class="col-md-2 text-center">
                            <i class="fas fa-tshirt fa-3x text-primary"></i>
                        </div>
                        <div class="col-md-4">
                            <h5 class="mb-1">{{ item.product.name }}</h5>
                            <p class="text-muted small mb-1">{{ item.product.product_code }}</p>
                            <span class="badge bg-secondary">{{ item.product.size }}</span>
                            <span class="badge bg-secondary">{{ item.product.color }}</span>
                        </div>
                        <div class="col-md-2">
                            <p class="mb-0 fw-bold">₱{{ "%.2f"|format(item.product.price) }}</p>
                        </div>
                        <div class="col-md-2">
                            <div class="input-group input-group-sm">
                                <button class="btn btn-outline-secondary qty-btn" type="button" 
                                        data-action="decrease" data-product-id="{{ item.product.id }}">
                                    <i class="fas fa-minus"></i>
                                </button>
                                <input type="number" class="form-control text-center qty-input" 
                                       value="{{ item.quantity }}" min="1" max="{{ item.product.quantity }}"
                                       data-product-id="{{ item.product.id }}" readonly>
                                <button class="btn btn-outline-secondary qty-btn" type="button" 
                                        data-action="increase" data-product-id="{{ item.product.id }}"
                                        {% if item.quantity >= item.product.quantity %}disabled{% endif %}>
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                            <small class="text-muted">Max: {{ item.product.quantity }}</small>
                        </div>
                        <div class="col-md-2">
                            <p class="mb-0 fw-bold subtotal" id="subtotal-{{ item.product.id }}">
                                ₱{{ "%.2f"|format(item.subtotal) }}
                            </p>
                            <form method="POST" action="{{ url_for('remove_from_cart', product_id=item.product.id) }}" 
                                  class="d-inline" onsubmit="return confirm('Remove this item?');">
                                <button type="submit" class="btn btn-link btn-sm text-danger p-0">
                                    <i class="fas fa-trash"></i> Remove
                                </button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="col-lg-4">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-receipt"></i> Order Summary</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Subtotal:</span>
                        <span id="cart-total">₱{{ "%.2f"|format(total) }}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Shipping:</span>
                        <span class="text-success">FREE</span>
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between mb-3">
                        <h5>Total:</h5>
                        <h5 class="text-success" id="final-total">₱{{ "%.2f"|format(total) }}</h5>
                    </div>
                    <a href="{{ url_for('checkout') }}" class="btn btn-success w-100 btn-lg">
                        <i class="fas fa-lock"></i> Proceed to Checkout
                    </a>
                </div>
            </div>

            <div class="card shadow-sm mt-3">
                <div class="card-body">
                    <h6><i class="fas fa-shield-alt text-success"></i> Secure Checkout</h6>
                    <p class="small text-muted mb-0">Your payment information is protected with industry-standard encryption.</p>
                </div>
            </div>
        </div>
    </div>

    {% else %}
    <div class="text-center py-5">
        <i class="fas fa-shopping-cart fa-5x text-muted mb-4"></i>
        <h3>Your cart is empty</h3>
        <p class="text-muted">Add some items to your cart to get started!</p>
        <a href="{{ url_for('shop') }}" class="btn btn-primary btn-lg">
            <i class="fas fa-shopping-bag"></i> Start Shopping
        </a>
    </div>
    {% endif %}
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const qtyButtons = document.querySelectorAll('.qty-btn');

    qtyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const action = this.dataset.action;
            const input = document.querySelector(`.qty-input[data-product-id="${productId}"]`);
            let quantity = parseInt(input.value);

            if (action === 'increase') {
                quantity++;
            } else if (action === 'decrease') {
                quantity--;
            }

            if (quantity < 1) {
                if (confirm('Remove this item from cart?')) {
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = `/cart/remove/${productId}`;
                    document.body.appendChild(form);
                    form.submit();
                }
                return;
            }

            updateCart(productId, quantity);
        });
    });

    function updateCart(productId, quantity) {
        const formData = new FormData();
        formData.append('quantity', quantity);

        fetch(`/cart/update/${productId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const input = document.querySelector(`.qty-input[data-product-id="${productId}"]`);
                input.value = quantity;

                const subtotalEl = document.getElementById(`subtotal-${productId}`);
                subtotalEl.textContent = `₱${data.subtotal.toFixed(2)}`;

                document.getElementById('cart-total').textContent = `₱${data.total.toFixed(2)}`;
                document.getElementById('final-total').textContent = `₱${data.total.toFixed(2)}`;

                const cartBadge = document.querySelector('.badge.bg-light');
                if (cartBadge) {
                    cartBadge.textContent = data.cart_count;
                }

                const maxQty = parseInt(input.getAttribute('max'));
                const increaseBtn = document.querySelector(`.qty-btn[data-action="increase"][data-product-id="${productId}"]`);
                if (quantity >= maxQty) {
                    increaseBtn.disabled = true;
                } else {
                    increaseBtn.disabled = false;
                }
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to update cart');
        });
    }
});
</script>
{% endblock %}
'''

print("Creating missing shop templates...")
print("=" * 60)

try:
    with open('templates/shop/checkout.html', 'w', encoding='utf-8') as f:
        f.write(checkout_template)
    print("✓ Created templates/shop/checkout.html")

    with open('templates/shop/orders.html', 'w', encoding='utf-8') as f:
        f.write(orders_template)
    print("✓ Created templates/shop/orders.html")

    with open('templates/shop/cart.html', 'w', encoding='utf-8') as f:
        f.write(cart_template)
    print("✓ Created templates/shop/cart.html")

    print("=" * 60)
    print("✓ All templates created successfully!")
    print("\nYou can now:")
    print("1. Restart your Flask app")
    print("2. Visit /shop to browse products")
    print("3. Visit /cart to see your shopping cart")
    print("4. Visit /checkout to complete your order")
    print("5. Visit /orders to see your order history")

except Exception as e:
    print(f"✗ Error: {e}")
    print("\nMake sure you're running this script from your project root directory")
    print("(The same folder where app.py is located)")