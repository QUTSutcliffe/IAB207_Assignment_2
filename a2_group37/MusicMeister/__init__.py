# import flask - from 'package' import 'Class'
from flask import Flask, render_template 
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime

db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app():
  
   app = Flask(__name__)  # this is the name of the module/package that is calling this app
   # Should be set to false in a production environment
   app.debug = False
   app.secret_key = 'somesecretkey'
   # set the app configuration data 
   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
   # initialise db with flask app
   db.init_app(app)

   Bootstrap5(app)
    
    #scheduler for regularly updating event statuses
   from apscheduler.schedulers.background import BackgroundScheduler
   from .tasks import update_event_statuses
   
   
   
   scheduler = BackgroundScheduler()
   scheduler.add_job(
      update_event_statuses,
      args=[app],
      trigger="interval",
      minutes=1,
      id="update_event_statuses",
      max_instances=1,
      coalesce=True,
      replace_existing=True,
      next_run_time=datetime.now(),
   )
   scheduler.start()
    
   # initialise the login manager
   login_manager = LoginManager()

   # set the name of the login function that lets user login
   # in our case it is auth.login (blueprintname.viewfunction name)
   login_manager.login_view = 'auth.login'
   login_manager.init_app(app)

   # create a user loader function takes userid and returns User
   # Importing inside the create_app function avoids circular references
   from .models import User
   @login_manager.user_loader
   def load_user(user_id):
      return db.session.scalar(db.select(User).where(User.id==user_id))

   from . import views
   app.register_blueprint(views.main_bp)

   from . import auth
   app.register_blueprint(auth.auth_bp)

   # Error 404 and 500 handlers
   @app.errorhandler(404)
   def page_not_found(e):
      return render_template('404.html'), 404


   @app.errorhandler(500)
   def internal_server_error(e):
      db.session.rollback()
      return render_template('500.html'), 500
   return app