import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

connection = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

try:
    with connection.cursor() as cursor:

        cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
        result = cursor.fetchone()
        print("Current 'role' column definition:")
        print(result)
        print()


        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        print("Existing users:")
        for user in users:
            print(f"  {user}")
        print()

finally:
    connection.close()

print("\nSuggested fix: The database role column type might need to be altered.")
print("Run this SQL to fix it:")
print("ALTER TABLE users MODIFY COLUMN role ENUM('Admin','Staff','User') DEFAULT 'User';")