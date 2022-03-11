# This is where the meat of the application is defined - i.e., the endpoints for
# viewing/creating memes.

##########
# IMPORTS.
##########
import boto3
from flask import Blueprint, render_template
from flask_login import current_user, login_required

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

main = Blueprint('main', __name__)

###############################
# INDEX (LANDING PAGE) HANDLER.
###############################
@main.route('/')
def index():
    # TODO: Implement this.
    return render_template('index.html')

########################
# SUBSCRIPTIONS HANDLER.
########################
@main.route('/subscriptions')
@login_required
def subscriptions():
    # TODO: Implement this.
    return "subscriptions"

######################
# MEME VIEWER HANDLER.
######################
@main.route('/meme/<uri>')
def viewMeme(uri):
    # TODO: Implement this.
    return "view meme {uri}".format(uri = uri)

###########################
# PORTFOLIO VIEWER HANDLER.
###########################
@main.route('/portfolio/<username>')
def viewPortfolio(username):
    # TODO: Implement this.
    # TODO: Check that username actually exists. The user could enter some junk in the URL bar.
    return "view portfolio of {username}".format(username = username)

#######################
# MEME VIEWER HANDLERS.
#######################
@main.route('/create')
def create():
    # TODO: Implement this.
    return "create meme start"

@main.route('/create', methods=["POST"])
def create_post():
    # TODO: Implement this.
    raise NotImplementedError()

##################
# PROFILE HANDLER.
##################

# TODO: Determine whether we're doing this.
@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.username)
