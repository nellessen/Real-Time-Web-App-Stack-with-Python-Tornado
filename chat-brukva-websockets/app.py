# coding=UTF-8

# General modules.
import os.path
import logging
import sys
from threading import Timer

# Tornado modules.
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.auth
import tornado.options
import tornado.escape
from tornado import gen

# MongoDb modules.
from bson.objectid import ObjectId

# Redis modules.
import brukva

# Import application modules.
from base import BaseHandler
from auth import LoginHandler
from auth import LogoutHandler
from symbol import except_clause

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

        
        


class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Handler for dealing with websockets.
    @todo: No authentication yet!
    """

    @gen.engine
    def open(self):
        """
        Called when socket is opened. Used to subscribe to conversation.
        """
        # Subscribe to conversation channel.
        self.new_message_send = False
        self.client = brukva.Client()
        self.client.connect()
        self.client.subscribe('conversation')
        self.subscribed = True
        self.client.listen(self.on_new_messages)
        
    
    def on_new_messages(self, message):
        """
        Callback for listening to subscription 'conversation'
        """
        logging.info("on_new_messages")
        # Aboart if message type is something like unsubscribe.
        if not message.kind == "message":
            return;
        # Send messages to client and finish connection.
        self.write_message(dict(messages=[tornado.escape.json_decode(message.body)]))
        
    
    def on_close(self):
        """
        Callback when socket is closed
        """
        self.cleanup()
        
    
    def cleanup(self):
        """
        Frees up resource related to this socket.
        """
        # Cleanup database connection.
        logging.info("CLEANUP")
        if hasattr(self, 'client'):
            # Unsubscribe if not done yet.
            if self.subscribed:
                self.client.unsubscribe('conversation')
                self.subscribed = False
            # Disconnect connection after delay due to this issue:
            # https://github.com/evilkost/brukva/issues/25 
            t = Timer(0.1, self.client.disconnect)
            t.start()
        
    
    def on_message(self, data):
        """
        Callback when new message received from socket.
        """
        logging.info('Got message %r', data)
        
        # get message data.
        try:
            # Parse input.
            datadecoded = tornado.escape.json_decode(data)
            # create new message.
            message = dict()
            # @todo: Set username after implementation of authentication.
            message['from'] = "TODO"
            messagebody = datadecoded["body"]
            message['body'] = tornado.escape.linkify(messagebody)
        except Exception, err:
            # Send an error back to client.
            self.write_message({'error': 1, 'textStatus': 'Bad input data ... ' + str(err) + data})
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
            self.write_message({'error': 1, 'textStatus': 'Error writing to database: ' + str(err)})
            return;
        
        # Send message to indicate a successful operation.
        self.write_message(message)
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
            (r"/socket", ChatSocketHandler),
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
            apptitle = 'Chat example: Tornado, Redis, brukva, Websockets'
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