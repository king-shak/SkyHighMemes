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
    return(render_template('home.html', page_name="Home", meme_list=memes))

@app.route('/create', methods=['GET'])
def create_meme():
    return(render_template('create.html'))

@app.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    return(render_template('home.html', page_name="Subscriptions"))

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