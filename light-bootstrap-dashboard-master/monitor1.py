import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import datetime
import requests
import json
import DBConnection
# import zlib
# import pybase64
import time


tornado.options.define('port', default=8889, help='port to listen on')


# return an object containing info for each widget
# def widget_properties(name, url):
#     try:
#         string = []
#         request = requests.get(url)
#         r = json.loads(request.text)
#         responsetime = "Response time: " + str(round(request.elapsed.total_seconds(), 2)) + "s"
#         stamp = "Query: " + str(datetime.datetime.now())
#         # string.extend(widget_specs(name, r, datetime.datetime.now(), round(request.elapsed.total_seconds(), 2)))
#         string.extend((responsetime, stamp))
#         return {name: {url: string}}
#     except:
#         print("Couldn't get widget properties")


def query_database_single_response(query):
    response = DBConnection.get_all_responses(query)
    if response is None:
        return None
    return response[0][0]


def query_database_all_responses(query):
    response = DBConnection.get_all_responses(query)
    if response is None:
        return None
    return response


def add_api_data(dictionary, api_name, response):
    if response.status_code != 200:
        active = False
    else:
        active = True
    response_time = str(response.elapsed.total_seconds())
    # print(type(response.elapsed))
    dictionary['api'].append({'name': api_name, 'info': {'active': active,
                             'response_time': response_time}})
    return dictionary


class DBError(Exception):
    pass


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
        data = {'total_profiles': query_database_single_response(total_profiles_query),
                'most_recently_added': query_database_single_response(last_profile_added).strftime("%H:%M"),
                'total_last_week': query_database_single_response(profiles_last_week_query)}
        self.write(data)


class GraphHandler(tornado.web.RequestHandler):
    def get(self):
        graph_data = {'graphs': {'profiles_last_week': {'title': 'Profiles Last Week',
                                                   'data': []},
                            'revenue_last_week': {'title': 'Revenue Last Week',
                                                   'data': []}
                            }
                }
        today = datetime.datetime.today()
        for num in range(0, 7):
            day = (today - datetime.timedelta(days=num+1))
            next_day = day + datetime.timedelta(days=1)
            query = 'SELECT count(profiles.id), count(addresses.address1) ' \
                    'FROM "User"."profiles" profiles ' \
                    'INNER JOIN "User"."addresses" addresses ON (profiles.id = addresses.user_profile_id) ' \
                    'WHERE profiles.date_added > \'{0}\' AND profiles.date_added < \'{1}\''.format(day.strftime("%Y-%m-%d"),
                                                                                                   next_day.strftime("%Y-%m-%d"))
            response = query_database_all_responses(query)[0]
            graph_data['graphs']['profiles_last_week']['data'].append({'date': day.strftime("%m/%d"),
                                 'registered': response[0],
                                 'filled_profile': response[1]})

        for num in range(0, 7):
            day = (today - datetime.timedelta(days=num+1))
            next_day = day + datetime.timedelta(days=1)
            query = 'SELECT SUM(final_price) FROM "Insurance"."insurance_purchases" purchases ' \
                    'WHERE purchases.date_added > \'{0}\' AND purchases.date_added < \'{1}\''.format(day.strftime("%Y-%m-%d"),
                                                                                                   next_day.strftime("%Y-%m-%d"))
            response = query_database_all_responses(query)[0]
            graph_data['graphs']['revenue_last_week']['data'].append({'date': day.strftime("%m/%d"),
                                                                      'revenue': response[0]})
        print(graph_data)
        #self.write(graph_data)


class PoliciesHandler(tornado.web.RequestHandler):
    def get(self):
        total_policies_query = 'SELECT COUNT(id) FROM "Insurance"."insurance_policies"'
        self.write({'total_policies': query_database_single_response(total_policies_query)})


class RevenueHandler(tornado.web.RequestHandler):
    def get(self):
        currency = "$"
        total_revenue_query = 'SELECT SUM(final_price) FROM "Insurance"."insurance_purchases"'
        today = datetime.datetime.today()
        revenue_today = total_revenue_query + ' WHERE date_added > \'{}\''.format(today.strftime("%Y-%m-%d"))
        self.write({'total_revenue': currency + str(round(query_database_single_response(total_revenue_query))),
                    'revenue_today': currency + str(round(query_database_single_response(revenue_today)))})


class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        data = {'api':[]}
        hazard_response = self.query_hazard_service(40.791859, -84.434, 30, 'http://hazards.skywatch.ai')
        skywatch_response = self.query_skywatch_api()
        add_api_data(data, 'hazard_api', hazard_response)
        add_api_data(data, 'skywatch_api', skywatch_response)
        self.test_database(data)
        self.write(data)

    def query_hazard_service(self, lat, lng, radius, url):
        response = requests.post(url + "/sfa_handler_safe",
                        json={"lat": lat, "lng": lng, "radius": radius, "request_type": "point_safety"})
        return response
        # return zlib.decompress(pybase64.standard_b64decode(json.loads(requests.post(url + "/sfa_handler_safe",
        #                 json={"lat": lat, "lng": lng, "radius": radius, "request_type": "point_safety"}).content)['data']))

    def test_database(self, dictionary):
        example_query = 'SELECT id FROM "Insurance"."insurance_policies"'
        start_time = time.time()
        response = query_database_single_response(example_query)
        end_time = time.time()
        if response is not None:
            active = True
            response_time = round(end_time-start_time, 4)
        else:
            active = False
            response_time = 0
        dictionary['api'].append({'name': 'DataBase', 'info': {'active': active,
                                  'response_time': str(response_time)}})
        return dictionary


    def query_skywatch_api(self):
        skywatch_api = 'http://api.us-dev.skywatch.ai/api/insurances/offers'
        data_to_input = {
            "airspace": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -6.86370849656,
                                52.35211857272093
                            ],
                            [
                                -6.847229003543,
                                52.3336607715546
                            ],
                            [
                                -6.84448245436,
                                52.35211857272093
                            ],
                            [
                                -6.8637084564544,
                                52.35211857272093
                            ],
                            [
                                -6.86370849656,
                                52.35211857272093
                            ]
                        ]
                    ]
                }
            },
            "start_time": 8563885267000
        }
        response = requests.post(skywatch_api, json=data_to_input)
        return response


# launch url according to input path
def application():
    try:
        urls = [(r"/", jsHandler),
                (r"/profiles", ProfilesHandler),
                (r"/policies", PoliciesHandler),
                (r"/revenue", RevenueHandler),
                (r"/api", ApiHandler),
                (r"/graphs", GraphHandler),
                (r"/assets/css/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/css"},),
                (r"/assets/js/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/js"},),
                (r"/assets/js/core/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/js/core"},),
                (r"/assets/js/plugins/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/js/plugins"},),
                (r"/assets/fonts/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/fonts"},)]
        return tornado.web.Application(urls, debug=True)
    except:
        print("Application not working")


if __name__ == "__main__":
    try:
        app = application()
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.listen(tornado.options.options.port)
        print("Success; listening on http://localhost:%i" % tornado.options.options.port)
        tornado.ioloop.IOLoop.current().start()
    except Exception as e:
        print(e)
