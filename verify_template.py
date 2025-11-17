import os


def check_template_structure():

    required_templates = {
        'Main': [
            'templates/base.html',
            'templates/layout.html',
            'templates/dashboard.html'
        ],
        'Auth': [
            'templates/auth/login.html',
            'templates/auth/admin_login.html',
            'templates/auth/register.html'
        ],
        'Categories': [
            'templates/categories/list.html',
            'templates/categories/create.html',
            'templates/categories/edit.html'
        ],
        'Products': [
            'templates/products/list.html',
            'templates/products/create.html',
            'templates/products/edit.html',
            'templates/products/view.html'
        ],
        'Users': [
            'templates/users/list.html'
        ],
        'Shop': [
            'templates/shop/browse.html',
            'templates/shop/cart.html',
            'templates/shop/checkout.html',
            'templates/shop/product_detail.html',
            'templates/shop/order_confirmation.html',
            'templates/shop/orders.html',
            'templates/shop/order_detail.html'
        ]
    }

    print("=" * 70)
    print("CHECKING TEMPLATE STRUCTURE")
    print("=" * 70)

    all_exist = True
    missing_templates = []

    for category, templates in required_templates.items():
        print(f"\n{category}:")
        for template in templates:
            if os.path.exists(template):
                print(f"  ✓ {template}")
            else:
                print(f"  ✗ {template} - MISSING!")
                all_exist = False
                missing_templates.append(template)

    print("\n" + "=" * 70)
    if all_exist:
        print("✓ All templates exist!")
    else:
        print(f"✗ Missing {len(missing_templates)} template(s):")
        for template in missing_templates:
            print(f"  - {template}")

            directory = os.path.dirname(template)
            if not os.path.exists(directory):
                print(f"    → Need to create directory: {directory}")

    print("=" * 70)

    return all_exist, missing_templates


if __name__ == "__main__":
    all_exist, missing = check_template_structure()

    if not all_exist:
        print("\nTO FIX:")
        print("1. Create missing directories:")
        directories = set(os.path.dirname(t) for t in missing)
        for directory in directories:
            print(f"   mkdir -p {directory}")

        print("\n2. Create missing template files from the artifacts")
        print("   I've provided all templates in the artifacts above.")