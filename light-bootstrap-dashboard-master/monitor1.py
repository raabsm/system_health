import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import datetime
import requests
import json
from dateutil.relativedelta import relativedelta
import DBConnection
# import zlib
# import pybase64
import time
import pytz
import elasticlogs

tornado.options.define('port', default=8889, help='port to listen on')


def format_number(entry):
    return "{:,}".format(round(entry))


def format_time(time):
    utc_time = pytz.utc.localize(time)
    israel_timezone = pytz.timezone('Israel')
    israel = utc_time.astimezone(israel_timezone)
    return israel.strftime("%H:%M")


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
        data = {'total_profiles': format_number(query_database_single_response(total_profiles_query)),
                'most_recently_added': format_time(query_database_single_response(last_profile_added)),
                'total_last_week': format_number(query_database_single_response(profiles_last_week_query))}
        self.write(data)


class GraphHandler(tornado.web.RequestHandler):
    def get(self):
        self.graph_data = {'graphs': {'profiles_last_week': {'title': 'Daily Profile Increase',
                                                             'key': {'x': 'Date',
                                                                     'y1': 'Registered',
                                                                     'y2': 'Filled address info',
                                                                     'y3': 'Filled card info'
                                                                     },
                                                             'data': []
                                                             },
                                      'revenue_last_week': {'title': 'Daily Revenue',
                                                            'key': {'x': 'Date',
                                                                    'y1': 'Revenue'
                                                                    },
                                                            'data': []
                                                            },
                                      'revenue_last_month': {'title': 'Monthly Revenue',
                                                             'key': {'x': 'Month',
                                                                     'y1': 'Revenue'
                                                                     },
                                                             'data': []
                                                             },
                                      'policies_last_week': {'title': 'Daily Policy Count',
                                                             'key': {'x': 'Day',
                                                                     'y1': 'On Demand',
                                                                     'y2': 'Monthly'
                                                                     },
                                                             'data': []
                                                             }
                                      }
                           }
        profiles_last_week_query = 'SELECT count(profiles.id), count(addresses.address1), count(profiles.stripe_customer_id)' \
                                   'FROM "User"."profiles" profiles ' \
                                   'INNER JOIN "User"."addresses" addresses ON (profiles.id = addresses.user_profile_id) ' \
                                   'WHERE profiles.date_added > \'{0}\' AND profiles.date_added < \'{1}\''
        revenue_last_week_query = 'SELECT SUM(final_price) FROM "Insurance"."insurance_purchases" purchases ' \
                                  'WHERE purchases.date_added > \'{0}\' AND purchases.date_added < \'{1}\''
        revenue_last_month_query = revenue_last_week_query
        policies_last_week_query = 'SELECT count(id), (count(id) - count(covered_airspace)) ' \
                                   'FROM "Insurance"."insurance_purchases" ' \
                                   'WHERE date_added > \'{0}\' AND date_added < \'{1}\''

        self.fill_graph('profiles_last_week', "%m/%d", profiles_last_week_query, y_vals=3)
        self.fill_graph('revenue_last_week', "%m/%d", revenue_last_week_query)
        self.fill_graph('revenue_last_month', "%b", revenue_last_month_query, days=False)
        self.fill_graph('policies_last_week', "%m/%d", policies_last_week_query, y_vals=2)
        self.write(self.graph_data)

    def fill_graph(self, graph_name, formatted_date, query, days=True, y_vals=1):
        today = datetime.datetime.today()
        for num in range(0, 7):
            if days:
                day = (today - relativedelta(days=num + 1))
                next_day = day + datetime.timedelta(days=1)
            else:
                day = (today - relativedelta(months=num + 1, day=1))
                next_day = day + relativedelta(months=1, day=1)
            db_query = query.format(day.strftime("%Y-%m-%d"), next_day.strftime("%Y-%m-%d"))
            response = query_database_all_responses(db_query)[0]
            if y_vals == 3:
                self.graph_data['graphs'][graph_name]['data'].append({'x': day.strftime(formatted_date),
                                                                      'y1': response[0],
                                                                      'y2': response[1],
                                                                      'y3': response[2]})
            elif y_vals == 2:
                self.graph_data['graphs'][graph_name]['data'].append({'x': day.strftime(formatted_date),
                                                                      'y1': response[0],
                                                                      'y2': response[1]})
            else:
                self.graph_data['graphs'][graph_name]['data'].append({'x': day.strftime(formatted_date),
                                                                      'y1': response[0]})


class PoliciesHandler(tornado.web.RequestHandler):
    def get(self):
        total_policies_query = 'SELECT COUNT(id) FROM "Insurance"."insurance_purchases"' \
                               'WHERE is_canceled = false'
        most_recent_policy_query = 'SELECT date_added FROM "Insurance"."insurance_purchases" ORDER BY date_added DESC LIMIT 1'
        self.write({'total_policies': format_number(query_database_single_response(total_policies_query)),
                    'most_recently_added': format_time(query_database_single_response(most_recent_policy_query))})


class RevenueHandler(tornado.web.RequestHandler):
    def get(self):
        currency = "$"
        total_revenue_query = 'SELECT SUM(final_price) FROM "Insurance"."insurance_purchases"'
        most_recent_policy_query = 'SELECT date_added FROM "Insurance"."insurance_purchases" ORDER BY date_added DESC'
        today = datetime.datetime.today()
        revenue_today = total_revenue_query + ' WHERE date_added > \'{}\''.format(today.strftime("%Y-%m-%d"))
        self.write({'total_revenue': currency + format_number(query_database_single_response(total_revenue_query)),
                    'revenue_today': currency + format_number(query_database_single_response(revenue_today)),
                    'most_recently_added': format_time(query_database_single_response(most_recent_policy_query))})


class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        data = {'api': []}
        hazard_response = self.query_hazard_service(40.791859, -84.434, 30, 'http://hazards.skywatch.ai')
        skywatch_response = self.query_skywatch_api()
        airmap_response = self.query_airmap()
        add_api_data(data, 'hazard_api', hazard_response)
        add_api_data(data, 'skywatch_api', skywatch_response)
        add_api_data(data, 'airmap_api', airmap_response)
        self.test_database(data)
        self.write(data)

    def query_hazard_service(self, lat, lng, radius, url):
        response = requests.post(url + "/sfa_handler_safe",
                                 json={"lat": lat, "lng": lng, "radius": radius, "request_type": "point_safety"})
        return response
        # return zlib.decompress(pybase64.standard_b64decode(json.loads(requests.post(url + "/sfa_handler_safe",
        #                 json={"lat": lat, "lng": lng, "radius": radius, "request_type": "point_safety"}).content)['data']))

    def test_database(self, dictionary):
        example_query = 'SELECT id FROM "Insurance"."insurance_policies" LIMIT 1'
        start_time = time.time()
        response = query_database_single_response(example_query)
        end_time = time.time()
        if response is not None:
            active = True
            response_time = round(end_time - start_time, 4)
        else:
            active = False
            response_time = 0
        dictionary['api'].append({'name': 'Database', 'info': {'active': active,
                                                               'response_time': str(response_time)}})
        return dictionary

    def query_airmap(self):
        url = "https://api.airmap.com/aircraft/v2/manufacturer"
        headers = {
            'accept': "application/json",
            'x-api-key': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVkZW50aWFsX2lkIjoiY3JlZGVudGlhbHxLYTNrZ1B4RktReW1kZ2h5N3F2cEFzTUFKYTVnIiwiYXBwbGljYXRpb25faWQiOiJhcHBsaWNhdGlvbnxhWVlhNG1kSGQ0QmdPRkdwTGdiT0ZrTjAwWFAiLCJvcmdhbml6YXRpb25faWQiOiJkZXZlbG9wZXJ8UHlNTHkzWUZnM2IyTUtpeUVsYldic1FnbUw0RCIsImlhdCI6MTUxOTU4MTQ4OX0.rnz4zjKkyO9dzDW5S8bhkIOjwRPLuoUaXT0kqNcHgzo"
        }
        response = requests.request("GET", url, headers=headers)
        return response

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
            "start_time": 96510964051541
        }
        response = requests.post(skywatch_api, json=data_to_input)
        return response


class ErrorLogsHandler(tornado.web.RequestHandler):
    def get(self):
        count_last_day = elasticlogs.count_last_24_hours()
        count_last_month = elasticlogs.count_last_month()
        count_last_week = elasticlogs.count_last_7_days()
        most_recent_logs = elasticlogs.most_recent_logs()
        self.write({'count_last_day': count_last_day,
                    'count_last_week': count_last_week,
                    'count_last_month': count_last_month,
                    'most_recent_logs': most_recent_logs})


# launch url according to input path
def application():
    try:
        urls = [(r"/", jsHandler),
                (r"/profiles", ProfilesHandler),
                (r"/policies", PoliciesHandler),
                (r"/revenue", RevenueHandler),
                (r"/api", ApiHandler),
                (r"/graphs", GraphHandler),
                (r"/errors", ErrorLogsHandler),
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
