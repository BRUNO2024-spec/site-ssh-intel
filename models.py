from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ServerCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(50), nullable=False)
    flag_code = db.Column(db.String(10), default='br') # ISO code like 'br', 'us'
    ports = db.Column(db.String(200)) # Comma separated like '80, 8080'
    protocols = db.Column(db.String(200)) # Comma separated like 'WS, WSS'
    api_token = db.Column(db.String(200))
    api_url_create = db.Column(db.String(200))
    api_url_monitor = db.Column(db.String(200))
    api_url_stats = db.Column(db.String(200))
    google_ads_enabled = db.Column(db.Boolean, default=False)
    google_ads_code = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AppConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)

class XrayLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    link = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
