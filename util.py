# This contains helper methods for retrieving AWS resources such as the S3 bucket and DynamoDB
# tables.

##########
# IMPORTS.
##########
import sys

import boto3
import botocore

############
# CONSTANTS.
############

# These are all used for connecting to the DynamoDB resource.
REGION_NAME = "us-west-2"
ROLE_ARN = "arn:aws:iam::336154851508:role/dynamodb-full-access-role-test"  # Hopefully we can use
                                                                            # the same one for all
                                                                            # of them...
ROLE_SESSION_NAME = "RoleSessionName"   # This can be anything.

##########
# METHODS.
##########

# Retrieves a bucket given a S3 resource instance and the name of the bucket.
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
            s3.meta.client.head_bucket(Bucket = bucketName)
        except botocore.exceptions.ClientError as e:
            # The bucket may exist, but even if it does, we don't have access to it.
            print("ERROR: Unable to retrieve bucket \"{bucketName}\"".format(bucketName = bucketName))
            sys.exit()

    # Return the bucket.
    return s3.Bucket(bucketName)

# Retrieves a DynamoDB table given the name of the table.
def retrieveTable(tableName):
    dynamodb = boto3.resource("dynamodb", region_name = REGION_NAME)
    table = dynamodb.Table(tableName)
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
            table = dynamodb.Table(tableName)
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
            print("ERROR: Unable to retrieve table \"{tableName}\"".format(tableName = tableName))
            sys.exit()
    
    # If we got here, we're good to go.
    return table

def getCDNURLForS3Object(bucketCDNDomain, objectKey):
    if (not bucketCDNDomain.endswith("/")): bucketCDNDomain += "/"
    if (objectKey.startswith("/")): objectKey = objectKey[1:]
    return bucketCDNDomain + objectKey

def getKeyFromCDNURL(url):
    return url[url.index(".net") + 5:]