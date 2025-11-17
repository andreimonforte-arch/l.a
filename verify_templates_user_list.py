import os

path = r'C:\Users\DELL\PycharmProjects\Clothing Inventory\templates\users\list.html'

if os.path.exists(path):
    print("✅ File exists!")
    print(f"Size: {os.path.getsize(path)} bytes")
else:
    print("❌ File NOT found!")
    print("Creating file now...")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write("File created")

    print("✅ File created! Now paste the HTML code into it.")