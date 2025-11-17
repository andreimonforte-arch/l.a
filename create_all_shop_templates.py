import os

os.makedirs('templates/shop', exist_ok=True)

templates = {
    'checkout.html': '''{% extends "base.html" %}

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
                            <small class="text-muted">Complete address with street, barangay, city, and province</small>
                        </div>

                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> 
                            Orders processed within 1-2 business days. Delivery: 3-7 days.
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
                    <div class="d-flex gap-2 flex-wrap">
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
}

print("\n" + "=" * 70)
print("CREATING ALL SHOP TEMPLATES")
print("=" * 70 + "\n")

created = 0
for filename, content in templates.items():
    filepath = f'templates/shop/{filename}'
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created {filepath}")
        created += 1
    except Exception as e:
        print(f"✗ Error creating {filepath}: {e}")

print("\n" + "=" * 70)
print(f"✓ Successfully created {created} template(s)")
print("=" * 70)
print("\n🎉 All shop templates are ready!")
print("\nNext steps:")
print("1. Restart your Flask app: python app.py")
print("2. Test the complete shopping flow:")
print("   → Browse: http://localhost:5000/shop")
print("   → Cart: http://localhost:5000/cart")
print("   → Checkout: http://localhost:5000/checkout")
print("   → Orders: http://localhost:5000/orders")
print("\n✨ Happy shopping! ✨\n")