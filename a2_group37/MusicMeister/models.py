from . import db
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    surname = db.Column(db.String(64))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    contact_number = db.Column(db.String(12))
    address = db.Column(db.String(64))
    
    
    events = db.relationship("Event", backref="owner")
    orders = db.relationship("Order", backref="orderer")
    
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
    
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    orders = db.relationship("Order", backref="event")
    comments = db.relationship("Comment", backref="event")
    
class Comment(db.Model):
    __tablename__ = "comments"
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000))
    datetime = db.Column(db.DateTime)
    
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    commented_event = db.Column(db.Integer, db.ForeignKey("events.id"))
    
class Order(db.Model):
    __tablename__ = "orders"
    
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer)
    ticket_quantity = db.Column(db.Integer)
    time_ordered = db.Column(db.DateTime)
    
    orderer = db.Column(db.Integer, db.ForeignKey("user.id"))
    for_event = db.Column(db.Integer, db.ForeignKey("events.id"))