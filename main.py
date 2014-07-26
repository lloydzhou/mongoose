from handlers import BaseHandler, MongoRestHandler, GridfsHandler
import tornado.httpserver
import tornado.ioloop
from tornado.options import define, options
from pymongo import MongoClient
from pymongo.read_preferences import ReadPreference
import os

define("port", default=8889, help="run on the given port", type=int)
define("xorigin", default='*', help="xorigin", type=basestring)
define("hosts", default='localhost', help="hosts", type=basestring)
define("reps", default='', help="replicaSet", type=basestring)
define("tags", default='', help="tag set", type=basestring)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/([a-z0-9_]+)", BaseHandler, dict(xorigin=options.xorigin)),
            (r"/([a-z0-9_]+)/([a-z0-9_]+)",
             MongoRestHandler, dict(xorigin=options.xorigin)),
            (r"/gridfs/([a-z0-9_]+)/([a-z0-9_]+)", GridfsHandler),
            (r"/(.*)", tornado.web.StaticFileHandler,
             {'path': os.path.dirname(os.path.abspath(__file__))})
        ]
        tornado.web.Application.__init__(self, handlers)

        # Have one global connection to the blog DB across all handlers
        self.connection = None
        self.cursors = {}
        self._cursor_id = 0

        self._get_connection()

    def _get_connection(self):

        if not self.connection:
            try:
                settings = {
                    'socketTimeoutMS': 30000,
                    'connectTimeoutMS': 10000,
                    'read_preference': ReadPreference.SECONDARY_PREFERRED
                }
                if options.reps:
                    settings.replicaSet = options.reps
                    settings.tag_sets = options.tags and [
                        {'dc': options.tags}, {}] or [{}]

                self.connection = MongoClient(options.hosts, **settings)

            except:
                return None

        return self.connection


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    print "server started..."
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
