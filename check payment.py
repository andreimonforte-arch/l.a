import os
from dotenv import load_dotenv

load_dotenv()


def check_payment_setup():
    print("\n" + "=" * 60)
    print("🔍 PAYMENT SETUP CHECKER")
    print("=" * 60 + "\n")

    issues = []
    warnings = []

    print("📦 Checking required packages...")
    try:
        import requests
        print("   ✅ requests library installed")
    except ImportError:
        issues.append("requests library not installed")
        print("   ❌ requests library NOT installed")
        print("      Fix: pip install requests")

    print()

    print("🔑 Checking PayMongo API keys...")
    secret_key = os.getenv('PAYMONGO_SECRET_KEY', '')
    public_key = os.getenv('PAYMONGO_PUBLIC_KEY', '')

    if not secret_key or secret_key == '':
        warnings.append("PayMongo Secret Key not configured")
        print("   ⚠️  PAYMONGO_SECRET_KEY not found in .env")
    elif secret_key.startswith('sk_test_'):
        print("   ✅ PAYMONGO_SECRET_KEY configured (TEST MODE)")
    elif secret_key.startswith('sk_live_'):
        print("   ✅ PAYMONGO_SECRET_KEY configured (LIVE MODE)")
    else:
        issues.append("Invalid PayMongo Secret Key format")
        print("   ❌ Invalid PAYMONGO_SECRET_KEY format")

    if not public_key or public_key == '':
        warnings.append("PayMongo Public Key not configured")
        print("   ⚠️  PAYMONGO_PUBLIC_KEY not found in .env")
    elif public_key.startswith('pk_test_'):
        print("   ✅ PAYMONGO_PUBLIC_KEY configured (TEST MODE)")
    elif public_key.startswith('pk_live_'):
        print("   ✅ PAYMONGO_PUBLIC_KEY configured (LIVE MODE)")
    else:
        issues.append("Invalid PayMongo Public Key format")
        print("   ❌ Invalid PAYMONGO_PUBLIC_KEY format")

    print()

    print("🗄️  Checking database...")
    try:
        from app import app, db, Order
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('orders')]

            required_columns = ['payment_method', 'payment_status', 'payment_reference']
            missing_columns = [col for col in required_columns if col not in columns]

            if missing_columns:
                issues.append(f"Missing database columns: {', '.join(missing_columns)}")
                print(f"   ❌ Missing columns in orders table: {', '.join(missing_columns)}")
                print("      Fix: python migrate_database.py")
            else:
                print("   ✅ Database columns are up to date")
    except Exception as e:
        issues.append(f"Database check failed: {str(e)}")
        print(f"   ❌ Database check failed: {str(e)}")

    print()

    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60 + "\n")

    if not issues and not warnings:
        print("✅ All checks passed! Payment system is ready.")
        print("\n💡 Available payment methods:")
        print("   • Cash on Delivery")
        if secret_key and public_key:
            print("   • GCash")
            print("   • Maya (PayMaya)")
            print("   • Credit/Debit Cards")
    else:
        if issues:
            print("❌ Critical Issues Found:")
            for issue in issues:
                print(f"   • {issue}")
            print()

        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
            print()

        print("📝 Current Status:")
        print("   • Cash on Delivery: ✅ Available")
        if secret_key and public_key:
            print("   • Online Payments: ✅ Available")
        else:
            print("   • Online Payments: ❌ Not Available")

    print()
    print("=" * 60)

    if warnings and not issues:
        print("\n💡 To enable online payments:")
        print("   1. Sign up at https://paymongo.com")
        print("   2. Get your API keys from the dashboard")
        print("   3. Add them to your .env file:")
        print("      PAYMONGO_SECRET_KEY=sk_test_your_key_here")
        print("      PAYMONGO_PUBLIC_KEY=pk_test_your_key_here")
        print("   4. Restart your Flask app")

    print()


if __name__ == '__main__':
    check_payment_setup()