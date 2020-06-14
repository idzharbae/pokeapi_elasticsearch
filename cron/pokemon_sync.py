import json
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from elasticsearch import helpers, Elasticsearch
from typing import Callable
from queue import Queue
from threading import Thread


def get_pokemon_data():
    url = 'https://pokeapi.co/api/v2/pokemon/'
    idx = 1
    poke_data = []
    res = requests.get (url+str(idx))
    while 'Not Found' not in res.text and idx <= 10:
        poke_data.append(json.loads(res.text))
        idx += 1
        res = requests.get (url+str(idx))
    return poke_data


def document_to_upsert_action(doc: dict):
    return {
        '_op_type': 'update',
        '_index': 'pokeapi',
        '_id': doc['id'],
        '_source': {
            'script': {
                'source': 'if (ctx._source.doc != null) { ctx.op="noop" } else { ctx._source.doc=params.doc }',
                'params': {'doc': doc}
            },
            'upsert': {'doc': doc}
        }
    }


def get_pokemon_data_func(pokemon_data: Queue):
    def f():
        idx = 1
        url = 'https://pokeapi.co/api/v2/pokemon/'
        res = requests.get(url + str(idx))
        while 'Not Found' not in res.text:
            pokemon_data.put(json.loads(res.text))
            idx += 1
            res = requests.get(url + str(idx))
        pokemon_data.put(None)
    return f


def bulk_upsert_func(es: Elasticsearch, pokemon_queue: Queue, result: Queue, batch: int):
    def f():
        pokemon = pokemon_queue.get()
        actions = []
        while pokemon is not None:
            actions.append(
                document_to_upsert_action(pokemon)
            )
            if len(actions) == batch:
                result.put(helpers.bulk(es, actions))
                actions = []
            pokemon = pokemon_queue.get()
        if len(actions) > 0:
            result.put(helpers.bulk(es, actions))
        result.put(None)
    return f


def pokemon_bulk_upserts_job(es: Elasticsearch, batch: int):
    def job():
        print('pokemon sync starting...')
        pokemon_data = Queue()
        result = Queue()

        get_pokemon_job = get_pokemon_data_func(pokemon_data)
        bulk_pokemon_upsert_job = bulk_upsert_func(es, pokemon_data, result, batch)

        get_pokemon_thread = Thread(target=get_pokemon_job, daemon=True)
        bulk_upsert_thread = Thread(target=bulk_pokemon_upsert_job, daemon=True)

        get_pokemon_thread.start()
        bulk_upsert_thread.start()

        bulk_result = result.get()
        while bulk_result is not None:
            print('result:', bulk_result)
            bulk_result = result.get()
        print('pokemon sync finished.')

    return job


def create_job_scheduler(interval_minutes: int, job: Callable):
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, 'interval', seconds=interval_minutes*60)
    return scheduler


def schedule_pokemon_sync(es: Elasticsearch, interval: int, batch: int, job_options: list, run_instantly: bool):
    upsert_job = pokemon_bulk_upserts_job(es, batch)

    for option in job_options:
        upsert_job = option(upsert_job)

    poke_sync_scheduler = create_job_scheduler(interval, upsert_job)
    poke_sync_scheduler.start()

    if run_instantly:
        upsert_job()


def pokemon_scheduler_job(es: Elasticsearch, interval: int, batch: int, job_options: list, run_instantly: bool):
    def f():
        schedule_pokemon_sync(
            es, interval, batch, job_options, run_instantly
        )
    return f
