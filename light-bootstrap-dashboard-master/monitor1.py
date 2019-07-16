import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import datetime
import requests
import json
import logging
from pymongo import MongoClient


tornado.options.define('port', default=8888, help='port to listen on')

# Create a logging instance // https://do

# return an object containing info for each widget
def widget_properties(name, url):
    try:
        string = []
        request = requests.get(url)
        r = json.loads(request.text)
        responsetime = "Response time: " + str(round(request.elapsed.total_seconds(), 2)) + "s"
        stamp = "Query: " + str(datetime.datetime.now())
        # string.extend(widget_specs(name, r, datetime.datetime.now(), round(request.elapsed.total_seconds(), 2)))
        string.extend((responsetime, stamp))
        return {name: {url: string}}
    except:
        print("Couldn't get widget properties")


# call required function based on input name
# def widget_specs(name, r, stamp, response_time):
#     if name == "widget1":
#         topost.insert_one({"widget1": {"stamp": stamp, "responsetime": response_time}})
#         return weather_widget(r)
#     elif name == "catfacts":
#         topost.insert_one({"catfacts": {"stamp": stamp, "responsetime": response_time}})
#         return cat_facts(r)
#     elif name == "quote":
#         topost.insert_one({"quote": {"stamp": stamp, "responsetime": response_time}})
#         return quote(r)


# render the page; let jQuery do the work
class jsHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            self.render("examples/dashboard.html")
        except Exception as e:
            print(e.message, "Could not render the page")


# renders the JSON file at the url on a local page
class infoHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(""" retrive and display all the required data """)


# launch url according to input path
def application():
    try:
        urls = [(r"/", jsHandler),
                (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "./assets"},),
                (r"/style/(.*)", tornado.web.StaticFileHandler, {"path": "./style"},)]
        return tornado.web.Application(urls, debug=True)
    except:
        print("Application not working")


if __name__ == "__main__":
    app = application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(tornado.options.options.port)
    print("Success; listening on http://localhost:%i" % tornado.options.options.port)
    tornado.ioloop.IOLoop.current().start()
