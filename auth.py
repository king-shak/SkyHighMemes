# This file handles everything related to authentication, account creation, and session management.

##########
# IMPORTS.
##########
import datetime

today = datetime.date.today()
from boto3.dynamodb.conditions import Attr
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from main import authenticatedTopBar, unauthenticatedTopBar, nav, usersTable
from models import User
from util import createTopic


########
# SETUP.
########

# Define the auth blueprint. This has all the event handlers for handling session management.
auth = Blueprint('auth', __name__)

#################
# LOGIN HANDLERS.
#################
@auth.route('/login')
def login():
    # Register the unauthenticated topbar and return the login page.
    nav.register_element('top', unauthenticatedTopBar)
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    # Grab the email, password, and whether they want their credentials to be remembered from the
    # HTML form.
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    # Check whether the user actually exists (user.id shouldn't be None), and if so, whether the
    # password is correct.
    user = User(usersTable, email)
    if (user.id != None and check_password_hash(user.passwordHash, password)):
        # The user has the right credentials.
        login_user(user, remember=remember)     # Starts the session.
        nav.register_element('top', authenticatedTopBar)
        return redirect(url_for('main.subscriptions'))
    else:
        # Incorrect credentials.
        flash('Please check your login details and try again.')
        nav.register_element('top', unauthenticatedTopBar)
        return redirect(url_for('auth.login'))

##################
# SIGNUP HANDLERS.
##################

# Determines whether a user exists - returns True if so or False otherwise.
def isValidEmail(email):
    user = User(usersTable, email)
    return (user.id == None)

def isValidUsername(username):
    response = usersTable.scan(FilterExpression = Attr("username").eq(username))
    return (response["Count"] == 0)

# Creates a new user in the database. THIS WILL OVERWRITE ANY EXISTING ENTRY WITH THE SAME EMAIL.
# You must ensure the email and username are not already in use before calling this method.
def createUser(email, username, password):
    # Create their SNS topic.
    topic = createTopic("{username}-sns-topic".format(username = username))
    topicARN = topic.arn

    # Create their account into the actual DB.
    item = {
        "email": email,
        "username": username,
        "passwordHash": generate_password_hash(password, method="sha256"),
        "joinDate": today.strftime("%b %d %Y"),
        "topicARN": topicARN
    }
    usersTable.put_item(Item = item)
    return User(usersTable, email)

@auth.route('/signup')
def signup():
    # Register the unauthenticated topbar.
    nav.register_element('top', unauthenticatedTopBar)
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    # Register the unauthenticated topbar.
    nav.register_element('top', unauthenticatedTopBar)

    # Grab the email, username and password from the HTML form.
    email = request.form.get('email')
    username = request.form.get('name')
    password = request.form.get('password')

    # If the email is already in use, create the account.
    user = None
    validEmail = isValidEmail(email)
    validUsername = isValidUsername(username)
    if ((not validEmail) or (not validUsername)):
        # Either the email or username is already in use.
        if (not validEmail): flash('Email address already in use')
        if (not validUsername): flash('Username already exists')
        return redirect(url_for('auth.signup'))
    
    # Create the new user, adding the information to the database.
    user = createUser(email, username, password)

    # Send them to login with their new credentials.
    return redirect(url_for('auth.login'))

#################
# LOGOUT HANDLER.
#################
@auth.route('/logout')
@login_required
def logout():
    # Register the unauthenticated topbar.
    nav.register_element('top', unauthenticatedTopBar)
    logout_user()   # Ends the session.
    return redirect(url_for('main.index'))  # Redirect to the landing page.
