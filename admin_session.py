from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')
    is_active = db.Column(db.Boolean, default=True)


with app.app_context():
    print("\n" + "=" * 70)
    print("ADMIN ACCESS DIAGNOSTICS")
    print("=" * 70 + "\n")

    user = User.query.filter_by(username='supremo_admin').first()

    if user:
        print(f"✓ User found: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")
        print(f"  Active: {user.is_active}")
        print(f"  User ID: {user.id}")

        if user.role != 'Admin':
            print(f"\n⚠️  ISSUE FOUND: Role is '{user.role}' but should be 'Admin'")
            print(f"   Fixing...")
            user.role = 'Admin'
            db.session.commit()
            print(f"   ✓ Fixed! Role is now 'Admin'")
        else:
            print(f"\n✓ Role is correct: Admin")

        if not user.is_active:
            print(f"\n⚠️  ISSUE FOUND: User is inactive")
            print(f"   Activating...")
            user.is_active = True
            db.session.commit()
            print(f"   ✓ Fixed! User is now active")
        else:
            print(f"✓ User is active")

    else:
        print("✗ User 'supremo_admin' not found!")
        print("\nCreating admin user...")

        from werkzeug.security import generate_password_hash

        new_admin = User(
            username='supremo_admin',
            email='admin@clothingstore.com',
            role='Admin',
            is_active=True
        )
        new_admin.password_hash = generate_password_hash('admin123')  # Change this!

        db.session.add(new_admin)
        db.session.commit()

        print("✓ Admin user created!")
        print("  Username: supremo_admin")
        print("  Password: admin123 (CHANGE THIS!)")

    print("\n" + "=" * 70)
    print("ALL ADMIN USERS:")
    print("=" * 70 + "\n")

    admins = User.query.filter_by(role='Admin', is_active=True).all()

    if admins:
        for admin in admins:
            print(f"  → {admin.username} ({admin.email})")
    else:
        print("  No admin users found!")

    print("\n" + "=" * 70)
    print("SOLUTION:")
    print("=" * 70 + "\n")

    print("1. LOGOUT from your current session")
    print("2. Go to: http://localhost:5000/admin/login")
    print("3. Login with:")
    print(f"   Username: supremo_admin")
    print(f"   Password: (your password)")
    print("\n4. After login, check the badge - it should say 'Admin' (red)")
    print("5. Now try creating a product again")

    print("\n" + "=" * 70)
    print("✓ Diagnostic complete!")
    print("=" * 70 + "\n")