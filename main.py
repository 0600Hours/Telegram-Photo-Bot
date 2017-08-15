import telegram
import logging
import urllib.request, json
from telegram.ext import Updater

import tokens

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
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
    print("get_photo")
    urlBase = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key={0}&tags={1}&text={1}&sort=relevance&safe_search=1&content_type=1&media=photos&per_page=10&page={2}&format=json&nojsoncallback=1"
    url = urlBase.format(FLICKR_TOKEN, tag, 1)

    with urllib.request.urlopen(url) as request:
        response = json.loads(request.read().decode())
        print (response['photos']['photo'][0])


def main():
    print("main")
    handlers = [v for k, v in globals().items() if k.startswith('handler')]

    quote = PhotoBot(BOT_TOKEN, handlers)
    quote.run()

if __name__ == '__main__':
    main()