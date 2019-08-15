import elasticsearch
import time
import math
import pymongo
from bson import ObjectId
import US_Constants as US_constants
import UK_Constants as UK_constants

uri = US_constants.uri

day = 86400000
week = 604800000
month = 2592000000


def init_db(country):
    global db
    global es
    if country == "US":
        db = US_constants.error_db
    else:
        db = UK_constants.error_db
    es = elasticsearch.Elasticsearch([db], http_auth=('kibana', 'SkyWatch123#@!'))


def elastic_day(query):
    # print(elastic_count(query, day))
    return elastic_count(query, day)


def elastic_week(query):
    # print(elastic_count(query, week))
    return elastic_count(query, week)


def elastic_month(query):
    # print(elastic_count(query, month))
    return elastic_count(query, month)


def elastic_count(query, interval):
    now = math.floor(time.time() * 1000)
    last_time = now - interval

    index = "prod-api-*"

    response = es.search(index=index, body=elastic_query(last_time, now, query), request_timeout=30)

    # count
    count = response["hits"]["total"]
    return count


# most recent logs this year
def most_recent_logs(query):
    now = math.floor(time.time() * 1000)
    last_time = now - (7 * day)
    index = "prod-api-*"

    response = es.search(index=index, body=elastic_query(last_time, now, query), request_timeout=30)

    three_recent_logs = []
    list_of_logs = response["hits"]["hits"]
    for i in (range(6) if len(list_of_logs) > 6 else range(len(list_of_logs))):
        stamp = list_of_logs[i]["_source"]["@timestamp"]
        stamp = stamp[:stamp.find(".")].replace("T", " ")
        stamp += " UTC"

        message = list_of_logs[i]["_source"]["messageTemplate"]
        message = (message[:115] + '...') if len(message) > 115 else message

        info = {"message_template": message,
                "exception_message": list_of_logs[i]["_source"]["exceptions"][0]["Message"],
                "exception_source": list_of_logs[i]["_source"]["exceptions"][0]["Source"],
                "timestamp": stamp,
                "id": list_of_logs[i]["_id"]}
        three_recent_logs.append(info)
    return three_recent_logs


def elastic_query(old_time, now, query):
    return {
        "version": True,
        "size": 500,
        "sort": [
            {
                "@timestamp": {
                    "order": "desc",
                    "unmapped_type": "boolean"
                }
            }
        ],
        "_source": {
            "excludes": []
        },
        "aggs": {
            "2": {
                "date_histogram": {
                    "field": "@timestamp",
                    "interval": "3h",
                    "time_zone": "Asia/Jerusalem",
                    "min_doc_count": 1
                }
            }
        },
        "stored_fields": [
            "*"
        ],
        "script_fields": {},
        "docvalue_fields": [
            {
                "field": "@timestamp",
                "format": "date_time"
            },
            {
                "field": "ObjectResult.Value.DateOfBirth",
                "format": "date_time"
            },
            {
                "field": "ObjectResult.Value.Flight.EndTime",
                "format": "date_time"
            },
            {
                "field": "ObjectResult.Value.Flight.StartTime",
                "format": "date_time"
            },
            {
                "field": "ObjectResult.Value.StartedAt",
                "format": "date_time"
            },
            {
                "field": "ObjectResult.Value.ValidFromUtc",
                "format": "date_time"
            },
            {
                "field": "ObjectResult.Value.ValidUntilUtc",
                "format": "date_time"
            },
            {
                "field": "Offer.StartTime",
                "format": "date_time"
            },
            {
                "field": "OkObjectResult.Value.ValidFromUtc",
                "format": "date_time"
            },
            {
                "field": "OkObjectResult.Value.ValidUntilUtc",
                "format": "date_time"
            },
            {
                "field": "OkObjectResult.Value.expiration",
                "format": "date_time"
            },
            {
                "field": "UserProfileDto.DateOfBirth",
                "format": "date_time"
            },
            {
                "field": "ViewResult.Model.IssuedTime",
                "format": "date_time"
            },
            {
                "field": "ViewResult.Model.ValidFrom",
                "format": "date_time"
            },
            {
                "field": "ViewResult.Model.ValidUntil",
                "format": "date_time"
            }
        ],
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": query,
                            "analyze_wildcard": True,
                            "default_field": "*"
                        }
                    },
                    {
                        "match_phrase": {
                            "level": {
                                "query": "Error"
                            }
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": old_time,
                                "lte": now,
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "filter": [],
                "should": [],
                "must_not": []
            }
        },
        "highlight": {
            "pre_tags": [
                "@kibana-highlighted-field@"
            ],
            "post_tags": [
                "@/kibana-highlighted-field@"
            ],
            "fields": {
                "*": {}
            },
            "fragment_size": 2147483647
        }
    }


def insert_into_mongo(document, doc_id):
    connection = pymongo.MongoClient(uri)
    mongo_db = connection['MyDatabase']
    collection = mongo_db['Service_Error_Logs']
    collection.update_one({'_id': ObjectId(doc_id)}, {"$set": document})


def fill_data(query):
    count_last_day = elastic_day(query)
    count_last_week = elastic_week(query)
    count_last_month = elastic_month(query)
    recent_logs = most_recent_logs(query)
    document = {'count_last_day': count_last_day,
                'count_last_week': count_last_week,
                'count_last_month': count_last_month,
                'most_recent_logs': recent_logs}
    return document


if __name__ == "__main__":
    query = "Level = Error, level = Error"
    init_db("US")
    us_data = fill_data(query)
    init_db("UK")
    uk_data = fill_data(query)
    insert_into_mongo(us_data, US_constants.error_doc_id)
    insert_into_mongo(uk_data, UK_constants.error_doc_id)
