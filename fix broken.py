from app import app, db, Order, OrderDetail, Product
from sqlalchemy import text


def fix_broken_orders():
    with app.app_context():
        try:
            print("\n" + "=" * 60)
            print("🔧 FIXING BROKEN ORDERS")
            print("=" * 60 + "\n")

            # Find order_details with null order_id
            result = db.session.execute(text(
                "SELECT id, product_id, quantity FROM order_details WHERE order_id IS NULL"
            ))
            broken_details = result.fetchall()

            if not broken_details:
                print("✅ No broken order details found!")
                print("=" * 60 + "\n")
                return

            print(f"Found {len(broken_details)} broken order detail(s)\n")

            # Restore inventory for each broken detail
            for detail_id, product_id, quantity in broken_details:
                product = Product.query.get(product_id)
                if product:
                    old_qty = product.quantity
                    product.quantity += quantity
                    print(f"📦 Product #{product_id} ({product.name})")
                    print(f"   Restored {quantity} units")
                    print(f"   Old quantity: {old_qty} → New quantity: {product.quantity}")

                # Delete the broken detail
                db.session.execute(text(
                    f"DELETE FROM order_details WHERE id = {detail_id}"
                ))
                print(f"   ✅ Removed broken order detail #{detail_id}\n")

            db.session.commit()

            print("=" * 60)
            print("✅ All broken orders have been fixed!")
            print("=" * 60 + "\n")

            # Show summary
            print("📊 Summary:")
            print(f"   • Broken details removed: {len(broken_details)}")
            print(f"   • Inventory restored for {len([d for d in broken_details if Product.query.get(d[1])])} products")
            print("\n💡 Your database is now clean!")
            print()

        except Exception as e:
            print(f"\n❌ Error occurred: {e}")
            db.session.rollback()
            print("\n💡 If the error persists, you may need to manually clean the database.")
            print()


if __name__ == '__main__':
    fix_broken_orders()