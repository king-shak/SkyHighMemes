# This is where the meat of the application is defined - i.e., the endpoints for
# viewing/creating memes.

##########
# IMPORTS.
##########
import datetime
from email.mime import image
import hashlib
import os
import boto3
from dominate import tags
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_nav import Nav, register_renderer
from flask_nav.elements import Navbar, View
from flask_nav.renderers import Renderer
from werkzeug.utils import secure_filename

from manage_memes import get_meme_url, get_memes, get_makers, get_makers_memes
from meme_maker import addTextToImage, downloadImgFromURL
from util import retrieveBucket, retrieveTable, getCDNURLForS3Object, getKeyFromCDNURL

############
# CONSTANTS.
############
BUCKET_NAME = "skyhighmemes-store"
BUCKET_CDN_DOMAIN = "https://d1kkk6ov7aou0v.cloudfront.net"
MEME_IMG_ACL = "public-read"

USERS_TABLE_NAME = "skyhighmemes-users-table"
MEMES_TABLE_NAME = "skyhighmemes-memes-table"

ALLOWED_EXTENSIONS = {'.png', '.jpg'}

################
# AWS RESOURCES.
################

# Grab the bucket.
s3 = boto3.resource("s3")
memesBucket = retrieveBucket(s3, BUCKET_NAME)

# Grab the tables.
usersTable = retrieveTable(USERS_TABLE_NAME)
memesTable = retrieveTable(MEMES_TABLE_NAME)

#####################
# NAVBAR DECLARATION.
#####################
nav = Nav()

# This is the renderer for the navbar.
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

# Define the authenticated and unauthenticated topbars.
logo = tags.img(src='/static/img/SkyHigh_Memes.png', height="50", style="margin-top:-15px")
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

# We start off with the unauthenticated top bar.
nav.register_element('top', unauthenticatedTopBar)

#################
# MAIN DEFINITON.
#################
main = Blueprint('main', __name__)

###############################
# INDEX (LANDING PAGE) HANDLER.
###############################
@main.route('/')
def index():
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    memes = get_memes()
    makers = get_makers()
    return render_template('home.html', page_title="Check out the latest memes",
                                        meme_list=memes,
                                        maker_title="Top Makers",
                                        maker_list=makers)

########################
# SUBSCRIPTIONS HANDLER.
########################
@main.route('/subscriptions')
@login_required
def subscriptions():
    # Register the authenticated topbar.
    nav.register_element('top', authenticatedTopBar)

    # TODO: Implement this.
    memes = get_memes()
    return(render_template('home.html', page_title="Memes from makers you're subscribed to",
                                        meme_list=memes,
                                        maker_title="Subscriptions"))

######################
# MEME VIEWER HANDLER.
######################
def getUserMemes(userid, exclude = None):
    response = usersTable.get_item(Key = {"email": userid})
    allMemes = response['Item']['memes']
    memes = []
    for i in range(9):
        if (i == len(allMemes)): break
        elif (allMemes[i] == exclude): continue
        else:
            response = memesTable.get_item(Key = {'uri': allMemes[i]})
            memes.append([response['Item']['url'], allMemes[i]])
    return memes

@main.route('/meme/<uri>')
def viewMeme(uri):
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # Grab the meme requested and other memes from the creator.
    response = memesTable.get_item(Key = {'uri': uri})
    if ('Item' not in response): abort(404)
    memes = getUserMemes(response['Item']['owner'], exclude=uri)
    
    # Return them all to the user.
    return render_template('meme.html', url=response['Item']['url'], images=memes)

###########################
# PORTFOLIO VIEWER HANDLER.
###########################
@main.route('/portfolio/<username>')
def viewPortfolio(username):
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    # TODO: Check that username actually exists. The user could enter some junk in the URL bar.
    # return "view portfolio of {username}".format(username = username)
    memes = get_makers_memes(username)
    return(render_template('home.html', page_title="Memes made by {username}".format(username = username),
                                        meme_list=memes,
                                        maker_title=""))

#######################
# MEME VIEWER HANDLERS.
#######################
@main.route('/create')
def create():
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # Grab the set of images they can choose from.
    memes = get_memes()
    return render_template('create.html', image_list=memes)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/create', methods=["POST"])
def create_post():
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # TODO: Implement this.
    # Determine what was posted.
    if (("myfile" in request.form) or ("ourfile" in request.form)):
        imgURL = None
        if ("myfile" in request.form):  # The user has chosen their own image.
            # Grab the file.
            file = request.files['memeImageFile']
            if (file.filename == ''):   # No file was selected.
                flash('No selected file')
                return redirect(url_for('main.create'))
            if (not allowed_file):      # The file has an invalid extension.
                flash('Invalid file: please only choose upload .png and .jpg')
                return redirect(url_for('main.create'))

            # We're good to go - download the file.
            filename = secure_filename(file.filename)
            filepath = 'upload/{filename}'.format(filename = filename)
            split = os.path.splitext(filepath)
            fileKey = 'upload/{filename}'.format(filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + split[1])
            file.save(filepath)
            
            # Upload the file to our bucket, build the URL for it.
            memesBucket.upload_file(filepath, fileKey, ExtraArgs = {'ACL': 'public-read'})
            os.remove(filepath)
            imgURL = getCDNURLForS3Object(BUCKET_CDN_DOMAIN, fileKey)
        else:   # The user has chosen an image from our selection.
            # Using one of our files.
            imgURL = request.form['memeImageUrl']
        
        return render_template('create-text.html', memeURL=imgURL)
    elif ("generate" in request.form):
        # Grab the image URL and text.
        imgURL = request.form['imgURL']
        memeText = request.form['memeText']

        # Create the meme.
        memeURL = None
        imgName = downloadImgFromURL(imgURL)
        if (imgName != None):
            print(imgName)
            meme, duration = addTextToImage(imgName, memeText)
            if (meme != None):
                if (len(meme) == 1):    # Non-GIF.
                    meme[0].save(imgName)
                else:   # GIF.
                    meme[0].save(imgName,
                                save_all=True,
                                append_images=meme[1:],
                                loop=0,
                                duration=duration)
                # Upload to S3.
                split = os.path.splitext(imgName)
                key = "memes/{imgName}".format(imgName = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + split[1])
                memesBucket.upload_file(imgName, key, ExtraArgs = {'ACL': 'public-read'})
                os.remove(imgName)
                memeURL = getCDNURLForS3Object(BUCKET_CDN_DOMAIN, key)
            else:
                raise Exception()
        else:
            raise Exception()
        
        return render_template('create-result.html', memeURL = memeURL)
    else:   # The final page where they view the generated meme.
        memeURL = request.form['imgURL']
        if (request.form.get('saveToProfile')):
            response = usersTable.get_item(Key = {'email': current_user.id})
            newUser = response['Item']

            # First, create the entry in the memes table.
            hashObj = hashlib.md5(bytes(str(datetime.datetime.now()), 'utf-8'))
            memeURI = hashObj.hexdigest()
            memeEntry = {
                'uri': memeURI,     # This is the MD5 hash of the current timestamp.
                'url': memeURL,
                'owner': newUser['email'],
                'likes': 0
            }
            response = memesTable.put_item(Item = memeEntry)

            # Next, add this meme to the user's profile.
            if ('memes' in newUser):   # We'll add this to their existing list of memes.
                newUser['memes'].append(memeURI)
            else:   # This is the user's first meme.
                newUser['memes'] = [memeURI]
            usersTable.put_item(Item = newUser)

            return redirect(url_for('main.viewMeme', uri = memeURI))
        else:
            # Delete the meme from the S3 store.
            s3.Object(BUCKET_NAME, getKeyFromCDNURL(memeURL)).delete()
            # Redirect to the homepage.
            return redirect(url_for('main.index'))

##################
# PROFILE HANDLER.
##################

# TODO: Determine whether we're doing this.
@main.route('/profile')
@login_required
def profile():
    # Register the authenticated topbar.
    nav.register_element('top', authenticatedTopBar)
    return render_template('profile.html', name=current_user.username)
