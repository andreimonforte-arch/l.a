import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def check_database():

    print("\n" + "=" * 70)
    print("1. CHECKING DATABASE SCHEMA")
    print("=" * 70)

    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )

        with connection.cursor() as cursor:
            # Check if user_id column exists in customers table
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'customers' 
                AND COLUMN_NAME = 'user_id'
            """, (os.getenv('DB_NAME'),))

            if cursor.fetchone():
                print("✓ customers.user_id column exists")
            else:
                print("✗ customers.user_id column missing - FIXING...")

                # Add the column
                cursor.execute("""
                    ALTER TABLE customers 
                    ADD COLUMN user_id INT NULL
                """)

                try:
                    cursor.execute("""
                        ALTER TABLE customers 
                        ADD CONSTRAINT fk_customers_user 
                        FOREIGN KEY (user_id) REFERENCES users(id) 
                        ON DELETE SET NULL
                    """)
                except:
                    print("  (Foreign key might already exist)")

                connection.commit()
                print("✓ Added customers.user_id column")

            cursor.execute("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'role'
            """, (os.getenv('DB_NAME'),))

            result = cursor.fetchone()
            if result:
                print(f"✓ users.role column type: {result[0]}")

        connection.close()
        return True

    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def check_templates():

    print("\n" + "=" * 70)
    print("2. CHECKING TEMPLATE STRUCTURE")
    print("=" * 70)

    required_dirs = [
        'templates',
        'templates/auth',
        'templates/categories',
        'templates/products',
        'templates/users',
        'templates/shop'
    ]

    required_templates = [
        'templates/base.html',
        'templates/admin_login.html',
        'templates/dashboard.html',
        'templates/auth/login.html',
        'templates/auth/admin_login.html',
        'templates/auth/register.html',
        'templates/categories/list.html',
        'templates/categories/create.html',
        'templates/categories/edit.html',
        'templates/products/list.html',
        'templates/products/create.html',
        'templates/products/edit.html',
        'templates/products/view.html',
        'templates/users/list.html',
        'templates/shop/browse.html',
        'templates/shop/cart.html',
        'templates/shop/checkout.html',
        'templates/shop/product_detail.html',
        'templates/shop/order_confirmation.html',
        'templates/shop/orders.html',
        'templates/shop/order_detail.html'
    ]

    missing_dirs = []
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ {directory}/")
        else:
            print(f"✗ {directory}/ - MISSING")
            missing_dirs.append(directory)

    missing_templates = []
    for template in required_templates:
        if os.path.exists(template):
            print(f"✓ {template}")
        else:
            print(f"✗ {template} - MISSING")
            missing_templates.append(template)

    if missing_dirs:
        print("\nTO CREATE DIRECTORIES:")
        for directory in missing_dirs:
            print(f"  mkdir -p {directory}")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"    → Created {directory}")
            except:
                pass

    if missing_templates:
        print(f"\n✗ Missing {len(missing_templates)} template(s)")
        print("Please copy templates from the artifacts provided")
        return False
    else:
        print("\n✓ All templates exist")
        return True


def check_env():

    print("\n" + "=" * 70)
    print("3. CHECKING ENVIRONMENT VARIABLES")
    print("=" * 70)

    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'SECRET_KEY']

    all_exist = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var in ['DB_PASSWORD', 'SECRET_KEY']:
                print(f"✓ {var} = ****")
            else:
                print(f"✓ {var} = {value}")
        else:
            print(f"✗ {var} - MISSING")
            all_exist = False

    return all_exist


def main():
    print("\n" + "=" * 70)
    print("CLOTHING STORE - COMPLETE SETUP CHECK")
    print("=" * 70)

    env_ok = check_env()

    if not env_ok:
        print("\n✗ Please configure .env file first")
        return

    db_ok = check_database()

    templates_ok = check_templates()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if env_ok and db_ok and templates_ok:
        print("✓ All checks passed!")
        print("\nYou can now run your Flask app:")
        print("  python app.py")
    else:
        print("✗ Some issues need to be fixed:")
        if not env_ok:
            print("  - Configure .env file")
        if not db_ok:
            print("  - Fix database schema (run fix_customers_table.sql)")
        if not templates_ok:
            print("  - Create missing templates from artifacts")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()