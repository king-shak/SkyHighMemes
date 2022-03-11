from manage_memes import get_memes, get_meme_url
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from dominate.tags import img

logo = img(src='./static/img/SkyHigh_Memes.png', height="50", style="margin-top:-15px")
topbar = Navbar(View(logo, 'home'),
                View('Home', 'home'),
                View('Make a Meme', 'create_meme'),
                View('Subscriptions', 'get_subscriptions'),
                View('Sign up / Log in', 'handle_account'),
                )

# registers the "top" menubar
nav = Nav()
nav.register_element('top', topbar)

app = Flask(__name__)
Bootstrap(app)


@app.route('/', methods=['GET'])
def home():
    memes = get_memes()
    return(render_template('home.html', page_title="Check out the latest memes", meme_list=memes, maker_title="Trending Makers"))

@app.route('/create', methods=['GET'])
def create_meme():
    return(render_template('create.html'))

@app.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    memes = get_memes()
    return(render_template('home.html', page_title="Memes from makers you're subscribed to", meme_list=memes, maker_title="Subscriptions"))

@app.route('/account', methods=['GET'])
def handle_account():
    return(render_template('account.html'))

@app.route('/meme', methods=['GET'])
def meme():
    meme_id = request.args.get('selected_meme')
    meme_url = get_meme_url(int(meme_id))
    return(render_template('meme.html', meme_url=meme_url))

nav.init_app(app)

if __name__ == '__main__':
  app.run()
  # app.run(host='127.0.0.1', port=5000, debug=True)

# CONFLICT CENTER
  
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