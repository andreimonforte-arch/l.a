from app import app, db, User
import sys


def create_admin():
    print("=" * 60)
    print("        CLOTHING STORE - CREATE ADMIN ACCOUNT")
    print("=" * 60)
    print()


    while True:
        username = input("Enter admin username (3-50 characters): ").strip()
        if len(username) < 3 or len(username) > 50:
            print("❌ Username must be between 3 and 50 characters!")
            continue


        with app.app_context():
            existing = User.query.filter_by(username=username).first()
            if existing:
                print(f"❌ Username '{username}' already exists!")
                retry = input("Try another username? (y/n): ").lower()
                if retry != 'y':
                    return
                continue
        break


    while True:
        email = input("Enter admin email: ").strip()
        if '@' not in email or '.' not in email:
            print("❌ Please enter a valid email address!")
            continue


        with app.app_context():
            existing = User.query.filter_by(email=email).first()
            if existing:
                print(f"❌ Email '{email}' already in use!")
                retry = input("Try another email? (y/n): ").lower()
                if retry != 'y':
                    return
                continue
        break

    while True:
        password = input("Enter admin password (minimum 6 characters): ").strip()
        if len(password) < 6:
            print("❌ Password must be at least 6 characters!")
            continue

        confirm = input("Confirm password: ").strip()
        if password != confirm:
            print("❌ Passwords do not match!")
            continue
        break

    print("\n" + "=" * 60)
    print("Creating admin account...")

    try:
        with app.app_context():
            admin = User(
                username=username,
                email=email,
                role='admin',
                is_active=True
            )
            admin.set_password(password)

            db.session.add(admin)
            db.session.commit()

            print("\n✅ SUCCESS! Admin account created!")
            print("=" * 60)
            print(f"👤 Username: {username}")
            print(f"📧 Email:    {email}")
            print(f"🛡️  Role:     Admin")
            print(f"🔑 Password: {password}")
            print("=" * 60)
            print("\nYou can now login at:")
            print("👉 http://127.0.0.1:5000/admin/login")
            print()

    except Exception as e:
        print(f"\n❌ Error creating admin: {e}")


def list_admins():
    print("\n" + "=" * 60)
    print("        CURRENT ADMIN ACCOUNTS")
    print("=" * 60)

    try:
        with app.app_context():
            admins = User.query.filter_by(role='admin', is_active=True).all()

            if not admins:
                print("No admin accounts found.")
            else:
                print(f"\nFound {len(admins)} admin account(s):\n")
                for admin in admins:
                    print(f"👤 {admin.username:<20} | 📧 {admin.email:<30} | 🛡️  ADMIN")

            print("=" * 60)
    except Exception as e:
        print(f"❌ Error: {e}")


def upgrade_user_to_admin():
    print("\n" + "=" * 60)
    print("        UPGRADE USER TO ADMIN")
    print("=" * 60)

    username = input("\nEnter username to upgrade to admin: ").strip()

    try:
        with app.app_context():
            user = User.query.filter_by(username=username).first()

            if not user:
                print(f"❌ User '{username}' not found!")
                return

            if user.role == 'admin':
                print(f"ℹ️  User '{username}' is already an admin!")
                return


            print(f"\nUpgrade '{username}' ({user.email}) to ADMIN?")
            confirm = input("Type 'yes' to confirm: ").lower()

            if confirm != 'yes':
                print("❌ Cancelled.")
                return

            user.role = 'admin'
            db.session.commit()

            print("\n✅ SUCCESS!")
            print(f"👤 {username} is now an ADMIN!")
            print("\nThey can now login at:")
            print("👉 http://127.0.0.1:5000/admin/login")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "CLOTHING STORE ADMIN MANAGER" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    while True:
        print("\nWhat would you like to do?")
        print()
        print("1. Create new admin account")
        print("2. Upgrade existing user to admin")
        print("3. List all admin accounts")
        print("4. Exit")
        print()

        choice = input("Enter your choice (1-4): ").strip()

        if choice == '1':
            create_admin()
        elif choice == '2':
            upgrade_user_to_admin()
        elif choice == '3':
            list_admins()
        elif choice == '4':
            print("\n👋 Goodbye!\n")
            sys.exit(0)
        else:
            print("❌ Invalid choice! Please enter 1, 2, 3, or 4.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user. Goodbye!\n")
        sys.exit(0)
