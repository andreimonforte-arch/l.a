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
    print("=" * 50)
    print("FIXING USER ROLES")
    print("=" * 50)

    user = User.query.filter_by(username='supremo_admin').first()

    if user:
        print(f"\n✓ Found user: {user.username}")
        print(f"  Current role: {user.role}")

        if user.role != 'Admin':
            user.role = 'Admin'
            db.session.commit()
            print(f"  ✓ Updated role to: Admin")
        else:
            print(f"  ✓ Already an Admin")
    else:
        print("\n✗ User 'supremo_admin' not found!")

    print("\n" + "=" * 50)
    print("ALL USERS:")
    print("=" * 50)

    all_users = User.query.filter_by(is_active=True).all()

    for u in all_users:
        role_badge = "🔴 ADMIN" if u.role == 'Admin' else "🔵 USER"
        print(f"{role_badge} | {u.username:20} | {u.email:30} | {u.role}")

    print("\n" + "=" * 50)
    print("✓ Done! Please logout and login again.")
    print("=" * 50)