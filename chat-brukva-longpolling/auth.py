# coding=UTF-8

# Tornado modules.
import tornado.web
import tornado.escape

# MongoDb modules.
import pymongo
from bson.objectid import ObjectId

# Import application modules.
from base import BaseHandler



class LoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    """
    Handler for logins with Google Open ID / OAuth
    http://www.tornadoweb.org/documentation/auth.html#google
    """
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        elif self.get_argument("start_google_oauth", None):
            # Set users attributes to ask for.
            ax_attrs = ['name', 'email', 'language', 'username']
            self.authenticate_redirect(ax_attrs=ax_attrs)
        else:
            content = ('<div class="page-header"><h1>Login</h1></div>'
            + '<form action="/login" method="get">' 
            + '<input type="hidden" name="start_google_oauth" value="1">'
            + '<input type="submit" class="btn" value="Sign in with Google">'
            + '</form>')
            self.render_default("index.html", content=content)

    def _on_auth(self, user):
        """
        Callback for third party authentication (last step).
        """
        if not user:
            content = ('<div class="page-header"><h1>Login</h1></div>'
            + '<div class="alert alert-error">' 
            + '<button class="close" data-dismiss="alert">×</button>'
            + '<h3>Authentication failed</h3>'
            + '<p>This might be due to a problem in Tornados GoogleMixin.</p>'
            + '</div>')
            self.render_default("index.html", content=content)
            return None
        
        # @todo: Validate user data.
        # Save user when authentication was successful.
        def on_user_find(result, user=user):
            if result == "null" or not result:
                # If user does not exist, create a new entry.
                user["email"] = str(ObjectId())
                self.application.client.set("user:" + user["email"],
                                            tornado.escape.json_encode(user))
            else:
                # Update existing user.
                # @todo: Should use $set to update only needed attributes?
                dbuser = tornado.escape.json_decode(result)
                dbuser.update(user)
                user = dbuser
                self.application.client.set("user:" + user["email"],
                                            tornado.escape.json_encode(user))
            
            # Save user id in cookie.
            self.set_secure_cookie("user", user["email"])
            self.redirect("/")
        
        dbuser = self.application.client.get("user:" + user["email"], 
                                             on_user_find)
        
        


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect("/")
        
    
