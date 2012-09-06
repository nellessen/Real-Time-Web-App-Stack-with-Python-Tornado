# coding=UTF-8

# Tornado modules.
import tornado.web

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
        elif self.get_argument("start_direct_auth", None):
            # Get form inputs.
            try:
                user = dict()
                user["email"] = self.get_argument("email", default="")
                user["name"] = self.get_argument("name", default="")
            except:
                # Send an error back to client.
                content = "<p>There was an input error. Fill in all fields!</p>"
                self.render_default("index.html", content=content)
            # If user has not filled in all fields.
            if not user["email"] or not user["name"]:
                content = ('<h2>2. Direct Login</h2>' 
                + '<p>Fill in both fields!</p>'
                + '<form class="form-inline" action="/login" method="get"> '
                + '<input type="hidden" name="start_direct_auth" value="1">'
                + '<input type="text" name="name" placeholder="Your Name" value="' + str(user["name"]) + '"> '
                + '<input type="text" name="email" placeholder="Your Email" value="' + str(user["email"]) + '"> '
                + '<input type="submit" class="btn" value="Sign in">'
                + '</form>')
                self.render_default("index.html", content=content)
            # All data given. Log user in!
            else:
                self._on_auth(user)
            
        else:
            # Logins.
            content = '<div class="page-header"><h1>Login</h1></div>'
            content += ('<h2>1. Google Login</h2>' 
            + '<form action="/login" method="get">' 
            + '<input type="hidden" name="start_google_oauth" value="1">'
            + '<input type="submit" class="btn" value="Sign in with Google">'
            + '</form>')
            content += ('<h2>2. Direct Login</h2>' 
            + '<form class="form-inline" action="/login" method="get"> '
            + '<input type="hidden" name="start_direct_auth" value="1">'
            + '<input type="text" name="name" placeholder="Your Name"> '
            + '<input type="text" name="email" placeholder="Your Email"> '
            + '<input type="submit" class="btn" value="Sign in">'
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
        dbuser = self.db.users.find_one({"email": user["email"]})
        if dbuser == None:
            # If user does not exist, create a new entry.
            self.db.users.insert(user)
        else:
            # Update existing user.
            # @todo: Should use $set to update only needed attributes?
            dbuser.update(user)
            user = dbuser
            self.db.users.save(user)
            
        # Save user id in cookie.
        user["_id"] = str(user["_id"])
        self.set_secure_cookie("user", user["_id"])
        self.redirect("/")
        


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect("/")
        
    
