from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON

from admin_login import db


# or if using SQLite:
# from sqlalchemy import JSON

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    color = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255))
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # New field for storing size quantities as JSON
    size_quantities = db.Column(JSON, default={})

    # Remove these old fields if they exist:
    # size = db.Column(db.String(20))
    # quantity = db.Column(db.Integer)

    category = db.relationship('Category', backref='products')

    def get_total_quantity(self):
        """Calculate total quantity across all sizes"""
        if self.size_quantities:
            return sum(self.size_quantities.values())
        return 0