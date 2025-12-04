
from app import app, db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        try:
            print("\n" + "="*60)
            print("🔄 Starting Database Migration...")
            print("="*60 + "\n")

            result = db.session.execute(text("SHOW COLUMNS FROM products LIKE 'image'"))
            if result.fetchone() is None:
                print("📝 Adding 'image' column to products table...")
                db.session.execute(text("ALTER TABLE products ADD COLUMN image LONGBLOB NULL AFTER quantity"))
                print("✅ Successfully added 'image' column\n")
            else:
                print("ℹ️  'image' column already exists\n")

            result = db.session.execute(text("SHOW COLUMNS FROM products LIKE 'image_filename'"))
            if result.fetchone() is None:
                print("📝 Adding 'image_filename' column to products table...")
                db.session.execute(text("ALTER TABLE products ADD COLUMN image_filename VARCHAR(255) NULL AFTER image"))
                print("✅ Successfully added 'image_filename' column\n")
            else:
                print("ℹ️  'image_filename' column already exists\n")

            result = db.session.execute(text("SHOW COLUMNS FROM orders LIKE 'payment_method'"))
            if result.fetchone() is None:
                print("📝 Adding 'payment_method' column to orders table...")
                db.session.execute(text("ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50) NULL AFTER status"))
                print("✅ Successfully added 'payment_method' column\n")
            else:
                print("ℹ️  'payment_method' column already exists\n")

            result = db.session.execute(text("SHOW COLUMNS FROM orders LIKE 'payment_status'"))
            if result.fetchone() is None:
                print("📝 Adding 'payment_status' column to orders table...")
                db.session.execute(text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(20) DEFAULT 'Unpaid' AFTER payment_method"))
                print("✅ Successfully added 'payment_status' column\n")
            else:
                print("ℹ️  'payment_status' column already exists\n")

            result = db.session.execute(text("SHOW COLUMNS FROM orders LIKE 'payment_reference'"))
            if result.fetchone() is None:
                print("📝 Adding 'payment_reference' column to orders table...")
                db.session.execute(text("ALTER TABLE orders ADD COLUMN payment_reference VARCHAR(255) NULL AFTER payment_status"))
                print("✅ Successfully added 'payment_reference' column\n")
            else:
                print("ℹ️  'payment_reference' column already exists\n")

            db.session.commit()

            print("="*60)
            print("✅ Database Migration Completed Successfully!")
            print("="*60)
            print("\n📌 Next Steps:")
            print("   1. Install required package: pip install requests")
            print("   2. Sign up for PayMongo account at https://paymongo.com")
            print("   3. Add PayMongo keys to your .env file:")
            print("      PAYMONGO_SECRET_KEY=your_secret_key")
            print("      PAYMONGO_PUBLIC_KEY=your_public_key")
            print("   4. Restart your Flask application")
            print("   5. Payment features are now ready to use!\n")

        except Exception as e:
            print("\n❌ Migration Failed!")
            print(f"Error: {e}\n")
            db.session.rollback()
            print("💡 Troubleshooting:")
            print("   - Check your database connection in .env file")
            print("   - Ensure MySQL user has ALTER TABLE permissions")
            print("   - Verify the products and orders tables exist\n")
            return False

        return True

if __name__ == '__main__':
    success = migrate_database()
    if not success:
        exit(1)