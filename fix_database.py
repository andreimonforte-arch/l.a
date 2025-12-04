import pymysql

# UPDATE THESE WITH YOUR ACTUAL DATABASE CREDENTIALS
# Check your app.py for the correct credentials
connection = pymysql.connect(
    host='localhost',
    user='root',  # Change this to your MySQL username
    password='',  # Change this to your MySQL password (empty string if no password)
    database='clothing_inventory'  # Change this to your actual database name
)

try:
    with connection.cursor() as cursor:
        # Check current columns in users table
        print("Checking users table structure...")
        cursor.execute("SHOW COLUMNS FROM users")
        columns = cursor.fetchall()

        print("\nCurrent columns in users table:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")

        # Check if password column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'password'")
        result = cursor.fetchone()

        if not result:
            print("\n❌ Password column is missing!")
            print("Adding password column...")
            cursor.execute("ALTER TABLE users ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT ''")
            connection.commit()
            print("✅ Password column added successfully!")
        else:
            print("\n✅ Password column already exists!")

        # Show updated structure
        print("\nUpdated users table structure:")
        cursor.execute("SHOW COLUMNS FROM users")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")

except pymysql.err.OperationalError as e:
    if e.args[0] == 1045:
        print("\n❌ ERROR: Access denied!")
        print("Please update the database credentials in this script:")
        print("  - host (currently: 'localhost')")
        print("  - user (currently: 'root')")
        print("  - password (currently: '')")
        print("  - database (currently: 'clothing_inventory')")
        print("\nCheck your app.py file for the correct SQLALCHEMY_DATABASE_URI")
    elif e.args[0] == 1049:
        print(f"\n❌ ERROR: Database does not exist!")
        print(f"Please create the database first or check the database name.")
    else:
        print(f"\n❌ ERROR: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
finally:
    connection.close()
    print("\nConnection closed.")