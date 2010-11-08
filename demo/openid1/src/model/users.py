'''
Created on Nov 5, 2010

@author: ben
'''
from google.appengine.ext import db


class User(db.Model):
    
    email = db.StringProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def get_user_for_email(email):
        user_to_get = User.get_existing_user(email)
        if not user_to_get:
            user_to_get = User(email=email)
            user_to_get.put()
            
        return user_to_get
    
    @staticmethod
    def get_existing_user(email):
        users_with_email = User.all().filter("email = ", email).fetch(1)
        if len(users_with_email):
            return users_with_email[0]
        else:
            return None
    
class Message(db.Model):
    
    message = db.StringProperty(multiline=True)
    user = db.ReferenceProperty(reference_class=User, collection_name="messages")
    