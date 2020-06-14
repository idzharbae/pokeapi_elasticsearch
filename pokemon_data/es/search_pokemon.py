from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


def search_pokemon(es: Elasticsearch, search_query: str, page: int):
    s = Search(using=es)
    q = Q({
        'function_score': {
            'query': {
                'multi_match': {
                    'query': search_query,
                    'fields': [
                        'doc.name',
                        'doc.abilities.ability.name',
                        'doc.forms.name',
                        'doc.moves.move.name'
                    ],
                    'fuzziness': 'AUTO',
                    'prefix_length': 2
                }
            }
        }
    })
    s = s.query(q)[(page - 1) * 10:page * 10]
    res = s.execute()
    return res
