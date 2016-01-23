import json
import logging
from pprint import pprint

from flask import Flask, render_template, request

import settings
import redis
from datetime import datetime

from utils import foursquare
from utils import mondo

app = Flask(__name__, template_folder='../html', static_folder='../static')
app.config['DEBUG'] = True


log = logging.getLogger(__name__)


@app.route('/')
def route_index():
    log.info('test')
    return render_template('index.html')


@app.route('/webhook', methods=['POST'])
def route_webhook():
    transaction = json.loads(request.data.decode('utf8'))

    if not transaction['data']['is_load']:

        merchant = transaction['data']['merchant']
        account_id = transaction['data']['account_id']

        date = datetime.date.today()
        year_and_week = "%s_%s" % (date.isocalendar()[1], date.year)

        redis_client = redis.Redis()
        redis_key = "%s_%s_%s" % (account_id, merchant['id'], year_and_week)
        redis_client.incr(redis_key, 1)

        current_count = redis_client.get(redis_key)
        if current_count > 1:
            name = merchant['name']
            long = merchant['address']['longitude']
            lat = merchant['address']['latitude']

            venue_id = foursquare.get_venue_id(name, lat, long)

            similar_venues = foursquare.get_similar_venues(venue_id)

            if similar_venues['items']:
                title = similar_venues['items'][0]['name']
                url = similar_venues['items'][0].get('url')
                image_url = similar_venues['items'][0]['categories'][0]['icon']['prefix'] + 'bg_64' + similar_venues['items'][0]['categories'][0]['icon']['suffix']

                mondo.post_to_feed(account_id, title, url, image_url)

            else:
                log.info('Nothing Similar')
        else:
            log.info('Only been once')
    else:
        log.info('Mondo Top up')

    return ''




if __name__ == "__main__":
    app.run()
