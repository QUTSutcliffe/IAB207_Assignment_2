from datetime import datetime
from sqlalchemy import func
from . import db
from .models import Event, Order


def update_event_statuses(app):
    with app.app_context():
        now = datetime.now()

        Event.query.filter(
            Event.status == "Open", Event.endtime <= now
        ).update({"status": "Inactive"}, synchronize_session=False)
        
        Event.query.filter(
            Event.status == "Inactive", Event.endtime > now
        ).update({"status": "Open"}, synchronize_session=False)
                
        booked = (
            db.select(func.coalesce(func.sum(Order.ticket_quantity), 0))
            .where(Order.for_event == Event.id)
            .scalar_subquery()
        )
        
        Event.query.filter(
            Event.status == "Open", Event.capacity - booked < 1
        ).update({"status": "Sold Out"}, synchronize_session=False)
        
        Event.query.filter(
            Event.status == "Sold Out", Event.capacity - booked > 0
        ).update({"status": "Open"}, synchronize_session=False)
        

        db.session.commit()