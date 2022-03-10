##########
# IMPORTS.
##########
from datetime import datetime
import sys
from time import sleep
import os
from flask import Flask
import boto3
import botocore
import random
import string

############
# CONSTANTS.
############
BUCKET_NAME = "skyhighmemes-store"
MEME_IMG_ACL = "public-read"

USERS_TABLE_NAME = "skyhighmemes-user-table"
MEMES_TABLE_NAME = "skyhighmemes-memes-table"
REGION_NAME = "us-west-2"

# These are used for the STS connection.
ROLE_ARN = "arn:aws:iam::336154851508:role/dynamodb-full-access-role-test"  # Hopefully we can use
                                                                            # the same one for all
                                                                            # of them...
ROLE_SESSION_NAME = "RoleSessionName"

# TODO: Remove this constant.
N = 10

# Debugging.
SLEEP_TIME = 10

###########
# S3 SETUP.
###########
def retrieveBucket(s3, bucketName):
    # Make sure the bucket exists, just in case.
    buckets = s3.buckets.all()
    bucket = [cur for cur in buckets if cur.name == bucketName]
    if (len(bucket) == 0):
        # We don't own the bucket. See if we can still access it.
        bucket = s3.Bucket(bucketName)
        try:
            # Run the head bucket operation to determine (a) if the bucket exists and (b) if we
            # have access to it.
            s3.meta.client.head_bucket(Bucket = BUCKET_NAME)
        except botocore.exceptions.ClientError as e:
            # The bucket may exist, but even if it does, we don't have access to it.
            print("ERROR: Unable to retrieve bucket \"{bucketName}\"".format(bucketName = bucketName))
            sys.exit()

    # Return the bucket.
    return s3.Bucket(bucketName)

# Grab the bucket.
s3 = boto3.resource("s3")
bucket = retrieveBucket(s3, BUCKET_NAME)

#################
# DYNAMODB SETUP.
#################
def retrieveTable(tableName):
    dynamodb = boto3.resource("dynamodb", region_name = REGION_NAME)
    table = dynamodb.Table(MEMES_TABLE_NAME)
    creationTime = None

    # Try to connect to the table. See if we own it.
    try: creationTime = table.creation_date_time
    except Exception as e: creationTime = None

    if (creationTime == None):
        # We don't own the table, so we must connect using STS.
        try:
            # Form the STS connection.
            client = boto3.client("sts")
            assumedRoleObject = client.assume_role(RoleArn = ROLE_ARN,
                                                    RoleSessionName = ROLE_SESSION_NAME)
            
            # Grab the temporary credentials to make a connection to DynamoDB.
            credentials = assumedRoleObject['Credentials']

            # Form the DynamoDB connection and grab our table.
            dynamodb = boto3.resource("dynamodb",
                                        region_name= REGION_NAME, 
                                        aws_access_key_id = credentials['AccessKeyId'],
                                        aws_secret_access_key = credentials['SecretAccessKey'],
                                        aws_session_token = credentials['SessionToken'])
            table = dynamodb.Table(MEMES_TABLE_NAME)
        except Exception as e:
            # Some error in forming the STS connection, perhaps the roles or permissions are
            # misconfigured.
            print("ERROR: Failed to form STS connection: {errorMsg}".format(errorMsg = str(e)))
            sys.exit()
        
        # STS connection succeeded, check the table is valid.
        try:
            creationTime = table.creation_date_time
        except Exception as e:
            # The table doesn't exist.
            print("ERROR: Unable to retrieve table \"{tableName}\"".format(tableName = MEMES_TABLE_NAME))
            sys.exit()
    
    # If we got here, we're good to go.
    return table

# Grab our two tables.
memesTable = retrieveTable(MEMES_TABLE_NAME)
usersTable = retrieveTable(USERS_TABLE_NAME)

#####################
# HTML FOR RESPONSES.
#####################

# Form a greeting.
def sayHello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

# Some HTML for the various pages.
headerText = '''
    <html>\n<head> <title>TEST TEST TEST</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Thelonious</code>) to say hello to
    someone specific.</p>\n'''
homeLink = '<p><a href="/">Back</a></p>\n'
footerText = '</body>\n</html>'

#########################
# APPLICATION DEFINITION.
#########################
application = Flask(__name__)

@application.route("/")
def index():
    return headerText + sayHello() + instructions + footerText

@application.route("/<username>")
def hello(username):
    return headerText + sayHello(username) + homeLink + footerText

def printObjectsInBucket(bucket):
    printedSomething = False
    for object in bucket.objects.all():
        printedSomething = True
        print(object.key)
    if (not printedSomething): print ("(Nothing here)")

@application.route("/s3test")
def storeTest():
    success = True      # Keeps track of whether anything failed along the way.
    msg = "Uploaded the file!"      # The message to be displayed on the page to the user.

    # First, print the contents of the bucket.
    print("Bucket contents at the start:")
    printObjectsInBucket(bucket)
    print()     # Extra newline.

    # Create the file.
    fileName = str(datetime.now())
    with open(fileName, "w+") as file:
        file.write("test\n")

    # Upload the file to S3, print the contents of the bucket again.
    try:
        s3.Object(BUCKET_NAME, fileName).put(Body = open(fileName, "rb"), ACL = MEME_IMG_ACL)
    except Exception as e:
        success = False
        msg = "Failed to upload file: {errMsg}".format(errMsg = str(e))
    
    if (success):
        print("Bucket contents after uploading {fileName}:".format(fileName = fileName))
        printObjectsInBucket(bucket)
        print()     # Extra newline.

    # Remove the local file, try to download it again.
    os.remove(fileName)
    try:
        if (success): bucket.download_file(fileName, fileName)
    except Exception as e:
        success = False
        msg = "Failed to download file: {errMsg}".format(errMsg = str(e))

    # Attempt to delete the object, print the contents of the bucket again.
    try:
        if (success):
            sleep(SLEEP_TIME)
            s3.Object(BUCKET_NAME, fileName).delete()
    except Exception as e:
        success = False
        msg = "Failed to remove file: {errMsg}".format(errMsg = str(e))
    
    if (success):
        print("Bucket contents after deleting {fileName}:".format(fileName = fileName))
        printObjectsInBucket(bucket)
        print()     # Extra newline.

    # Return the status to the user.
    return headerText + "<p>{msg}</p>".format(msg = msg) + homeLink + footerText

@application.route("/dbtest")
def dbTest():
    success = True
    msg = "Successfully inserted a new item!"

    # Generate some random strings, grab the current time, form the item.
    picURL = "".join(random.choices(string.ascii_uppercase + string.digits, k = N))
    title = "".join(random.choices(string.ascii_uppercase + string.digits, k = N))
    time = str(datetime.now())
    key = {
        "picURL": picURL,
        "title": title
    }
    item = {
        **key,
        "time": time
    }

    # Make the entry in the DB.
    try: memesTable.put_item(Item = item)
    except Exception as e:
        success = False
        msg = "Failed to put an item into the DB: {errMsg}".format(errMsg = str(e))

    # Retrieve the entry.
    retrievedItem = None
    try:
        if (success):
            response = memesTable.get_item(Key = key)
            retrievedItem = response['Item']
    except Exception as e:
        success = False
        msg = "Failed to put an item into the DB: {errMsg}".format(errMsg = str(e))
    
    # Make sure the item we retrieved matches the original one.
    if (retrievedItem != item):
        success = False
        msg = "The retrieved item was didn't match the original one."

    # Now, delete the entry.
    try:
        if (success):
            sleep(SLEEP_TIME)
            memesTable.delete_item(Key = key)
    except Exception as e:
        success = False
        msg = "Failed to remove the item from the DB: {errMsg}".format(errMsg = str(e))

    # Return something to the user.
    return headerText + "<p>{msg}</p>".format(msg = msg) + homeLink + footerText

##############
# RUN THE APP.
##############
if __name__ == "__main__":
    # TODO: disable debugging mode when moving to production.
    application.debug = True
    application.run()