"""MusicMeister integration tests. Run: python -m unittest iab207_final_testing -v"""
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parent / 'a2_group37' / 'MusicMeister'


class MusicMeisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROJECT.is_dir():
            raise RuntimeError(f'MusicMeister folder not found: {PROJECT}')
        cls.temp = tempfile.TemporaryDirectory(prefix='iab207_test_', ignore_cleanup_errors=True)
        cls.root = Path(cls.temp.name)
        shutil.copytree(PROJECT, cls.root / 'MusicMeister',
                        ignore=shutil.ignore_patterns('__pycache__', '*.sqlite', '*.sqlite3'))
        (cls.root / 'instance').mkdir(exist_ok=True)
        sys.path.insert(0, str(cls.root))

        # Import and create the app with the scheduler disabled BEFORE it can start.
        with patch('apscheduler.schedulers.background.BackgroundScheduler.start'):
            from MusicMeister import create_app, db
            from MusicMeister.models import User, Event
            cls.app = create_app()
        cls.db, cls.User, cls.Event = db, User, Event
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        db.create_all()

        from flask_bcrypt import generate_password_hash
        password_hash = generate_password_hash('password123').decode('utf-8')
        owner = User(first_name='Owner', surname='Test', email='owner@test.invalid',
                     password_hash=password_hash)
        other = User(first_name='Other', surname='Test', email='other@test.invalid',
                     password_hash=password_hash)
        db.session.add_all([owner, other])
        db.session.flush()
        cls.owner_id, cls.other_id = owner.id, other.id
        now = datetime.now() + timedelta(days=10)
        events = [
            Event(name='Rock Test Concert', description='Live rock concert',
                  venue='City Hall', location='Brisbane', datetime=now,
                  endtime=now + timedelta(hours=2), category='Rock', program='Music',
                  price=12, capacity=10, status='Open', owner_id=owner.id),
            Event(name='Jazz Evening', description='Live jazz',
                  venue='Riverside', location='Gold Coast', datetime=now,
                  endtime=now + timedelta(hours=2), category='Jazz', program='Music',
                  price=12, capacity=10, status='Cancelled', owner_id=owner.id),
        ]
        db.session.add_all(events)
        db.session.commit()
        cls.event_ids = [event.id for event in events]

    @classmethod
    def tearDownClass(cls):
        try:
            cls.db.session.remove()
            cls.db.engine.dispose()
            cls.ctx.pop()
        finally:
            if str(cls.root) in sys.path:
                sys.path.remove(str(cls.root))
            cls.temp.cleanup()

    def setUp(self):
        self.client = self.app.test_client()

    def login_as(self, user_id):
        # Use the REAL login endpoint, not manual session manipulation.
        user = self.db.session.get(self.User, user_id)
        self.assertIsNotNone(user, 'Test user missing from database')
        response = self.client.post('/login', data={
            'email': user.email,
            'password': 'password123',
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302,
                         f'Login failed (HTTP {response.status_code}); check LoginForm')
        self.assertFalse(response.headers.get('Location', '').startswith('/login'),
                         'Login returned to login page')
        # Confirm Flask-Login actually recognizes the user.
        with self.client.session_transaction() as session:
            self.assertEqual(session.get('_user_id'), str(user_id),
                             'Flask-Login did not create the expected session')

    def test_01_homepage(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_02_homepage_contains_events(self):
        self.assertIn(b'Rock Test Concert', self.client.get('/').data)

    def test_03_search_keyword(self):
        response = self.client.get('/?search=Rock')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rock Test Concert', response.data)

    def test_04_search_no_results(self):
        response = self.client.get('/?search=NoSuchConcertXYZ')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Rock Test Concert', response.data)

    def test_05_search_case_insensitive(self):
        response = self.client.get('/?search=rock')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rock Test Concert', response.data)

    def test_06_search_location(self):
        response = self.client.get('/?search=Brisbane')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rock Test Concert', response.data)

    def test_07_category_filter(self):
        response = self.client.get('/?category=Rock')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rock Test Concert', response.data)

    def test_08_status_filter(self):
        response = self.client.get('/?status=Open')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rock Test Concert', response.data)

    def test_09_event_details(self):
        self.assertEqual(self.client.get(f'/details/{self.event_ids[0]}').status_code, 200)

    def test_10_invalid_event_details(self):
        self.assertEqual(self.client.get('/details/99999999').status_code, 404)

    def test_11_login_page(self):
        self.assertEqual(self.client.get('/login').status_code, 200)

    def test_12_register_page(self):
        self.assertEqual(self.client.get('/register').status_code, 200)

    def test_13_guest_orders_protected(self):
        response = self.client.get('/orders')
        self.assertIn(response.status_code, (302, 401))
        if response.status_code == 302:
            self.assertIn('/login', response.headers.get('Location', ''))

    def test_14_guest_edit_protected(self):
        response = self.client.get(f'/edit-event/{self.event_ids[0]}')
        self.assertIn(response.status_code, (302, 401))
        if response.status_code == 302:
            self.assertIn('/login', response.headers.get('Location', ''))

    def test_15_owner_authentication(self):
        self.login_as(self.owner_id)
        response = self.client.get(f'/edit-event/{self.event_ids[0]}')
        self.assertEqual(response.status_code, 200,
                         f'Owner could not open edit form: HTTP {response.status_code}')

    def test_16_other_user_cannot_edit(self):
        self.login_as(self.other_id)
        response = self.client.get(f'/edit-event/{self.event_ids[0]}')
        self.assertIn(response.status_code, (302, 403, 404),
                      'A different user can access the event edit form')
        if response.status_code == 302:
            self.assertNotIn('/login', response.headers.get('Location', ''),
                             'Login failed; ownership protection was not tested')

    def test_17_other_user_cannot_cancel_event(self):
        self.login_as(self.other_id)
        before = self.db.session.get(self.Event, self.event_ids[0]).status
        response = self.client.post(f'/cancel-event/{self.event_ids[0]}')
        self.db.session.expire_all()
        after = self.db.session.get(self.Event, self.event_ids[0]).status
        self.assertEqual(before, after, 'Another user changed the event status')
        self.assertNotIn('/login', response.headers.get('Location', ''),
                         'Login failed; cancellation protection was not tested')

    def test_18_invalid_event_edit_404(self):
        self.login_as(self.owner_id)
        response = self.client.get('/edit-event/99999999')
        self.assertEqual(response.status_code, 404,
                         f'Expected 404; got {response.status_code} '
                         f'and redirect {response.headers.get("Location")}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
