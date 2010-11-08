#!/usr/bin/env python

import os
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import mail

import model.users

#This is a list of Open ID providers from the Google documentation
openIdProviders = (
    'Google.com/accounts/o8/id', # shorter alternative: "Gmail.com"
    'Yahoo.com',
    'MySpace.com',
    'AOL.com',
    'MyOpenID.com',
    # add more here
)

class HomeHandler(webapp.RequestHandler):
    '''Homepage handler. Renders a standard template with login details
    and a message list'''
    
    def get(self):
        messages = model.users.Message.all().fetch(10)
        
        template_values = {'messages' : messages}
        if not users.get_current_user():
            template_values['open_id_providers'] = get_open_id_providers()
        render_template(self,'templates/home.html', template_values)


class LoginHandler(webapp.RequestHandler):
    '''Handler for PRE- and POST- Login attempts to redirect to the correct
    pages'''

    def get(self):
        '''Handler get requests; Receives requests to login and receives requests
        after login attempts. Forwards login requests to correct page and checks
        the outcome of login requests for the outcome and any followup action
        required'''
        
        current_user = users.get_current_user()
        if self.request.path == '/_ah/login_required':
            # The request has gone directly to a URI marked as requiring login
            # but the user is not logged in. GAE has redirected to 
            # /_ah/login_required so we need to prompt the user for login
            # We're lazy so we are shooting them back to the home page
            # with a message saying what happened.
            
            self.redirect('/?smsg=2') 
        
        elif self.request.get("done") and current_user:
            #user is logged in but we need to check the data provided 
            #by the provider is sufficient
            logging.info("Login complete")
            
            logging.info(current_user.email())
            if not mail.is_email_valid(current_user.email()):
                logging.info('checked email addy')
                #provider has not provided an email address. Not good.
                #force a log out and redirect to the home page with a
                #explanatory message
                logout_url = users.create_logout_url(dest_url="/?smsg=1")
                self.redirect(logout_url)
            else:
                self.redirect("/")
        
        elif self.request.get("done") and not current_user:
            #log on not complete. Log on was cancelled
            logging.info("Login cancelled")
            self.redirect("/")
                         
        elif not current_user:
            #user is not logged in, proceed to create the login URL 
            #and redirect. Notice this address is the return address
            open_id_provider = self.request.get("provider")
            login_url = users.create_login_url(dest_url="/login?done=1"
                                           , federated_identity=open_id_provider)
            logging.info("commencing login with %s", open_id_provider)
            self.redirect(login_url)
        
        else:
            #user is already logged
            #what were they thinking?
            logging.info("user already logged in")
            self.redirect("/")
        
class LogoutHandler(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")
        self.redirect(logout_url)

class MessageHandler(webapp.RequestHandler):
    '''Message handler. Posts new messages (only) and redirects back to the
    home page. Uses the confusingly named (by me) model.users.User to assign
    an actual model user object to the message to save'''
    
    def post(self):
        message = self.request.get("message")
        logging.info('in handler')
        logging.info(message)
        if users.get_current_user() and len(message):
            logging.info('Saving message')
            current_user =\
            model.users.User.get_user_for_email(
                    users.get_current_user().email()
                    )
            new_message = model.users.Message(message=message, user=current_user)
            new_message.put()
            
        self.redirect('/')
            
class SecureHandler(webapp.RequestHandler):
    '''Secure page handler. An example of a page declared as requiring login within
    the application configuration app.yaml file.'''
    
    def get(self):
        render_template(self,'templates/secure.html')       
        
class NotFoundHandler(webapp.RequestHandler):
    '''Page not found handler''' 
    
    def get(self):
        logging.info('Page not found')
        self.error(404)
        render_template(self,'templates/notfound.html')
        

def main():
    application = webapp.WSGIApplication([('/', HomeHandler),
                                          ('/login', LoginHandler),
                                          ('/logout', LogoutHandler),
                                          ('/messages', MessageHandler),
                                          ('/secure', SecureHandler),
                                          ('/_ah/login.*', LoginHandler),
                                          ('/.*^(gif|ico|jpg|png)', NotFoundHandler)
                                          ],
                                         debug=True)
        
    util.run_wsgi_app(application)

def render_template(request_handler, template_file, params = {}):
    '''A helper function to render templates. Includes user object from the
    google.api.user library if available as well a system message if indicated
    '''
    
    #add standard parameters
    params['user'] = users.get_current_user()

    #check for system message
    smsg_id = request_handler.request.get("smsg")
    if smsg_id == '1':
        params['system_message'] = 'Login provider did not provide an email address. Login aborted'
    if smsg_id == '2':
        params['system_message'] = 'You need to login to view this page'

    
    #render template
    path = os.path.join(os.path.dirname(__file__), template_file)
    request_handler.response.out.write(template.render(path, params))    

def get_open_id_providers():
    ''' returns a list of tuples containing open id provider display names
    and open id addresses. Shamelessly borrowed from the Google Open Id 
    example '''
    open_id_providers = [(p.split('.')[0],p.lower()) for p in openIdProviders ]
    logging.info(open_id_providers)
    return open_id_providers


if __name__ == '__main__':
    main()


