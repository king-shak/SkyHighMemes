# SkyHighMemes

This is the source code for SkyHighMemes!

# Credential Configuration

If you aren't one of the developers, ignore this. This section will go over how to configure your credentials to access the DynamoDB tables and S3 buckets used for the project.

## What You Need to Provide Me (Shakeel)

All I need from you is your AWS account ID (this is for your root account, not one of the accounts you created in IAM). This can be accessed by clicking the your username in the upper right hand corner of the AWS management console.

## What You Need to Do

### Gaining Access to S3

To access the buckets, if you use your admin AWS account, all you need to do is wait for the thumbs-up from me and you *should* be able to access it - we'll test this later.

However, if you're using another account, the way this works is that the permissions for the bucket are granted to your **admin** account, so you'll need to delegate them to whatever other account you wish to use. Luckily, this is very straightforward: all you need to do is add this following inline policy to whichever user you want to use:

```
{
   "Version": "2012-10-17",
   "Statement": [
      {
         "Sid": "Example",
         "Effect": "Allow",
         "Action": [
            "s3:GetBucketLocation",
			"s3:ListBucket",
			"s3:PutObject",
			"s3:PutObjectAcl",
			"s3:DeleteObject",
			"s3:GetObject",
			"s3:GetObjectAcl"
         ],
         "Resource": [
            "arn:aws:s3:::skyhighmemes-store",
			"arn:aws:s3:::skyhighmemes-store/*"
         ]
      }
   ]
}
```

If you're a little confused as to what to do, follow steps 2.1 - 2.3 here: https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-walkthroughs-managing-access-example2.html#access-policies-walkthrough-cross-account-permissions-acctB-tasks
(You obviously don't need to create a new account, unless you'd like, you can just use whatever existing one you have).

### Gaining Access to DynamoDB

To gain access to DynamoDB, you need to follow the directions here: https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/configure-cross-account-access-to-amazon-dynamodb.html

Specifically, follow the directions from the table titled "Configure Access to Account A from Account B" (you are account B, I am account A). A few things to note:
 * You can name the policy (the first row in the table) and role (the second row in the table) anything, it doesn't matter.
 * When creating the policy you'll see it asking you to paste a JSON document in one part of the setup, paste this one instead:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::336154851508:role/dynamodb-full-access-role-test"
        }
    ]
}
```

 * Lastly, when creating the role (the second row), step **2** tells you to set the type of trusted entity to "AWS Service". Instead, you should select "AWS Account", and select "This account (your 12-digit account ID)" below. Skip step 3, and follow the remaining steps.

## Verifying Your Access

The first thing you need to do is clone the project repository, and checkout the `resource-testing` branch. You need to run the server **locally**. This can be done by running `./run` in the terminal.

If the applications starts and spits some errors, send me the error and we'll work it out.

### Verifying Access to the S3 Bucket

Visit the `/s3test` endpoint. It will take about 10 seconds, after which you should see the message "Uploaded the file!" - in which case all is well. If you see anything other than this, send it to me and we'll work it out.

### Verifying Access to the DynamoDB Tables

Visit the `/dbtest` endpoint. It will take about 10 seconds, after which you should see the message "Successfully inserted a new item!" - in which case all is well. If you see anything other than this, send it to me and we'll work it out.
