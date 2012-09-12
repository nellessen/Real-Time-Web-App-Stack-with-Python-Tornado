# coding=UTF-8

# General modules.
import os.path
import logging
import sys

# Tornado modules.
import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.options
import tornado.escape

# MongoDb modules.
from bson.objectid import ObjectId

# Redis modules.
import brukva

# Import application modules.
from base import BaseHandler
from auth import LoginHandler
from auth import LogoutHandler

# Define port from command line parameter.
tornado.options.define("port", default=8888, help="run on the given port", type=int)



class MainHandler(BaseHandler):
    """
    Main request handler for the root path.
    """
    @tornado.web.asynchronous
    def get(self):
        # Get the current user.
        self._get_current_user(callback=self.on_auth)
        
    
    def on_auth(self, user):
        if not user:
            self.redirect("/login")
            return
        # Retreive 50 latest messages.
        self.application.client.lrange('conversation', -50, -1, 
                                       self.on_conversation_find)
        
    
    def on_conversation_find(self, result):
        """
        The callback for querying the latest messages in self.on_auth().
        """
        if isinstance(result, Exception):
            raise tornado.web.HTTPError(500)
        # JSON-decode messages.
        messages = []
        for message in result:
            messages.append(tornado.escape.json_decode(message))
        
        content = self.render_string("messages.html", 
                        messages=messages)
        self.render_default("index.html", content=content, chat=1)
        
    

class MessageHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        """
        Handles get requests for long polling.
        Expects to send a body like this:
        {'cursor': 'MessageID of the latest message received'}
        """
        # Check authentication.
        self._get_current_user(callback=self.get_on_auth)
        
    
    def get_on_auth(self, user):
        """
        Callback fot checking auth in self.get().
        """
        if not user:
            self.finish({'error': 1, 'textStatus': 'unauthorized'})
            return;
        
        # Subscribe to conversation channel.
        self.client = brukva.Client()
        self.client.connect()
        self.client.subscribe('conversation')
        self.client.listen(self.on_new_messages)
        
        # @todo: We could check if we missed a message between pollings.
        
        
    def on_new_messages(self, message):
        """
        Callback called by get() when new message is available.
        message - a new message.
        """
        # Remove waiter.
        logging.info("Removed one waiter")
        self.client.unsubscribe('conversation')
        self.client.disconnect()
        # Closed client connection
        if self.request.connection.stream.closed():
            logging.warning("Waiter disappeared")
            return
        # Send messages to client and finish connection.
        self.finish(dict(messages=[tornado.escape.json_decode(message.body)]))
        

    def on_connection_close(self):
        """
        Called when connection closed.
        """
        # Remove waiter.
        logging.info("Removed one waiter")
        self.client.unsubscribe('conversation')
        self.client.disconnect()
        
    
    @tornado.web.asynchronous
    def post(self):
        """
        Handles post request for creating new posts.
        Expects to send a body like this:
        {'body': 'Message body...'}
        """
        # Check authentication.
        self._get_current_user(callback=self.post_on_auth)
        
    
    def post_on_auth(self, user):
        """
        Callback fot checking auth in self.post().
        """
        if not user:
            self.finish({'error': 1, 'textStatus': 'unauthorized'})
            return;
        
        # get message data from request body.
        try:
            # create new message.
            message = dict()
            message['from'] = user['name']
            #message['id'] = str(uuid.uuid4())
            # @todo: Validate input.
            message['body'] = tornado.escape.linkify(self.get_argument("body"))
            # Uncomment this line to add the port number to the body.
            message['body'] += " (over port " + str(tornado.options.options.port) + ")"
        except:
            # Send an error back to client.
            self.finish({'error': 1, 'textStatus': 'Bad input data'})
            return;
        
        # Save message.
        try:
            # Generate object id as message id.
            message["_id"] = str(ObjectId())
            # Convert to JSON-literal.
            message_encoded = tornado.escape.json_encode(message)
            # Persistently store message.
            self.application.client.rpush('conversation', message_encoded)
            # publish message.
            self.application.client.publish('conversation', message_encoded)
        except Exception, err:
            e = str(sys.exc_info()[0])
            # Send an error back to client.
            self.finish({'error': 1, 'textStatus': 'Error writing to database: ' + str(err)})
            return;
        
        # Send message to indicate a successful operation.
        self.finish(message)
        return;
    


class Application(tornado.web.Application):
    """
    Main Class for this application holding everything together.
    """
    def __init__(self):
        
        # Handlers defining the url routing.
        handlers = [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/message", MessageHandler),
        ]
        
        # Settings:
        settings = dict(
            cookie_secret = "43osdETzKXasdQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url = "/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies= True,
            autoescape="xhtml_escape",
            # Set this to your desired database name.
            db_name = 'chat',
            # apptitle used as page title in the template.
            apptitle = 'Chat example: Tornado, Redis, brukva, Longpolling'
        )
        
        # Call super constructor.
        tornado.web.Application.__init__(self, handlers, **settings)
        
        """
        We create a database connection using brukva, which is a 
        non-blocking, asynchronous driver for redis.
        """
        # Connect to redis.
        self.client = brukva.Client()
        self.client.connect()
        


def main():
    """
    Main function to run the chat application.
    """
     # This line will setup default options.
    tornado.options.parse_command_line()
    # Create an instance of the main application.
    application = Application()
    # Start application by listening to desired port and starting IOLoop.
    application.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()
    

if __name__ == "__main__":
    main()