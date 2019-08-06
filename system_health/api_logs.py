import pymongo
import requests
import time
import psycopg2
import datetime
from bson import ObjectId

import pprint

# cursor = collection.find({})
# for doc in cursor:
#     print(doc)
# inserted_document = collection.insert_one({'logs': []})
# doc_id = inserted_document.inserted_id
#
# collection.update_one({'_id': doc_id}, {"$push": {'logs': log_document}})
#
#
uri = "mongodb://health-dashboard-mongo:" \
      "2unhwWjCwN1KaLWRmBPRbrIu6yNmax5A2FlHycleFjH65pB9sTvYJrU9ihMeUIbA2hpJehgmwa0tJUgsQHB5zw" \
      "==@health-dashboard-mongo.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"

doc_id = "5d49785591ed6e2f4815a4de"


def check_response(response):
    response_time = str(response.elapsed.total_seconds())
    if response.status_code != 200:
        return False, response_time
    else:
        return True, response_time


def query_hazard_service(lat, lng, radius, url):
    try:
        response = requests.post(url + "/sfa_handler_safe",
                                 json={"lat": lat, "lng": lng, "radius": radius, "request_type": "point_safety"},
                                 timeout=10)
        return check_response(response)
    except (requests.Timeout, requests.ConnectionError):
        return False, 'TIMEOUT'


def query_database(query):
    prod_connection_string = "dbname='skywatch_prod' user='skywatch@skywatchdb-prod.postgres.database.azure.com' " \
                             "host='skywatchdb-prod.postgres.database.azure.com' password='SkyWatch1234'"

    conn = psycopg2.connect(
        prod_connection_string,
        sslmode='require')
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        response = cursor.fetchall()
        return response
    except:
        return None

def test_database():
    example_query = 'SELECT id FROM "Insurance"."insurance_policies" LIMIT 1'
    start_time = time.time()
    response = query_database(example_query)
    end_time = time.time()
    if response is not None:
        active = True
        response_time = round(end_time - start_time, 4)
    else:
        active = False
        response_time = 0
    return active, str(response_time)


def query_airmap():
    url = "https://api.airmap.com/aircraft/v2/manufacturer"
    headers = {
        'accept': "application/json",
        'x-api-key': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVkZW50aWFsX2lkIjoiY3JlZGVudGlhbHxLYTNrZ1B4RktReW1kZ2h5N3F2cEFzTUFKYTVnIiwiYXBwbGljYXRpb25faWQiOiJhcHBsaWNhdGlvbnxhWVlhNG1kSGQ0QmdPRkdwTGdiT0ZrTjAwWFAiLCJvcmdhbml6YXRpb25faWQiOiJkZXZlbG9wZXJ8UHlNTHkzWUZnM2IyTUtpeUVsYldic1FnbUw0RCIsImlhdCI6MTUxOTU4MTQ4OX0.rnz4zjKkyO9dzDW5S8bhkIOjwRPLuoUaXT0kqNcHgzo"
    }
    try:
        response = requests.request("GET", url, headers=headers, timeout=10)
    except (requests.Timeout, requests.ConnectionError):
        return False, 'Timeout'

    return check_response(response)


def query_skywatch_api():
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
        # "start_time": 9651096405567
        "start_time": 9651096
    }
    try:
        response = response = requests.post(skywatch_api, json=data_to_input, timeout=10)
    except (requests.Timeout, requests.ConnectionError):
        return False, 'Timeout'
    return check_response(response)


def add_api_data(dictionary, errors, api_name, active, rt):
    if not active:
        errors['{}.errors'.format(api_name)] = {'timestamp': datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                                                'response_time': rt}
    dictionary['{}.most_recent_log'.format(api_name)] = {'active': active,
                                                         'response_time': rt}


def add_timestamp(dic):
    dic['timestamp'] = datetime.datetime.today().strftime("%H:%M:%S")


def update_recent_log(most_recent, errors):
    hazard_active, hazard_rt = query_hazard_service(40.791859, -84.434, 30, 'http://hazards.skywatch.ai')
    skywatch_active, skywatch_rt = query_skywatch_api()
    airmap_active, airmap_rt = query_airmap()
    db_active, db_rt = test_database()
    add_api_data(most_recent, errors, 'hazard_api', hazard_active, hazard_rt)
    add_api_data(most_recent, errors, 'skywatch_api', skywatch_active, skywatch_rt)
    add_api_data(most_recent, errors, 'airmap_api', airmap_active, airmap_rt)
    add_api_data(most_recent, errors, 'Database', db_active, db_rt)
    add_timestamp(most_recent)


def insert_into_db(most_recent, errors):
    connection = pymongo.MongoClient(uri)
    db = connection['MyDatabase']
    collection = db['API_Logs']
    collection.update_one({'_id': ObjectId(doc_id)}, {"$set": most_recent})
    collection.update_one({'_id': ObjectId(doc_id)}, {"$push": errors})


if __name__ == '__main__':
    most_recent_data = {}
    api_errors = {}
    update_recent_log(most_recent_data, api_errors)
    print(most_recent_data)
    print(api_errors)
    insert_into_db(most_recent_data, api_errors)



