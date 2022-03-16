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

# Methods for dealing with SNS: https://www.learnaws.org/2021/05/05/aws-sns-boto3-guide/
def createTopic(name):
    """
    Creates a notification topic.

    :param name: The name of the topic to create.
    :return: The newly created topic.
    """
    sns = boto3.resource("sns", region_name=REGION_NAME)
    topic = sns.create_topic(Name=name)
    return topic

def listTopics():
    """
    Lists topics for the current account.

    :return: An iterator that yields the topics.
    """
    sns = boto3.resource("sns", region_name=REGION_NAME)
    topics_iter = sns.topics.all()
    return topics_iter

def retrieveTopic(topicARN):
    for topic in listTopics():
        print(topic)
        if (topic.arn == topicARN):
            return topic
    return None

def subscribeToTopic(topic, protocol, endpoint):
    """
    Subscribes an endpoint to the topic. Some endpoint types, such as email,
    must be confirmed before their subscriptions are active. When a subscription
    is not confirmed, its Amazon Resource Number (ARN) is set to
    'PendingConfirmation'.

    :param topic: The topic to subscribe to.
    :param protocol: The protocol of the endpoint, such as 'sms' or 'email'.
    :param endpoint: The endpoint that receives messages, such as a phone number
                      or an email address.
    :return: The newly added subscription.
    """
    subscription = topic.subscribe(Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
    return subscription

def deleteSubscription(subscription):
    """
    Unsubscribes and deletes a subscription.
    """
    subscription.delete()

def publishMessage(topic, message):
    """
    Publishes a message to a topic.

    :param topic: The topic to publish to.
    :param message: The message to publish.
    :return: The ID of the message.
    """
    response = topic.publish(Message=message)
    message_id = response['MessageId']
    return message_id

# Methods for dealing with the CDN.
def getCDNURLForS3Object(bucketCDNDomain, objectKey):
    if (not bucketCDNDomain.endswith("/")): bucketCDNDomain += "/"
    if (objectKey.startswith("/")): objectKey = objectKey[1:]
    return bucketCDNDomain + objectKey

def getKeyFromCDNURL(url):
    return url[url.index(".net") + 5:]