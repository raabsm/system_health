import pymongo
import requests
import time
import psycopg2
import datetime
from bson import ObjectId
import US_Constants as US_constants
import UK_Constants as UK_constants


def check_response(response):
    response_time = str(response.elapsed.total_seconds())
    if response.status_code != 200:
        return False, response_time, response.status_code
    else:
        return True, response_time, response.status_code


def query_hazard_service(lat, lng, radius, url):
    try:
        response = requests.post(url + "/sfa_handler_safe",
                                 json={"lat": lat, "lng": lng, "radius": radius, "request_type": "point_safety"},
                                 timeout=10)
        return check_response(response)
    except (requests.Timeout, requests.ConnectionError):
        return False, 'TIMEOUT', None


def query_database(prod_string, query):
    conn = psycopg2.connect(
        prod_string,
        sslmode='require')
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        response = cursor.fetchall()
        return response
    except:
        return None


def test_database(prod_string):
    example_query = 'SELECT id FROM "Insurance"."insurance_policies" LIMIT 1'
    start_time = time.time()
    response = query_database(prod_string, example_query)
    end_time = time.time()
    if response is not None:
        active = True
        response_time = round(end_time - start_time, 4)
    else:
        active = False
        response_time = 0
    return active, str(response_time), None


def query_airmap():
    url = "https://api.airmap.com/aircraft/v2/manufacturer"
    headers = {
        'accept': "application/json",
        'x-api-key': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVkZW50aWFsX2lkIjoiY3JlZGVudGlhbHxLYTNrZ1B4RktReW1kZ2h5N3F2cEFzTUFKYTVnIiwiYXBwbGljYXRpb25faWQiOiJhcHBsaWNhdGlvbnxhWVlhNG1kSGQ0QmdPRkdwTGdiT0ZrTjAwWFAiLCJvcmdhbml6YXRpb25faWQiOiJkZXZlbG9wZXJ8UHlNTHkzWUZnM2IyTUtpeUVsYldic1FnbUw0RCIsImlhdCI6MTUxOTU4MTQ4OX0.rnz4zjKkyO9dzDW5S8bhkIOjwRPLuoUaXT0kqNcHgzo"
    }
    try:
        response = requests.request("GET", url, headers=headers, timeout=10)
    except (requests.Timeout, requests.ConnectionError):
        return False, 'Timeout', None

    return check_response(response)


def query_skywatch_api(url):
    skywatch_api = url
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
         "start_time": 9651096405776
    }
    try:
        response = requests.post(skywatch_api, json=data_to_input, timeout=10)
    except (requests.Timeout, requests.ConnectionError):
        return False, 'Timeout', None
    return check_response(response)


def add_api_data(dictionary, errors, api_name, response_info):
    active, rt, status_code = response_info
    if not active:
        errors[api_name] = {'response_time': rt}
        if status_code is not None:
             errors[api_name]['status_code'] = status_code
        dictionary['most_recent_errors.{}'.format(api_name)] = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S") + " UTC"
    dictionary['most_recent_logs.{}'.format(api_name)] = {'active': active,
                                                          'response_time': rt}


def add_timestamp(dic):
    dic['timestamp'] = datetime.datetime.utcnow().strftime("%H:%M:%S") + " UTC"


def update_recent_log_us(log, errors):
    hazard_response_info = query_hazard_service(40.791859, -84.434, 30, 'http://hazards.skywatch.ai')
    skywatch_response_info = query_skywatch_api('https://api.skywatch.ai/api/insurances/offers')
    airmap_response_info = query_airmap()
    db_response_info = test_database(US_constants.prod_connection_string)
    add_api_data(log, errors, 'hazard_api', hazard_response_info)
    add_api_data(log, errors, 'skywatch_api', skywatch_response_info)
    add_api_data(log, errors, 'airmap_api', airmap_response_info)
    add_api_data(log, errors, 'Database', db_response_info)
    add_timestamp(log)


def update_recent_log_uk(log, errors):
    hazard_response_info = query_hazard_service(40.791859, -84.434, 30, 'http://40.68.131.122')
    skywatch_response_info = query_skywatch_api('https://skywatch-stack-prod-uk.westeurope.cloudapp.azure.com/api/insurances/offers')
    db_response_info = test_database(UK_constants.prod_connection_string)
    add_api_data(log, errors, 'hazard_api', hazard_response_info)
    add_api_data(log, errors, 'skywatch_api', skywatch_response_info)
    add_api_data(log, errors, 'Database', db_response_info)
    add_timestamp(log)


def insert_into_db(most_recent, errors, country):
    if country == "US":
        doc_id = US_constants.api_doc_id
    else:
        doc_id = UK_constants.api_doc_id
    connection = pymongo.MongoClient(US_constants.uri)
    db = connection['MyDatabase']
    collection = db['API_Logs']
    if len(errors) > 0:
        collection.insert_one({'errors': errors,
                               'country': country,
                               'timestamp': datetime.datetime.utcnow()})
    collection.update_one({'_id': ObjectId(doc_id)}, {"$set": most_recent})


if __name__ == '__main__':
    most_recent_data_us = {}
    api_errors_us = {}
    most_recent_data_uk = {}
    api_errors_uk = {}
    update_recent_log_us(most_recent_data_us, api_errors_us)
    insert_into_db(most_recent_data_us, api_errors_us, "US")
    update_recent_log_uk(most_recent_data_uk, api_errors_uk)
    insert_into_db(most_recent_data_uk, api_errors_uk, "UK")


