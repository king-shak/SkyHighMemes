# This contains the User class, an easy way to access the information of a user throughout their
# session.

##########
# IMPORTS.
##########
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, userTable, userid):
        # Make sure the table is valid.
        creationTime = None
        try: creationTime = userTable.creation_date_time
        except Exception as e: raise Exception("Invalid table: {errMsg}".format(errMsg = str(e)))

        # Query the DB for the user info, build up our user instance.
        response = userTable.get_item(Key = {"email": userid})
        if ("Item" in response):
            user = response['Item']
            self.id = userid
            self.username = user['username']
            self.passwordHash = user['passwordHash']
            self.joinDate = user['joinDate']
        else:
            self.id = None
