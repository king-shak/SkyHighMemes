# This file is where the application is built and run.

##########
# IMPORTS.
##########
from flask import Flask
from flask_login import LoginManager

from auth import auth as auth_blueprint
from auth import usersTable
from main import main as main_blueprint
from models import User

####################
# BUILD APPLICATION.
####################
application = Flask(__name__)

# This has something to do with session management - idk what but DO NOT REMOVE.
application.config['SECRET_KEY'] = 'secret-key-goes-here'

# Configure the login manager.
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(application)

# This tells Flask how to find a specific user from the ID that is stored in their session
# cookie.
@login_manager.user_loader
def load_user(user_id):
    user = User(usersTable, user_id)
    if (user.id == None): return None
    else: return user

# Register blueprints.
application.register_blueprint(auth_blueprint)
application.register_blueprint(main_blueprint)

# Run the app.
if __name__ == "__main__":
    # TODO: Disable debugging for production.
    application.debug = True
    application.run()
