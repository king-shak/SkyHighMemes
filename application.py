# This file is where the application is built and run.

##########
# IMPORTS.
##########
from dominate import tags
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_nav import Nav, register_renderer
from flask_nav.elements import Navbar, View
from flask_nav.renderers import Renderer

from auth import auth as auth_blueprint
from auth import usersTable
from main import main as main_blueprint
from models import User

####################
# BUILD APPLICATION.
####################
# registers the "top" menubar
nav = Nav()
@nav.renderer()
class JustDivRenderer(Renderer):
    def visit_Navbar(self, node):
        kwargs = {'_class': 'navbar-end'}
        cont = tags.div(**kwargs)
        for item in node.items:
            cont.add(self.visit(item))

        return cont

    def visit_View(self, node):
        kwargs = {'_class': 'navbar-item'}
        return tags.a(node.text,
                      href=node.get_url(),
                      title=node.text,
                      **kwargs)

    def visit_Subgroup(self, node):
        group = tags.ul(_class='subgroup')
        title = tags.span(node.title)
        if node.active:
            title.attributes['class'] = 'active'

        for item in node.items:
            group.add(tags.li(self.visit(item)))

        return tags.div(title, group)

logo = tags.img(src='./static/img/SkyHigh_Memes.png', height="50", style="margin-top:-15px")
topbar = Navbar(View(logo, 'main.index'),
                View('Home', 'main.index'),
                View('Make a Meme', 'main.create'),
                View('Subscriptions', 'main.subscriptions'),
                View('Log in', 'auth.login'),
                View('Sign up', 'auth.signup')
                )

nav.register_element('top', topbar)

application = Flask(__name__)
Bootstrap(application)


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

# Initialize the navbar with the application.
nav.init_app(application)

# Run the app.
if __name__ == "__main__":
    # TODO: Disable debugging for production.
    application.debug = True
    application.run()
