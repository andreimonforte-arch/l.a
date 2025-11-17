from dotenv import load_dotenv
import os

load_dotenv()

print("Testing .env file:")
print(f"DB_HOST = {os.getenv('DB_HOST')}")
print(f"DB_USER = {os.getenv('DB_USER')}")
print(f"DB_NAME = {os.getenv('DB_NAME')}")
print(f"Password set = {os.getenv('DB_PASSWORD') is not None}")

if os.getenv('DB_HOST') is None:
    print("\n❌ ERROR: .env file not loaded!")
    print("Make sure .env is in the same folder as app.py")
else:
    print("\n✓ .env file loaded successfully!")