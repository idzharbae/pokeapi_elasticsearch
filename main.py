from elasticsearch import Elasticsearch
from cron import pokemon_sync
from function_decorator import logger
from flask import Flask, render_template, request
from threading import Thread
from pokemon_data.redis import search_pokemon as redis


POKE_SYNC_INTERVAL = 60
POKE_SYNC_BATCH = 25

es = Elasticsearch(HOST='http://localhost', PORT=9200)
pokemon_scheduler_job = pokemon_sync.pokemon_scheduler_job(
    es, POKE_SYNC_INTERVAL, POKE_SYNC_BATCH, [logger.with_logger], False
)
poke_scheduler_thread = Thread(target=pokemon_scheduler_job, daemon=True)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    search_query = request.args.get('search_query')
    if search_query is None:
        return render_template('index.html', search_results=None)
    page = request.args.get('page')
    if page is None:
        page = 1
    else:
        page = int(page)

    res = redis.search_pokemon(es, search_query, page)
    return render_template('index.html', search_results=res, query=search_query, page=page)


if __name__ == '__main__':
    poke_scheduler_thread.start()
    print('listening to port ', 9000)
    app.run('localhost', 9000, True)
