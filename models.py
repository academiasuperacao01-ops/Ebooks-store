from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Ebook(db.Model):
    __tablename__ = "ebooks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(50), nullable=True)  # texto livre, ex: "R$ 29,90"
    image_filename = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)  # alternativa: link externo da imagem
    purchase_link = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def image_src(self):
        """Retorna a melhor fonte de imagem disponível para exibir no template."""
        if self.image_filename:
            return f"/static/uploads/{self.image_filename}"
        if self.image_url:
            return self.image_url
        return "/static/no-image.png"
