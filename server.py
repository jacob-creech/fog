import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import Steam_Rec as recommender
import SteamValues as steamval

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket opened"

    def on_message(self, message):
        print type(message)
        game_list = recommender.main(message)
        self.write_message(game_list)
        #self.write_message(u"You said: " + message)


    def on_close(self):
        print "WebSocket closed"

    def check_origin(self, origin):
        return True

application = tornado.web.Application([
    (r"/websocket", EchoWebSocket),
    (r"/", MainHandler),
])

if __name__ == "__main__":
    #steamval.main()
    steamval.read_from_files()
    print "Done reading files"
    application.listen(10096)
    tornado.ioloop.IOLoop.instance().start()
