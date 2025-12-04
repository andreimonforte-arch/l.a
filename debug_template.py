from app import app
import os

print("\n" + "=" * 60)
print("🔍 TEMPLATE DEBUGGING TOOL")
print("=" * 60 + "\n")

templates_dir = os.path.join(app.root_path, 'templates', 'shop')

if os.path.exists(templates_dir):
    print("📁 Templates in shop folder:")
    for file in os.listdir(templates_dir):
        if file.endswith('.html'):
            filepath = os.path.join(templates_dir, file)
            print(f"\n   ✓ {file}")

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                order_count = content.count('order.')
                if order_count > 0:
                    print(f"     Uses 'order' variable: {order_count} times")

                    if 'payment_url' in content:
                        print(f"     Needs: payment_url")
                    if 'payment_method' in content:
                        print(f"     Needs: payment_method")
                    if 'client_key' in content:
                        print(f"     Needs: client_key")
                    if 'public_key' in content:
                        print(f"     Needs: public_key")
else:
    print("❌ Templates/shop folder not found!")

print("\n" + "=" * 60)
print("📋 REQUIRED VARIABLES BY TEMPLATE:")
print("=" * 60 + "\n")

print("shop/payment.html requires:")
print("  • order (Order object)")
print("  • payment_url (string)")
print("  • payment_method (string: 'gcash' or 'maya')")
print()

print("shop/payment_card.html requires:")
print("  • order (Order object)")
print("  • client_key (string)")
print("  • public_key (string)")
print()

print("shop/order_confirmation.html requires:")
print("  • order (Order object)")
print()

print("shop/checkout.html requires:")
print("  • cart_items (list)")
print("  • total (float)")
print("  • cart_count (int)")
print("  • customer (Customer object or None)")
print("  • form_data (dict, optional)")
print()

print("=" * 60)
print("💡 TROUBLESHOOTING:")
print("=" * 60 + "\n")

print("If you see 'order is undefined' error:")
print("  1. Check which URL you're accessing")
print("  2. Look at the full error traceback")
print("  3. Identify which template file is causing it")
print("  4. Verify the route is passing 'order' variable")
print()

print("Common causes:")
print("  • Accessing /payment/<id> without valid order")
print("  • Order ID doesn't exist in database")
print("  • Customer doesn't own the order")
print("  • Template file has typo in variable name")
print()