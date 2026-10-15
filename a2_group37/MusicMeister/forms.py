from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Length, Email, EqualTo, NumberRange

# creates the login information
class LoginForm(FlaskForm):
    email=StringField("Email Address", validators=[InputRequired('Enter email')])
    password=PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")

 # this is the registration form
class RegisterForm(FlaskForm):
    email = StringField("Email Address", validators=[InputRequired(), Email("Please enter a valid email")])
    first_name = StringField("First Name", validators=[InputRequired()] )
    surname = StringField("Surname", validators=[InputRequired()] )
    contact_number = StringField("Contact Number", validators=[InputRequired(), Length(min=10, max=10)])
    address = StringField("Address", validators=[InputRequired()] )
    # linking two fields - password should be equal to data entered in confirm
    password=PasswordField("Password", validators=[InputRequired(),
                  EqualTo('confirm', message="Passwords should match"), Length(8)])
    confirm = PasswordField("Confirm Password", validators=[InputRequired()])
    
    # submit button
    submit = SubmitField("Register", validators=[InputRequired()])

# booking form
class BookingForm(FlaskForm):
     ticket_quantity = IntegerField("Number of Tickets", validators=[InputRequired(), NumberRange(min=1, max=10)], default=1)
     submit = SubmitField("Book Tickets")

    