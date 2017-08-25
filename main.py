import telegram
import logging
from telegram.ext import CommandHandler, MessageHandler, Updater
import urllib.request, json
from operator import attrgetter
import random
import traceback

import tokens

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = tokens.BOT_TOKEN
FLICKR_TOKEN = tokens.FLICKR_TOKEN
DELAY = 2 * 60 * 60
TAGS = ["tiger", "cheetah", "lion", "snow leopard"]
ID_FILE_PATH = "ids.txt"
PAST_IDS = []

class PhotoBot:
    def __init__(self, token, handlers):
        print("__init__")
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        for i, handler in enumerate(handlers):
            self.dispatcher.add_handler(handler, group=i)

    def run(self):
        print("run")
        self.updater.start_polling()
        self.updater.idle()

# Non-handler helper methods

def get_photo(tag):
    print("get_photo tag=" + tag)
    tag = '+'.join(tag.split(' '))

    # search flickr for tag
    results_per_page = 500
    page = 1
    search_url_base = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key={0}&tags={1}&text={1}&sort=relevance&safe_search=1&content_type=1&media=photos&per_page={3}&page={2}&format=json&nojsoncallback=1"
    search_url = search_url_base.format(FLICKR_TOKEN, tag, page, results_per_page)

    print("http request to " + search_url)
    with urllib.request.urlopen(search_url) as search_request:
        search_response = json.loads(search_request.read().decode())

    # find unique image
    response_count = len(search_response['photos']['photo'])
    image_order = random.sample(range(0, response_count), response_count)
    index = image_order.pop()
    image_info = search_response['photos']['photo'][index]
    print("checking image #" + str(index) + '(' + image_info['id'] + ')')
    while image_info['id'] in PAST_IDS:
        #if we run out of images, go to next page
        if not image_order:
            page = page + 1
            print("no more images. moving to page " + page)
            search_url = search_url_base.format(FLICKR_TOKEN, tag, page, results_per_page)
            print("http request to " + search_url)
            with urllib.request.urlopen(search_url) as search_request:
                search_response = json.loads(search_request.read().decode())

            response_count = len(search_response['photos']['photo'])
            image_order = random.sample(range(0, response_count), response_count)

        index = image_order.pop()
        image_info = search_response['photos']['photo'][index]
        print("image not unique. checking image #" + str(index) + '(' + image_info['id'] + ')')


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

    PAST_IDS.append(image_info['id'])

    return image_info['id'], largest['source']

def handle_getpic(bot, update, args=list()):
    print("handle_getpic args=" + str(args))
    message = update.message

    if args:
        tag = ' '.join(args)
    else:
        tag = random.choice(TAGS)

    print("tag=" + tag)

    photo_id, photo_url = get_photo(tag)
    with open(ID_FILE_PATH, 'a') as id_file:
        id_file.write(photo_id + "\n")
    message.reply_photo(photo=photo_url)


handler_getpic = CommandHandler('getpic', handle_getpic, pass_args=True)

def handle_gettags(bot, update):
    print("handle_gettags")
    message = update.message

    response = ', '.join(TAGS)
    print("current tags: " + response)

    message.reply_text(text="Current tags: " + response)

handler_gettags = CommandHandler('gettags', handle_gettags)

def main():
    print("main")
    handlers = [v for k, v in globals().items() if k.startswith('handler')]

    with open(ID_FILE_PATH, 'w+') as id_file:
        PAST_IDS = id_file.read().splitlines()

    quote = PhotoBot(BOT_TOKEN, handlers)
    quote.run()

if __name__ == '__main__':
    main()