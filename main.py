# This is where the meat of the application is defined - i.e., the endpoints for
# viewing/creating memes.

##########
# IMPORTS.
##########
from crypt import methods
import datetime
from email.mime import image
import hashlib
import os
import random
from types import new_class
import boto3
from boto3.dynamodb.conditions import Attr
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
                            View('My Memes', 'main.profile'),
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
def getMemes(creators):
    # First, retrieve the creators we should get memes from.
    chosenUsers = []
    if (creators == 'all'):     # Get memes from all creators.
        # Retrieve all the users.
        response = usersTable.scan()
        users = response['Items']

        # Choose 10 users at random.
        if (len(users) > 10): chosenUsers = random.sample(users, 10)
        else: chosenUsers = users
    else:       # Get memes from a select few creators.
        for creator in creators:    # creator is the creator ID (email).
            response = usersTable.get_item(Key = {'email': creator})
            chosenUsers.append(response['Item'])
    
    # Grab the URIs of the first 3 memes for each user.
    memes = []
    names = []
    for user in chosenUsers:
        count = 3
        if ('memes' not in user): continue
        maker = {'name': user['username'], 'subs': 0}
        if ('subscribers' in user): maker['subs'] = len(user['subscribers'])
        names.append(maker)
        for meme in user['memes']:
            if (count == 0): break
            response = memesTable.get_item(Key = {'uri': meme})
            memes.append([response['Item']['url'], meme])
            count = count - 1

    # Return the memes, and sort the names list.
    return memes, sorted(names, key=lambda m: m['subs'], reverse=True)

@main.route('/')
def index():
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # Grab the memes.
    memes, names = getMemes('all')

    return render_template('home.html', page_title="Check out the latest memes",
                                        meme_list=memes,
                                        maker_title="Trending Makers",
                                        maker_list=names)

########################
# SUBSCRIPTIONS HANDLER.
########################
@main.route('/subscriptions')
@login_required
def subscriptions():
    # Register the authenticated topbar.
    nav.register_element('top', authenticatedTopBar)

    # Grab the memes.
    memes = None
    names = None
    response = usersTable.get_item(Key = {"email": current_user.id})
    curUser = response['Item']
    if ('subscriptions' in curUser): memes, names = getMemes(curUser['subscriptions'])

    return render_template('home.html', page_title="Memes from makers you're subscribed to",
                                        meme_list=memes,
                                        maker_title="Subscriptions",
                                        maker_list=names)

######################
# MEME VIEWER HANDLER.
######################
def getUserMemes(userid, limit = None, exclude = None):
    # Grab the URIs of all the memes created by this user.
    response = usersTable.get_item(Key = {"email": userid})
    if ('memes' not in response['Item']): return None
    allMemes = response['Item']['memes']

    # Setup loop params.
    if (limit == None): limit = len(allMemes)
    selection = []
    for uri in allMemes:
        if (limit == 0): break      # We've reached the limit.
        elif (uri == exclude): continue     # We need to skip this meme.
        else:
            # Grab the meme URL.
            response = memesTable.get_item(Key = {'uri': uri})
            selection.append([response['Item']['url'], uri])
            limit = limit - 1
    return selection

@main.route('/meme/<uri>')
def viewMeme(uri):
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    # Grab the meme requested and other memes from the creator.
    response = memesTable.get_item(Key = {'uri': uri})
    if ('Item' not in response): abort(404)
    imgURL = response['Item']['url']
    creatorID = response['Item']['owner']
    memes = getUserMemes(creatorID, limit=9, exclude=uri)
    
    # Get the name of the creator.
    response = usersTable.get_item(Key = {'email': creatorID})
    creatorName = response['Item']['username']
    
    # Return them all to the user.
    return render_template('meme.html', url=imgURL, images=memes, creator_name=creatorName)

###########################
# PORTFOLIO VIEWER HANDLER.
###########################
@main.route('/portfolio/<username>')
def viewPortfolio(username):
    # Register the appropriate topbar.
    if (current_user.is_authenticated): nav.register_element('top', authenticatedTopBar)
    else: nav.register_element('top', unauthenticatedTopBar)

    response = usersTable.scan(FilterExpression = Attr("username").eq(username))
    if (response['Count'] == 0): abort(404)     # A user with that name does not exist.

    # Check if the current user is subscribed to this creator.
    subscribed = False
    if (current_user.is_authenticated):
        response_cur = usersTable.get_item(Key = {"email": current_user.id})
        if ('subscriptions' in response_cur['Item'] and response['Items'][0]['email'] in response_cur['Item']['subscriptions']): subscribed = True

    # Get all the memes for that user.
    return render_template('portfolio.html', page_title="Memes made by {username}".format(username = username),
                                            meme_list=getUserMemes(response['Items'][0]['email']),
                                            sameUser=(current_user.username == username),
                                            subscribed=subscribed,
                                            creatorName=username)

@main.route('/portfolio', methods=['POST'])
@login_required
def subscribe():
    creatorName = request.form['creator']
    response = usersTable.scan(FilterExpression = Attr("username").eq(creatorName))
    creator = response['Items'][0]
    creatorID = creator['email']

    # Add the creator to the subscriber's list.
    response = usersTable.get_item(Key = {'email': current_user.id})
    newUser = response['Item']
    if ('subscriptions' in newUser):    # We'll add this to their existing list of ubscriptions.
        newUser['subscriptions'].append(creatorID)
    else:       # This is their first subscription.
        newUser['subscriptions'] = [creatorID]
    usersTable.put_item(Item = newUser)

    # Add the subcriber to the creators's list.
    if ('subscribers' in creator):
        creator['subscribers'].append(current_user.id)
    else:
        creator['subscribers'] = [current_user.id]
    usersTable.put_item(Item = creator)

    # Return the user to the portfolio page.
    return redirect(url_for('main.viewPortfolio', username=creatorName))

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
@main.route('/profile')
@login_required
def profile():
    # Register the authenticated topbar.
    nav.register_element('top', authenticatedTopBar)

    # Grab the user's meme and return them to the client.
    return render_template('account.html', meme_list=getUserMemes(current_user.id))
