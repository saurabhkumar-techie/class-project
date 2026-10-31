import os
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
    sent_negotiation_messages = db.relationship(
        "NegotiationMessage",
        back_populates="sender"
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
    negotiations = db.relationship("Negotiation", back_populates="crop")

    @property
    def image_url(self):
        """Returns the appropriate clean image URL/path for the crop."""
        if self.image_filename:
            if self.image_filename.startswith(("http://", "https://", "/")):
                return self.image_filename
            crops_dir = os.path.join(os.path.dirname(__file__), "static", "images", "crops")
            if os.path.exists(os.path.join(crops_dir, self.image_filename)):
                return f"/static/images/crops/{self.image_filename}"
            return f"/static/uploads/{self.image_filename}"

        # Smart automatic image matching based on crop name (Hindi & English keywords)
        name_lower = (self.name or "").lower()
        if any(w in name_lower for w in ["wheat", "गेहूं", "gehu", "sharbati"]):
            return "/static/images/crops/wheat.jpg"
        elif any(w in name_lower for w in ["paddy", "rice", "धान", "चावल", "basmati"]):
            return "/static/images/crops/rice.jpg"
        elif any(w in name_lower for w in ["mustard", "सरसों", "sarson", "mustard oil"]):
            return "/static/images/crops/mustard.jpg"
        elif any(w in name_lower for w in ["tomato", "टमाटर", "tamatar"]):
            return "/static/images/crops/tomato.jpg"
        elif any(w in name_lower for w in ["potato", "आलू", "aloo"]):
            return "/static/images/crops/potato.jpg"
        elif any(w in name_lower for w in ["onion", "प्याज", "प्याज़"]):
            return "/static/images/crops/onion.jpg"
        elif any(w in name_lower for w in ["corn", "मक्का", "maize", "makka"]):
            return "/static/images/crops/corn.jpg"
        elif any(w in name_lower for w in ["mango", "आम"]):
            return "/static/images/crops/mango.jpg"

        return "/static/images/crops/default_crop.jpg"


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


class Negotiation(db.Model):
    __tablename__ = "negotiations"

    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(
        db.Integer, db.ForeignKey("crops.id"), nullable=False, index=True
    )
    buyer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    agreed_price = db.Column(db.Float)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    crop = db.relationship("Crop", back_populates="negotiations")
    buyer = db.relationship("User", foreign_keys=[buyer_id])
    farmer = db.relationship("User", foreign_keys=[farmer_id])
    messages = db.relationship(
        "NegotiationMessage",
        back_populates="negotiation",
        order_by="NegotiationMessage.created_at",
        cascade="all, delete-orphan",
    )


class NegotiationMessage(db.Model):
    __tablename__ = "negotiation_messages"

    id = db.Column(db.Integer, primary_key=True)
    negotiation_id = db.Column(
        db.Integer, db.ForeignKey("negotiations.id"), nullable=False, index=True
    )
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    offer_price = db.Column(db.Float, nullable=False)
    message = db.Column(db.String(1000), nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    negotiation = db.relationship("Negotiation", back_populates="messages")
    sender = db.relationship(
        "User", back_populates="sent_negotiation_messages"
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
