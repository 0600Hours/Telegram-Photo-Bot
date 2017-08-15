import telegram
import logging
from telegram.ext import Updater
import urllib.request, json
from operator import attrgetter

import tokens

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = tokens.BOT_TOKEN
FLICKR_TOKEN = tokens.FLICKR_TOKEN
DELAY = 2 * 60 * 60
TAGS = ["tiger", "cheetah", "lion", "snow leopard"]

class PhotoBot:
    def __init__(self, token, handlers):
        print("__init__")
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        for i, handler in enumerate(handlers):
            self.dispatcher.add_handler(handler, group=i)

    def run(self):
        print("run")
        get_photo("tiger");

        self.updater.start_polling()
        self.updater.idle()



# Non-handler helper methods

def get_photo(tag):
    print("get_photo tag=" + tag)

    # search flickr for tag
    search_url_base = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key={0}&tags={1}&text={1}&sort=relevance&safe_search=1&content_type=1&media=photos&per_page=10&page={2}&format=json&nojsoncallback=1"
    search_url = search_url_base.format(FLICKR_TOKEN, tag, 1)

    print("http request to " + search_url)
    with urllib.request.urlopen(search_url) as search_request:
        search_response = json.loads(search_request.read().decode())

    image_info = search_response['photos']['photo'][0]
    print("found image id " + image_info['id'])

    # get images from search result

    sizes_url_base = "https://api.flickr.com/services/rest/?method=flickr.photos.getSizes&api_key={0}&photo_id={1}&format=json&nojsoncallback=1"
    sizes_url = sizes_url_base.format(FLICKR_TOKEN, image_info['id'])

    print("http request to " + sizes_url)
    with urllib.request.urlopen(sizes_url) as sizes_request:
        sizes_response = json.loads(sizes_request.read().decode())

    sizes = sizes_response['sizes']['size']

    # find largest image

    widths = [int(x['width']) for x in sizes]
    largest = [x for x in sizes if x['width'] == str(max(widths))][0]
    print("chose size {0} ({1}x{2}) at {3}".format(largest['label'], largest['width'], largest['height'], largest['source']))

    return largest['source']


def main():
    print("main")
    handlers = [v for k, v in globals().items() if k.startswith('handler')]

    quote = PhotoBot(BOT_TOKEN, handlers)
    quote.run()

if __name__ == '__main__':
    main()