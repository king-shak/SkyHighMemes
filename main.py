# This is where the meat of the application is defined - i.e., the endpoints for
# viewing/creating memes.

##########
# IMPORTS.
##########
import boto3
from dominate import tags
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from flask_nav import Nav, register_renderer
from flask_nav.elements import Navbar, View
from flask_nav.renderers import Renderer

from manage_memes import get_meme_url, get_memes
from meme_maker import addTextToImage, downloadImgFromURL
from util import retrieveBucket, retrieveTable

############
# CONSTANTS.
############
BUCKET_NAME = "skyhighmemes-store"
BUCKET_CDN_DOMAIN = "https://d1kkk6ov7aou0v.cloudfront.net"
MEME_IMG_ACL = "public-read"

MEMES_TABLE_NAME = "skyhighmemes-memes-table"

########
# SETUP.
########

# Grab the bucket.
s3 = boto3.resource("s3")
bucket = retrieveBucket(s3, BUCKET_NAME)

# Grab the memes table.
memesTable = retrieveTable(MEMES_TABLE_NAME)

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
authenticatedTopBar = Navbar(View(logo, 'main.index'),
                            View('Home', 'main.index'),
                            View('Make a Meme', 'main.create'),
                            View('Subscriptions', 'main.subscriptions'),
                            View('Log out', 'auth.logout'))

unauthenticatedTopBar = Navbar(View(logo, 'main.index'),
                                View('Home', 'main.index'),
                                View('Make a Meme', 'main.create'),
                                View('Subscriptions', 'main.subscriptions'),
                                View('Log in', 'auth.login'),
                                View('Sign up', 'auth.signup'))
nav.register_element('top', unauthenticatedTopBar)

main = Blueprint('main', __name__)

###############################
# INDEX (LANDING PAGE) HANDLER.
###############################
@main.route('/')
def index():
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    memes = get_memes()
    return render_template('home.html', page_title="Check out the latest memes",
                                        meme_list=memes,
                                        maker_title="Trending Makers")

########################
# SUBSCRIPTIONS HANDLER.
########################
@main.route('/subscriptions')
@login_required
def subscriptions():
    nav.register_element('top', authenticatedTopBar)

    # TODO: Implement this.
    memes = get_memes()
    return(render_template('home.html', page_title="Memes from makers you're subscribed to",
                                        meme_list=memes,
                                        maker_title="Subscriptions"))

######################
# MEME VIEWER HANDLER.
######################
@main.route('/meme/<uri>')
def viewMeme(uri):
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    # meme_id = request.args.get('selected_meme')
    memes = get_memes()
    url = memes[int(uri)-1]
    
    # meme_url = get_meme_url(int(uri))
    return(render_template('meme.html', url=url,images=memes))

###########################
# PORTFOLIO VIEWER HANDLER.
###########################
@main.route('/portfolio/<username>')
def viewPortfolio(username):
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    # TODO: Check that username actually exists. The user could enter some junk in the URL bar.
    return "view portfolio of {username}".format(username = username)

#######################
# MEME VIEWER HANDLERS.
#######################
@main.route('/create')
def create():
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    memes = get_memes()
    return render_template('create.html', image_list=memes)

@main.route('/create', methods=["POST"])
def create_post():
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    # image_url = request.form['filename']
    image_file = request.form['memeImageFile']
    image_url = request.form['memeImageUrl']
    # meme.html was put as placeholder, so it's clear how the image was passed
    return(render_template('meme.html', url=image_url if image_url else image_file))

##################
# PROFILE HANDLER.
##################

# TODO: Determine whether we're doing this.
@main.route('/profile')
@login_required
def profile():
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    return render_template('profile.html', name=current_user.username)
