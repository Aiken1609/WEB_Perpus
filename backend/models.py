from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from datetime import datetime

db = SQLAlchemy()

class Buku(db.Model):
    id_buku = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(150), nullable=False)
    foto = db.Column(db.String(300))
    penerbit = db.Column(db.String(100))
    bahasa = db.Column(db.String(50))
    kategori = db.Column(db.String(100))
    genre = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    rating = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=True)

    reviews = db.relationship('Review', back_populates='buku', cascade='all, delete-orphan')

class User(db.Model):
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(Enum("user", "admin", name="user_roles"), nullable=False)
    foto = db.Column(db.String(300), nullable=True)

    reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')
    rekomendasi = db.relationship('Rekomendasi', back_populates='user', cascade='all, delete-orphan')

class Review(db.Model):
    id_review = db.Column(db.Integer, primary_key=True)
    id_buku = db.Column(db.Integer, db.ForeignKey('buku.id_buku'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    review_text = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buku = db.relationship('Buku', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

class Rekomendasi(db.Model):
    id_rekomendasi = db.Column(db.Integer, primary_key=True)
    id_buku = db.Column(db.Integer, db.ForeignKey('buku.id_buku'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buku = db.relationship('Buku')
    user = db.relationship('User', back_populates='rekomendasi')
