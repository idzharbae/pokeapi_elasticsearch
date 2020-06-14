from redis.client import Redis
from elasticsearch import Elasticsearch
from ..es import search_pokemon as es_repository
import json

cache = Redis(host='localhost', port=6379)


def search_pokemon(es: Elasticsearch, search_query: str, page: int):
    key = search_query+'-'+str(page)
    cache_result = cache.hget('pokemon', key)
    if cache_result is not None:
        print('cache hit')
        return json.loads(cache_result)
    print('cache miss')
    es_result = es_repository.search_pokemon(es, search_query, page)['hits'].to_dict()
    cache.hset('pokemon', key, json.dumps(es_result))
    return es_result



