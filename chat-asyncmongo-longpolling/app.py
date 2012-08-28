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
import pymongo
import asyncmongo
from bson.objectid import ObjectId

# Import application modules.
from base import BaseHandler
from auth import LoginHandler
from auth import LogoutHandler



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
        # Retreive messages.
        self.db.conversation.find(callback=self.on_conversation_find)
        
    
    def on_conversation_find(self, response, error):
        """
        The callback for querying the latest messages in self.on_auth().
        """
        if error:
            raise tornado.web.HTTPError(500)
        content = self.render_string("messages.html", 
                        messages=list(response))
        self.render_default("index.html", content=content, chat=1)
        
    

class MessageHandler(BaseHandler):
    waiters = set()

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
        
        # Check if there are new messages.
        # @todo: Bad, bad performance loading all items each request!
        self.db.conversation.find(callback=self.on_conversation_find)
        
    
    def on_conversation_find(self, response, error):
        """
        Callback for loading messages in self.get_on_auth().
        """
        if error:
            raise tornado.web.HTTPError(500)
        
        # get message data from request body.
        try:
            # Get cursor form request body.
            cursor = self.get_argument("cursor", None)
        except:
            # Send an error back to client.
            self.finish({'error': 1, 'textStatus': 'Bad input data'})
            return;
        
        messages = list(response)
        # Stringify _id.
        for i in xrange(len(messages)):
            messages[i]["_id"] = str(messages[i]["_id"])
        
        # Find current message.
        if cursor:
            index = 0
            for i in xrange(len(messages)):
                index = len(messages) - i - 1
                if messages[index]["_id"] == cursor: break
            recent = messages[index + 1:]
            if recent:
                self.on_new_messages(recent)
                return
        MessageHandler.waiters.add(self.on_new_messages)
        
        
    def on_new_messages(self, messages):
        """
        Callback called by get() when new message is available.
        messages - a list of message object that are new to the waiter.
        """
        # Closed client connection
        if self.request.connection.stream.closed():
            logging.warning("Waiter disappeared")
            return
        # Send messages to client and finish connection.
        self.finish(dict(messages=messages))

    def on_connection_close(self):
        """
        Called when connection closed.
        """
        # Remove waiter.
        MessageHandler.waiters.discard(self.on_new_messages)
        logging.info("Removed one waiter")
        
    
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
        except:
            # Send an error back to client.
            self.finish({'error': 1, 'textStatus': 'Bad input data'})
            return;
        
        # Save message.
        try:
            # Generate object id because asyncmongo does not return it.
            message["_id"] = ObjectId()
            self.db.conversation.insert(message,
                                        callback=self.on_conversation_insert)
            # Stringify _id.
            message["_id"] = str(message["_id"])
        except Exception, err:
            e = str(sys.exc_info()[0])
            # Send an error back to client.
            self.finish({'error': 1, 'textStatus': 'Error writing to database: ' + str(err)})
            return;
        
        # Inform waiters about new message.
        # Waiters are stored in a class attribute.
        for waiter in MessageHandler.waiters:
            try: # Send message to waiter.
                waiter(messages=[message])
            except:
                logging.error("Error in waiter callback", exc_info=True)
        # Reset cache. 
        MessageHandler.waiters = set()
        
        # Send message to indicate a successful operation.
        message['_id'] = str(message['_id']) # Stringify id.
        self.finish(message)
        return;
    
    
    def on_conversation_insert(self, response, error):
        """
        Callback for inserting messages into the conversation in self.post.
        """
        if error:
            logging.error("Error writing to database", exc_info=True)
            return
        else:
            logging.info("Inserted message")
    


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
            apptitle = 'Chat example: Tornado, MongoDB, asyncmongo, Longpolling'
        )
        
        # Call super constructor.
        tornado.web.Application.__init__(self, handlers, **settings)
        
        """
        We create a database connection using asyncmongo, which is a 
        non-blocking, asynchronous driver.
        """
        # Configure your MongoDB connection.
        self.db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1',
                    port=27017, maxcached=10, maxconnections=50, dbname='chat')
        # Create collection 'conversation' manually to make it a fixed size
        # capped collection with the natural order being the one order of
        # insertion. We do this using the synchronous, blocking driver pymongo.
        
        # Configure your MongoDB connection.
        sync_connection = pymongo.Connection('localhost', 27017)
        # Choose your database for this application.
        self.sync_db = sync_connection['chat']
        # Create collection 'conversation' manually to make it a fixed size
        # capped collection with the natural order being the one order of
        # insertion.
        if not "conversation" in self.sync_db.collection_names():
            logging.info("Creating capped collection 'conversation'")
            pymongo.collection.Collection(self.sync_db, "conversation",
                                  create=True, capped=True, size=20480, max=50)
        



def main():
    """
    Main function to run the chat application.
    """
     # This line will setup default options.
    tornado.options.parse_command_line()
    # Create an instance of the main application.
    application = Application()
    # Start application by listening to desired port and starting IOLoop.
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    

if __name__ == "__main__":
    main()