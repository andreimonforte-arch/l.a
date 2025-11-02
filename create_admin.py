from app import app, db, User
from werkzeug.security import generate_password_hash


def create_default_users():
    with app.app_context():

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@clothingstore.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Admin user created: username='admin', password='admin123'")
        else:
            print("✗ Admin user already exists")


        user1 = User.query.filter_by(username='user1').first()
        if not user1:
            user1 = User(
                username='user1',
                email='user1@clothingstore.com',
                role='user'
            )
            user1.set_password('user123')
            db.session.add(user1)
            print("✓ Regular user created: username='user1', password='user123'")
        else:
            print("✗ User1 already exists")

        db.session.commit()
        print("\n✓ User creation completed!")
        print("\nLogin credentials:")
        print("Admin - Username: admin, Password: admin123")
        print("User  - Username: user1, Password: user123")


def create_custom_admin():
    print("\n=== Create Custom Admin User ===")
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()

    with app.app_context():

        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"✗ Username '{username}' already exists!")
            return


        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"✗ Email '{email}' already exists!")
            return


        admin = User(
            username=username,
            email=email,
            role='admin'
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        print(f"✓ Admin user '{username}' created successfully!")


if __name__ == '__main__':
    print("=" * 50)
    print("Clothing Store - User Creation Tool")
    print("=" * 50)

    print("\n1. Create default users (admin/admin123 and user1/user123)")
    print("2. Create custom admin user")
    print("3. Exit")

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == '1':
        create_default_users()
    elif choice == '2':
        create_custom_admin()
    elif choice == '3':
        print("Exiting...")
    else:
        print("Invalid choice!")