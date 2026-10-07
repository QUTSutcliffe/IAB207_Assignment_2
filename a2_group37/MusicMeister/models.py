from . import db
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    
    events = db.relationship("Event", backref="owner")
    
class Event(db.Model):
    __tablename__ = "events"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(255), index=true)
    image_path = db.Column(db.String(64), default="./static/img/band.jpg")
    datetime = db.Column(db.DateTime)
    category = db.Column(db.String(64), index=True)
    price = db.Column(db.Integer, index=True)
    capacity = db.Column(db.Integer, index=True)
    status = db.Column(db.String(64), index=True)
    acknowledgement = db.Column(db.String(1000))
    
    owner_id = db.Column(db.Integer, db.ForeinKey('user.id'))
    
class Comment(db.Model):
    __tablename__ = "comments"
    
    id = db.Column(db.Integer, primary_key=True)
    
class Order(db.Model):
    __tablename__ = "orders"
    
    id = db.Column(db.Integer, primary_key=True)