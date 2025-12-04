PRODUCTS = [
    {
        'code': 'JKT001',
        'name': 'Classic Bomber Jacket',
        'price': 2799.99,
        'stock': 18,
        'image': 'JKT001.jpg'
    },
    {
        'code': 'TEE001',
        'name': 'Essential Cotton Tee',
        'price': 299.99,
        'stock': 81,
        'image': 'TEE001.jpg'
    },
    {
        'code': 'TEE002',
        'name': 'Premium Classic Tee',
        'price': 499.99,
        'stock': 73,
        'image': 'TEE002.jpg'
    },
    {
        'code': 'ACC001',
        'name': 'Minimalist Cap',
        'price': 499.99,
        'stock': 64,
        'image': 'ACC001.jpg'
    },
    {
        'code': 'PNT001',
        'name': 'Relaxed Fit Jeans',
        'price': 1299.99,
        'stock': 37,
        'image': 'PNT001.jpg'
    }
]

def get_product_by_code(code):
    """Find product by code"""
    for product in PRODUCTS:
        if product['code'] == code:
            return product
    return None