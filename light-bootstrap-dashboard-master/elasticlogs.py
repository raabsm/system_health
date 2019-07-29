import elasticsearch
from datetime import date
import time
from pprint import pprint
import requests
import json

db = "http://elasticsearch-us-prod.eastus.cloudapp.azure.com:9200/"




def elastic_count():
    lte = round(time.time())
    gte = lte - 86400000
    today = date.today()
    # index = "prod-api-proxy-*" + today.strftime("%Y.%m.%d")
    index = "prod-api-proxy-*"

    es = elasticsearch.Elasticsearch([db], http_auth=('kibana', 'SkyWatch123#@!'))
    print(es)

    # statuscode200 in last 24
    count = es.search(index=index, body={"query": { "bool": { "must": [ {"query_string":{"query":"StatusCode: 200", "analyze_wildcard": False, "default_field": "*"}}, { "range": { "@timestamp": { "gte": gte, "lte": lte, "format": "epoch_millis" } } } ], "filter": [], "should": [], "must_not": [] } }})

    pprint(count)

def elastic_category():
    catergories = ["Warning"]


elastic_count()