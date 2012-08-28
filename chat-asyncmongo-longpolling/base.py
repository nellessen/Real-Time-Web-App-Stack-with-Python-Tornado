# coding=UTF-8
import tornado.web

# Tornado modules.
import tornado.web

# MongoDb modules.
import asyncmongo
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
        self.sync_db = application.sync_db
        # Call super constructor.
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        
    def _get_current_user(self, callback):
        """
        An async method to retreive current user object.
        The callback  function will receive the current user object or None
        as a parameter 'user'.
        """
        # Get the user_id by cookie.
        user_id = self.get_secure_cookie("user")
        if not user_id:
            callback(user=None)
            return
        # Define a callback for the db query.
        def query_callback(response, error):
            if error:
                raise tornado.web.HTTPError(500)
            else:
                self._current_user = response
                callback(user=response)
            
        # Load user object and pass query_callback as callback.
        self.db.users.find_one({'_id': ObjectId(user_id)}, callback=query_callback)
        return
    
    def render_default(self, template_name, **kwargs):
        # Set default variables and render template.
        if not hasattr(self, '_current_user'):
            self._current_user = None
        kwargs['user'] = self._current_user
        self.render(template_name,
                    apptitle=self.application.settings['apptitle'], **kwargs)
    
