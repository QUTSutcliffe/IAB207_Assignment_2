from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField, IntegerField, DateTimeLocalField, SelectField, DecimalField, FileField
from wtforms.validators import InputRequired, Length, Email, EqualTo, NumberRange
from flask_wtf.file import FileAllowed

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

# create event form
class CreateEventForm(FlaskForm):
    name = StringField("Event Name", validators=[InputRequired(), Length(max=64)])
    description = TextAreaField("Description", validators=[InputRequired(), Length(max=255)])
    venue = StringField("Venue", validators=[InputRequired(), Length(max=64)])
    location = StringField("Location", validators=[InputRequired(), Length(max=64)])
    datetime = DateTimeLocalField("Date and Start Time", format="%Y-%m-%dT%H:%M", validators=[InputRequired()])
    endtime = DateTimeLocalField("End Time", format="%Y-%m-%dT%H:%M", validators=[InputRequired()])
    category = SelectField("Genre", choices=[('', 'Select a genre'), ('Rock', 'Rock'), ('Country', 'Country'), ('Hip Hop', 'Hip Hop'), ('Pop', 'Pop'), ('EDM', 'EDM'), ('Jazz', 'Jazz'), ('Classical', 'Classical'), ('Latin', 'Latin'), ('Reggae', 'Reggae')], validators=[InputRequired()])
    program = TextAreaField("Planned Program", validators=[InputRequired(), Length(max=1000)])
    acknowledgement = TextAreaField("Acknowledgement", validators=[Length(max=500)])
    price = IntegerField("Ticket Price ($)", validators=[InputRequired(), NumberRange(min=0)])
    capacity = IntegerField("Total Ticket Capacity", validators=[InputRequired(), NumberRange(min=1)])
    image = FileField("Event Image", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Images only")])
# submit button
    submit = SubmitField("Create Event")
 
# end time must be after the start time
    def validate_endtime(self, field):
        if self.datetime.data and field.data <= self.datetime.data:
            raise ValidationError("End time must be after the start time")

# commenting
class CommentForm(FlaskForm):
    comment_text = TextAreaField("Write your comment", validators=[InputRequired(), Length(max=1000)])
    
    # post comment button
    submit = SubmitField("Post Comment")
