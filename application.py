##########
# IMPORTS.
##########
from datetime import datetime
from time import sleep
from doctest import UnexpectedException
import os
from flask import Flask
import boto3

############
# CONSTANTS.
############
BUCKET_NAME = "skyhighmemes-store"
MEME_IMG_ACL = "public-read"

############
# AWS SETUP.
############
def retrieveBucket(s3, bucketName):
    # Make sure the bucket exists, just in case.
    buckets = s3.buckets.all()
    bucket = [cur for cur in buckets if cur.name == bucketName]
    if (len(bucket) == 0):
        exceptionMsg = "ERROR: Unable to retrieve bucket \"{bucketName}\"" \
                            .format(bucketName = bucketName)
        raise UnexpectedException(exceptionMsg)

    # Return the bucket.
    return s3.Bucket(bucketName)

# Setup S3.
s3 = boto3.resource("s3")
bucket = retrieveBucket(s3, BUCKET_NAME)

#########################
# .
#########################

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
    success = True
    msg = "Uploaded the file!"

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
            sleep(10)
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

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()