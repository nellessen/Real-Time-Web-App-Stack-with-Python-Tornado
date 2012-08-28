# coding=UTF-8
import tornado.web

# Tornado modules.
import tornado.web

# MongoDb modules.
import pymongo
from bson.objectid import ObjectId


class BaseHandler(tornado.web.RequestHandler):
    """
    A base request Handler providing user authentication and exposing database.
    I also provides a render_default() method which passes arguments to render()
    with additional default arguments for the menu, user...
    """
    def __init__(self, application, request, **kwargs):
        # Expose database as instance attribute.
        self.db = application.db
        # Call super constructor.
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        
    def get_current_user(self):
        """
        Returns the user object of the current session or None for anonymous.
        """
        user_id = self.get_secure_cookie("user")
        if not user_id: return None
        # Load json based on cookie data.
        user = self.db.users.find_one({'_id': ObjectId(user_id)})
        return user
    
    def render_default(self, template_name, **kwargs):
        # Set default variables and render template.
        kwargs['user'] = self.current_user
        self.render(template_name,
                    apptitle=self.application.settings['apptitle'], **kwargs)