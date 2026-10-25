from flask import Blueprint, render_template, flash, request, url_for, redirect, current_app, abort
from flask_login import login_required, current_user
from . import db
from .forms import BookingForm, EventForm, CommentForm
from .models import Event, Order, Comment, User
from sqlalchemy import func, or_
from flask_login import current_user
from datetime import datetime
import uuid
import os
from functools import lru_cache
from sentence_transformers import SentenceTransformer


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Apply user-selected filters on the server (no custom JavaScript required).
    search = request.args.get('search', '', type=str).strip()
    status = request.args.get('status', '', type=str).strip()
    category = request.args.get('category', '', type=str).strip()
    query = Event.query
    use_ai = 'use_ai' in request.args
    if status:
            query = query.filter(Event.status == status)
    if category:
            query = query.filter(Event.category == category)
    events = query.order_by(Event.datetime.asc()).all()
    keyword_searches = []
    if search:
        term = f'%{search}%'

        keyword_query = query.filter(
            or_(
                Event.name.ilike(term),
                Event.description.ilike(term),
                Event.venue.ilike(term),
                Event.location.ilike(term)
                )
            ).order_by(Event.datetime.asc()).all()
    
        if use_ai:
                # selecting events not in the keyword search to use for Ai search
                keyword_ids = {event.id for event in keyword_query}
                ai_searchable_events = [
                    event for event in events
                    if event.id not in keyword_ids
                ]
                if ai_searchable_events:
                    model=aisearchmodel()
                    aievent_texts = [
                        f"{event.name or ''}. "
                        f"{event.description or ''}. "
                        f"Genre: {event.category or ''}. "
                        f"Venue: {event.venue or ''}. "
                        f"Location: {event.location or ''}"
                        for event in ai_searchable_events]
                    
                    search_embedding = model.encode([search], convert_to_tensor=True)
                    event_embeddings = model.encode(aievent_texts, convert_to_tensor=True)
                    similarities = model.similarity(search_embedding, event_embeddings)[0]

                    sorted_indices = similarities.argsort(descending=True).tolist()
                    ai_searchable_events = [ai_searchable_events[i] for i in sorted_indices]

                #Hybrid Search
                events = keyword_query + ai_searchable_events

        else:
            # Keyword Search
            events = keyword_query
    
    categories = [name for (name,) in db.session.query(Event.category).distinct().order_by(Event.category).all() if name]
    return render_template('index.html', events=events, search=search,
                           status=status, category=category, categories=categories, use_ai=use_ai)

@lru_cache(maxsize=1)
def aisearchmodel():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@main_bp.route('/details/<int:event_id>', methods=['GET', 'POST'])
def details(event_id):
    event = db.session.get(Event, event_id)
    comments = Comment.query.filter_by(commented_event=event_id).all()
    if event is None:
        return render_template('404.html'), 404

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

@main_bp.route('/edit-event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if event.owner_id != current_user.id:
        abort(403)
    form = EventForm(obj=event)
    try:
        if form.validate_on_submit():
            form.populate_obj(event)
            db.session.commit()
            flash('Your event was updated successfully!', 'success')
            return redirect(url_for('main.index'))
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to cancel event')
        flash('Unable to edit the event. Please try again.', 'error')
    return render_template('edit-event.html', form=form, event=event)

@main_bp.route('/cancel-event/<int:event_id>', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if event.owner_id != current_user.id:
        abort(403)

    if event is None:
        abort(404)

    try:
        event.status = 'Cancelled'
        db.session.commit()
        flash('Your event was cancelled.', 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to cancel event')
        flash('Unable to cancel the event. Please try again.', 'error')

    return redirect(url_for('main.index'))

@main_bp.route('/create-event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        existing = db.session.scalar(db.select(Event).where(Event.name == form.name.data))
        if existing:
            form.name.errors.append("An event with this name already exists")
            return render_template('create-event.html', form=form)
 
        image_path = "./static/img/band.jpg"
        file = form.image.data
        if file and file.filename:
            filename = str(uuid.uuid1())
            file.save(os.path.join(current_app.root_path, 'static', 'img', filename))
            image_path = f"./static/img/{filename}"


        if form.acknowledgement.data == 'generic':
            acknowledgement_message = (
                "This event acknowledges the Traditional Owners of the land "
                "on which we meet and pays its respects to Elders "
                "past and present."
            )
        elif form.acknowledgement.data == 'enhanced':
            acknowledgement_message = form.acknowledgementtext.data
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
            acknowledgement_message=acknowledgement_message,
            owner_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash("Your event was created successfully!", "success")
        return redirect(url_for('main.index'))
    return render_template('create-event.html', form=form)

@main_bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(order_owner=current_user.id).all()
    return render_template('orders.html', orders=orders)
