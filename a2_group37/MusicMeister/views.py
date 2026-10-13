from flask import Blueprint, render_template

from . import db
from .models import Event

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    events = Event.query.all() #getting all events from db
    return render_template('index.html', events = events)

@main_bp.route('/details')
def details():
    return render_template('details.html')

@main_bp.route('/edit-event')
def edit_event():
    return render_template('edit-event.html')

@main_bp.route('/create-event')
def create_event():
    return render_template('create-event.html')

@main_bp.route('/orders')
def orders():
    return render_template('orders.html')