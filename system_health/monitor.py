import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import datetime
import pymongo
from bson import ObjectId
from dateutil.relativedelta import relativedelta
import DBConnection
import pytz
import elasticlogs

tornado.options.define('port', default=8888, help='port to listen on')

currency = "$"

uri = "mongodb://health-dashboard-mongo:" \
      "2unhwWjCwN1KaLWRmBPRbrIu6yNmax5A2FlHycleFjH65pB9sTvYJrU9ihMeUIbA2hpJehgmwa0tJUgsQHB5zw" \
      "==@health-dashboard-mongo.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"

connection = pymongo.MongoClient(uri)
mongo_db = connection['MyDatabase']
doc_id = "5d49785591ed6e2f4815a4de"


def format_number(entry):
    if entry is None:
        return '0'
    return "{:,}".format(round(entry))


def format_time(time):
    if time is not None:
        utc_time = pytz.utc.localize(time)
        israel_timezone = pytz.timezone('Israel')
        israel = utc_time.astimezone(israel_timezone)
        return israel.strftime("%H:%M")
    else:
        return "Time not available"


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


def add_api_data(dictionary, api_name, active, rt):
    if not active:
        global api_errors
        api_errors.append({api_name:datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")})
    dictionary['api'].append({'name': api_name, 'info': {'active': active,
                                                         'response_time': rt}})
    return dictionary


def check_response(response):
    response_time = str(response.elapsed.total_seconds())
    if response.status_code != 200:
        return False, response_time
    else:
        return True, response_time


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
        filled_address_and_card = 'SELECT count(addresses.address1), count(profiles.stripe_customer_id) ' \
                                  'FROM "User"."profiles" profiles INNER JOIN "User"."addresses" addresses ' \
                                  'ON (profiles.id = addresses.user_profile_id)'
        today = datetime.datetime.today()
        last_week = (today - datetime.timedelta(days=7))
        profiles_last_week_query = total_profiles_query \
                                   + ' WHERE date_added > \'{0}\''.format(last_week.strftime("%Y-%m-%d"))
        num_filled_address, num_filled_card = query_database_all_responses(filled_address_and_card)[0]

        data = {'total_profiles': format_number(query_database_single_response(total_profiles_query)),
                'most_recently_added': format_time(query_database_single_response(last_profile_added)),
                'total_last_week': format_number(query_database_single_response(profiles_last_week_query)),
                'total_address': format_number(num_filled_address),
                'total_card': format_number(num_filled_card)}
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
                                      'revenue_last_month': {'title': 'Monthly Revenue ' + currency,
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
                day = (today - relativedelta(days=num))
                next_day = day + datetime.timedelta(days=1)
            else:
                day = (today - relativedelta(months=num, day=1))
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
        most_recent_policy_query = 'SELECT date_added FROM "Insurance"."insurance_purchases" ORDER BY ' \
                                   'date_added DESC LIMIT 1'
        self.write({'total_policies': format_number(query_database_single_response(total_policies_query)),
                    'most_recently_added': format_time(query_database_single_response(most_recent_policy_query))})


class RevenueHandler(tornado.web.RequestHandler):
    def get(self):
        total_revenue_query = 'SELECT SUM(final_price) FROM "Insurance"."insurance_purchases"'
        most_recent_policy_query = 'SELECT date_added FROM "Insurance"."insurance_purchases" ORDER BY date_added DESC LIMIT 1'
        today = datetime.datetime.today()
        revenue_today = total_revenue_query + ' WHERE date_added > \'{}\''.format(today.strftime("%Y-%m-%d"))
        self.write({'total_revenue': currency + format_number(query_database_single_response(total_revenue_query)),
                    'revenue_today': currency + format_number(query_database_single_response(revenue_today)),
                    'most_recently_added': format_time(query_database_single_response(most_recent_policy_query))})


class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        collection = mongo_db['API_Logs']
        api_logs = collection.find_one({'_id': ObjectId(doc_id)})
        del api_logs['_id']
        self.write(api_logs)
        

class ErrorLogsHandler(tornado.web.RequestHandler):
    def get(self):
        query = "Level = Error, level = Error"
        count_last_day = elasticlogs.elastic_day(query)
        count_last_week = elasticlogs.elastic_week(query)
        count_last_month = elasticlogs.elastic_month(query)
        most_recent_logs = elasticlogs.most_recent_logs(query)
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
                (r"/assets/img/(.*)", tornado.web.StaticFileHandler, {"path": "./assets/img"},),
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
