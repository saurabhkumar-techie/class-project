
from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="farmer")
    phone = db.Column(db.String(20))
    village = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    crops = db.relationship("Crop", back_populates="farmer")
    buyer_orders = db.relationship(
        "Order",
        foreign_keys="Order.buyer_id",
        back_populates="buyer"
    )
    farmer_orders = db.relationship(
        "Order",
        foreign_keys="Order.farmer_id",
        back_populates="farmer"
    )
    help_requests = db.relationship(
        "HelpRequest",
        back_populates="user"
    )
    articles = db.relationship(
        "Article",
        back_populates="author"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Crop(db.Model):
    __tablename__ = "crops"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(30), nullable=False, default="kg")
    price_per_unit = db.Column(db.Float, nullable=False)
    quality = db.Column(db.String(50))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship("User", back_populates="crops")
    orders = db.relationship("Order", back_populates="crop")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(
        db.Integer, db.ForeignKey("crops.id"), nullable=False
    )
    buyer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    crop = db.relationship("Crop", back_populates="orders")
    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        back_populates="buyer_orders"
    )
    farmer = db.relationship(
        "User",
        foreign_keys=[farmer_id],
        back_populates="farmer_orders"
    )


class Scheme(db.Model):
    __tablename__ = "schemes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.Text)
    documents = db.Column(db.Text)
    application_steps = db.Column(db.Text)
    official_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), default="Hindi")
    author_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User", back_populates="articles")


class HelpRequest(db.Model):
    __tablename__ = "help_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default="open")
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="help_requests")
