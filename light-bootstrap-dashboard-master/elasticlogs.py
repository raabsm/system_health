import elasticsearch
import requests
import json

try:
    es = elasticsearch.Elasticsearch(["https://skywatch-elasticsearch-dev.northeurope.cloudapp.azure.com/app/kibana#/discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-24h,mode:quick,to:now))&_a=(columns:!(level,message),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:ef8389d0-5b05-11e9-b4fb-6364e35ce19b,key:level,negate:!t,params:(query:Information,type:phrase),type:phrase,value:Information),query:(match:(level:(query:Information,type:phrase)))),('$state':(store:appState),meta:(alias:!n,disabled:!f,index:ef8389d0-5b05-11e9-b4fb-6364e35ce19b,key:level,negate:!t,params:(query:Warning,type:phrase),type:phrase,value:Warning),query:(match:(level:(query:Warning,type:phrase))))),index:ef8389d0-5b05-11e9-b4fb-6364e35ce19b,interval:auto,query:(language:lucene,query:''),sort:!('@timestamp',desc))"],
                                     http_auth=('kibana', 'SkyWatch123#@!'))
except:
    print("error")
# url = "https://skywatch-elasticsearch-dev.northeurope.cloudapp.azure.com/app/kibana#/discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-24h,mode:quick,to:now))&_a=(columns:!(level,message),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:ef8389d0-5b05-11e9-b4fb-6364e35ce19b,key:level,negate:!t,params:(query:Information,type:phrase),type:phrase,value:Information),query:(match:(level:(query:Information,type:phrase)))),('$state':(store:appState),meta:(alias:!n,disabled:!f,index:ef8389d0-5b05-11e9-b4fb-6364e35ce19b,key:level,negate:!t,params:(query:Warning,type:phrase),type:phrase,value:Warning),query:(match:(level:(query:Warning,type:phrase))))),index:ef8389d0-5b05-11e9-b4fb-6364e35ce19b,interval:auto,query:(language:lucene,query:''),sort:!('@timestamp',desc))"
print(es)

searched = es.count(index="/app/kibana", body={"version":True,"size":500,"sort":[{"@timestamp":{"order":"desc","unmapped_type":"boolean"}}],"_source":{"excludes":[]},"aggs":{"2":{"date_histogram":{"field":"@timestamp","interval":"30m","time_zone":"Asia\/Jerusalem","min_doc_count":1}}},"stored_fields":["*"],"script_fields":{},"docvalue_fields":[{"field":"@timestamp","format":"date_time"},{"field":"ObjectResult.Value.DateOfBirth","format":"date_time"},{"field":"ObjectResult.Value.ValidFromUtc","format":"date_time"},{"field":"ObjectResult.Value.ValidUntilUtc","format":"date_time"},{"field":"Offer.StartTime","format":"date_time"},{"field":"OkObjectResult.Value.ValidFromUtc","format":"date_time"},{"field":"OkObjectResult.Value.ValidUntilUtc","format":"date_time"},{"field":"OkObjectResult.Value.expiration","format":"date_time"},{"field":"UserProfileDto.DateOfBirth","format":"date_time"}],"query":{"bool":{"must":[{"match_all":{}},{"range":{"@timestamp":{"gte":1564226856700,"lte":1564313256700,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[{"match_phrase":{"level":{"query":"Information"}}}]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@\/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}})
# es.indices.create(index="app/kibana", ignore=400)
# print(searched)


request = {
  "version": true,
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
        "interval": "30m",
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
    }
  ],
  "query": {
    "bool": {
      "must": [
        {
          "match_all": {}
        },
        {
          "range": {
            "@timestamp": {
              "gte": 1564226856700,
              "lte": 1564313256700,
              "format": "epoch_millis"
            }
          }
        }
      ],
      "filter": [],
      "should": [],
      "must_not": [
        {
          "match_phrase": {
            "level": {
              "query": "Information"
            }
          }
        }
      ]
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