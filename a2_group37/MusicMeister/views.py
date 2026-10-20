from flask import Blueprint, render_template, flash, request, url_for, redirect, current_app
from flask_login import login_required, current_user
from . import db
from .forms import BookingForm, CreateEventForm, CommentForm
from .models import Event, Order, Comment, User
from sqlalchemy import func
from flask_login import current_user
from datetime import datetime
import uuid
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    events = Event.query.all() #getting all events from db
    return render_template('index.html', events = events)

@main_bp.route('/details/<int:event_id>', methods=['GET', 'POST'])
def details(event_id):
    event = db.session.get(Event, event_id)
    comments = Comment.query.filter_by(commented_event=event_id).all()
    if event is None:
        flash('Event does not exist.')
        return redirect(url_for('main.index'))

    booked = db.session.scalar(
    db.select(func.coalesce(func.sum(Order.ticket_quantity), 0))
    .where(Order.for_event == event.id))

    available = max(event.capacity - booked, 0)
    
    booking_form = BookingForm()
    
    comment_form = CommentForm()
    comment_text = comment_form.comment_text.data
        
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to leave comments.')
            return redirect(url_for('auth.login'))
        if comment_text is None:
            flash('Please make sure comment has text.')
        elif len(comment_text) < 5:
            flash('Plase make sure comment has more than 5 characters.')
        else:
            new_comment = Comment(
                text=comment_form.comment_text.data,
                datetime=datetime.now(),
                owner_id=current_user.id,
                commented_event=event.id
            )
            db.session.add(new_comment)
            db.session.commit()

            flash('Comment successful.')
            return redirect(url_for('main.details', event_id=event.id))

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
                price=float(event.price) * ticket_quantity,
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
        comment_form=comment_form,
        comments=comments,
        booked=booked,
        available=available
    )

@main_bp.route('/edit-event')
def edit_event():
    return render_template('edit-event.html')

@main_bp.route('/create-event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = CreateEventForm()
    if form.validate_on_submit():
        existing = db.session.scalar(db.select(Event).where(Event.name == form.name.data))
        if existing:
            form.name.errors.append("An event with this name already exists")
            return render_template('create-event.html', form=form)
 
        image_path = "./static/img/band.jpg"
        file = form.image.data
        filename = str(uuid.uuid1())
        file.save(os.path.join(current_app.root_path, 'static', 'img', filename))
        image_path = f"./static/img/{filename}"
 
        event = Event(
            name=form.name.data,
            description=form.description.data,
            image_path=image_path,
            venue=form.venue.data,
            location=form.location.data,
            datetime=form.datetime.data,
            endtime=form.endtime.data,
            category=form.category.data,
            program=form.program.data,
            price=form.price.data,
            capacity=form.capacity.data,
            status="Open",
            acknowledgement=form.acknowledgement.data,
            owner_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash("Your event was created successfully!", "success")
        return redirect(url_for('main.index'))
    return render_template('create-event.html', form=form)

@main_bp.route('/orders')
def orders():
    orders = Order.query.filter_by(order_owner=current_user.id).all()
    return render_template('orders.html', orders=orders)