import elasticsearch
import time
import math

db = "http://elasticsearch-us-prod.eastus.cloudapp.azure.com:9200/"

day = 86400000
week = 604800000
month = 2592000000


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

    es = elasticsearch.Elasticsearch([db], http_auth=('kibana', 'SkyWatch123#@!'))
    response = es.search(index=index, body=elastic_query(last_time, now, query), request_timeout=30)

    # count
    count = response["hits"]["total"]
    return count


# most recent logs this year
def most_recent_logs(query):
    now = math.floor(time.time() * 1000)
    last_time = now - (7 * day)
    index = "prod-api-*"

    es = elasticsearch.Elasticsearch([db], http_auth=('kibana', 'SkyWatch123#@!'))
    response = es.search(index=index, body=elastic_query(last_time, now, query), request_timeout=30)

    three_recent_logs = []
    list_of_logs = response["hits"]["hits"]
    for i in range(6):

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

# elastic_day("Level = Error")
# elastic_week("Level = Error")
# elastic_month("Level = Error")
# most_recent_logs("Level = Error")