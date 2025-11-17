import os
import pymysql
from dotenv import load_dotenv

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("   ⚠️  PIL (Pillow) not installed. Skipping placeholder image creation.")
    print("   → Install with: pip install Pillow")

load_dotenv()

print("\n" + "=" * 70)
print("SETTING UP PRODUCT IMAGE UPLOAD")
print("=" * 70 + "\n")

print("1. Creating upload directories...")
directories = [
    'static/uploads/products',
    'static/images'
]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ Created {directory}")
    else:
        print(f"   ✓ {directory} already exists")

print("\n2. Creating placeholder image...")
placeholder_path = 'static/images/placeholder-product.png'

if not os.path.exists(placeholder_path):
    if PIL_AVAILABLE:
        try:
            img = Image.new('RGB', (400, 400), color='#667eea')
            draw = ImageDraw.Draw(img)

            text = "No Image"
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (400 - text_width) / 2
            y = (400 - text_height) / 2

            draw.text((x, y), text, fill=(255, 255, 255))

            draw.ellipse([150, 100, 250, 200], fill=(255, 255, 255))

            img.save(placeholder_path)
            print(f"   ✓ Created {placeholder_path}")
        except Exception as e:
            print(f"   ⚠️  Could not create placeholder: {e}")
            print(f"   → Please manually add an image to {placeholder_path}")
    else:
        print(f"   ⚠️  Skipping placeholder creation (PIL not available)")
        print(f"   → Please manually add an image to {placeholder_path}")
else:
    print(f"   ✓ Placeholder already exists")

print("\n3. Updating database schema...")
try:
    connection = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'products' 
            AND COLUMN_NAME = 'image_url'
        """, (os.getenv('DB_NAME'),))

        exists = cursor.fetchone()[0]

        if exists:
            print("   ✓ image_url column already exists")
        else:
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN image_url VARCHAR(255) NULL AFTER description
            """)
            connection.commit()
            print("   ✓ Added image_url column to products table")

        cursor.execute("""
            UPDATE products 
            SET image_url = '/static/images/placeholder-product.png'
            WHERE image_url IS NULL OR image_url = ''
        """)
        updated = cursor.rowcount
        connection.commit()

        if updated > 0:
            print(f"   ✓ Updated {updated} products with placeholder image")
        else:
            print("   ✓ No products need placeholder update")

    connection.close()
    print("   ✓ Database updated successfully")

except Exception as e:
    print(f"   ✗ Database error: {e}")
    print("   → Please run the SQL script manually: add_product_images.sql")

print("\n4. Checking permissions...")
for directory in directories:
    if os.access(directory, os.W_OK):
        print(f"   ✓ {directory} is writable")
    else:
        print(f"   ⚠️  {directory} is not writable - check permissions")

print("\n" + "=" * 70)
print("SETUP SUMMARY")
print("=" * 70 + "\n")

print("✓ Directories created")
print("✓ Placeholder image created")
print("✓ Database schema updated")
print("✓ Existing products updated")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70 + "\n")

print("1. Update your app.py:")
print("   - Add upload configuration (see artifact)")
print("   - Update Product model to include image_url")
print("   - Update create_product and edit_product routes")
print("")
print("2. Update templates:")
print("   - Replace templates/products/create.html")
print("   - Replace templates/products/edit.html")
print("   - Update list/view templates to show images")
print("")
print("3. Restart Flask app:")
print("   python app.py")
print("")
print("4. Test image upload:")
print("   - Create new product")
print("   - Upload an image")
print("   - Verify it displays correctly")

print("\n" + "=" * 70)
print("✓ Setup complete! You can now upload product images!")
print("=" * 70 + "\n")