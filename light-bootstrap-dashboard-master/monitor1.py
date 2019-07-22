import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import datetime
import requests
import json
import DBConnection


tornado.options.define('port', default=8888, help='port to listen on')


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


def query_database(query):
    response = DBConnection.get_all_responses(query)
    return response[0][0]


# render the page; let jQuery do the work
class jsHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            self.render("dashboard.html")
        except Exception as e:
            print(e.message, "Could not render the page")


# renders the JSON file at the url on a local page
class ProfilesHandler(tornado.web.RequestHandler):
    def get(self):
        total_profiles_query = 'SELECT COUNT(id) FROM "User"."profiles"'
        last_profile_added = 'SELECT date_added FROM "User"."profiles" ORDER BY date_added DESC'
        today = datetime.datetime.today()
        last_week = (today - datetime.timedelta(days=7))
        profiles_last_week_query = total_profiles_query \
                             + ' WHERE date_added > \'{0}\''.format(last_week.strftime("%Y-%m-%d"))
        data = {'total_profiles': query_database(total_profiles_query),
                'most_recently_added': query_database(last_profile_added).strftime("%H-%M-%S"),
                'total_last_week': query_database(profiles_last_week_query)}
        self.write(data)


class PoliciesHandler(tornado.web.RequestHandler):
    def get(self):
        total_policies_query = 'SELECT COUNT(id) FROM "Insurance"."insurance_policies"'
        self.write({'total_policies': query_database(total_policies_query)})


class RevenueHandler(tornado.web.RequestHandler):
    def get(self):
        currency = "$"
        total_revenue_query = 'SELECT SUM(final_price) FROM "Insurance"."insurance_purchases"'
        today = datetime.datetime.today()
        revenue_today = total_revenue_query + ' WHERE date_added > \'{}\''.format(today.strftime("%Y-%m-%d"))
        self.write({'total_revenue': currency + str(round(query_database(total_revenue_query))),
                    'revenue_today': currency + str(round(query_database(revenue_today)))})


class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        skywatch_api = 'https://api.skywatch.ai/api/insurances/offers'
        response = requests.get(skywatch_api)
        print(response)


# launch url according to input path
def application():
    try:
        urls = [(r"/", jsHandler),
                (r"/profiles", ProfilesHandler),
                (r"/policies", PoliciesHandler),
                (r"/revenue", RevenueHandler),
                (r"/api", ApiHandler),
                (r"/assets/css/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/css"},),
                (r"/assets/js/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/js"},),
                (r"/assets/js/core/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/js/core"},),
                (r"/assets/js/plugins/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/js/plugins"},),
                (r"/assets/fonts/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/fonts"},)]
        return tornado.web.Application(urls, debug=True)
    except:
        print("Application not working")


if __name__ == "__main__":
    app = application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(tornado.options.options.port)
    print("Success; listening on http://localhost:%i" % tornado.options.options.port)
    tornado.ioloop.IOLoop.current().start()
