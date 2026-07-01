from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Ebook(db.Model):
    __tablename__ = "ebooks"
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text, nullable=False)
    price           = db.Column(db.String(50), nullable=True)
    image_filename  = db.Column(db.String(255), nullable=True)
    image_url       = db.Column(db.String(500), nullable=True)
    purchase_link   = db.Column(db.String(500), nullable=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    leads           = db.relationship("Lead", backref="ebook", lazy=True, cascade="all, delete-orphan")

    @property
    def image_src(self):
        if self.image_filename:
            return f"/static/uploads/{self.image_filename}"
        if self.image_url:
            return self.image_url
        return "/static/no-image.png"


class Lead(db.Model):
    __tablename__ = "leads"
    id            = db.Column(db.Integer, primary_key=True)
    ebook_id      = db.Column(db.Integer, db.ForeignKey("ebooks.id"), nullable=False)
    name          = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(150), nullable=False)
    whatsapp      = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    consented     = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
