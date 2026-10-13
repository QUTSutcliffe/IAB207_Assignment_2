from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

# this is a hint for a login function
@auth_bp.route('/login', methods=['GET', 'POST'])
# view function
def login():
    login_form = LoginForm()
    error = None
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user = db.session.scalar(db.select(User).where(User.email==email))

        if user is None:
            error = 'Incorrect user name'

        elif not check_password_hash(user.password_hash, password): # takes the hash and cleartext password
            error = 'Incorrect password'

        if error is None:
            login_user(user)
            nextp = request.args.get('next') # this gives the url from where the login page was accessed
            print(nextp)
            if nextp is None or not nextp.startswith('/') or nextp.startswith('//'):
                return redirect(url_for('main.index'))
            return redirect(nextp)
        
        else:
            flash(error)
    return render_template('user.html', form=login_form, heading='Login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        email = register_form.email.data
        password = register_form.password.data
        first_name = register_form.first_name.data
        surname = register_form.surname.data
        contact_number = register_form.contact_number.data
        address = register_form.address.data

        existing_user = db.session.scalar(
            db.select(User).where(User.email == email)
        )

        if existing_user:
            flash('Email is already registered.')
       
        else:
            hashed_password = generate_password_hash(
                password
            ).decode('utf-8')

            new_user = User(
                email=email,
                password_hash=hashed_password,
                first_name = first_name,
                surname = surname,
                contact_number = contact_number,
                address = address)

            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful.')
            return redirect(url_for('main.index'))

    return render_template(
        'user.html',
        form=register_form,
        heading='Register'
    )

@auth_bp.route('/logout')
@login_required
def logout():

    logout_user()
    flash('Logout successful.')
    return redirect(url_for('main.index'))