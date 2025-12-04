import os
from flask import Flask

app = Flask(__name__)

print("App root path:", app.root_path)
print("Template folder:", app.template_folder)
print("\nChecking templates folder:")
templates_path = os.path.join(app.root_path, 'templates')
print(f"Templates path: {templates_path}")
print(f"Templates folder exists: {os.path.exists(templates_path)}")

if os.path.exists(templates_path):
    print("\nFiles in templates folder:")
    for file in os.listdir(templates_path):
        print(f"  - {file}")