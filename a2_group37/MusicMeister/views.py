from flask import Blueprint, render_template, flash, request, url_for, redirect
from . import db
from .forms import BookingForm
from .models import Event, Order
from sqlalchemy import func
from flask_login import current_user
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    events = Event.query.all() #getting all events from db
    return render_template('index.html', events = events)

@main_bp.route('/details/<int:event_id>', methods=['GET', 'POST'])
def details(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        flash('Event does not exist.')
        return redirect(url_for('main.index'))

    booked = db.session.scalar(
    db.select(func.coalesce(func.sum(Order.ticket_quantity), 0))
    .where(Order.for_event == event.id))

    available = max(event.capacity - booked, 0)
    
    booking_form = BookingForm()

    if booking_form.validate_on_submit():
     if not current_user.is_authenticated:
        flash('Please log in to book tickets.')
        return redirect(url_for('auth.login'))

    ticket_quantity = booking_form.ticket_quantity.data
    
    if booking_form.validate_on_submit():
        ticket_quantity = booking_form.ticket_quantity.data

        if event.status != 'Open':
            flash('This event is not open for bookings.')
        elif ticket_quantity > available:
            flash('There are not enough tickets available.')
        else:
            new_order = Order(
                price=float(event.price.replace('$', '')) * ticket_quantity,
                ticket_quantity=ticket_quantity,
                time_ordered=datetime.now(),
                order_owner=current_user.id,
                for_event=event.id
            )


            db.session.add(new_order)
            db.session.commit()

            flash('Booking successful.')
            return redirect(url_for('main.orders'))

    return render_template(
        'details.html',
        event=event,
        form=booking_form,
        booked=booked,
        available=available
    )

@main_bp.route('/edit-event')
def edit_event():
    return render_template('edit-event.html')

@main_bp.route('/create-event')
def create_event():
    return render_template('create-event.html')

@main_bp.route('/orders')
def orders():
    orders = Order.query.filter_by(order_owner=current_user.id).all()
    return render_template('orders.html', orders=orders)