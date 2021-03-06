import telegram
import logging
from telegram.ext import CommandHandler, MessageHandler, Updater
import urllib.request, json
from operator import attrgetter
import random
import traceback
import os.path
import threading

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
CHAT_FILE_PATH = "chats.txt"
PAST_IDS = []
DELAY = 60 * 60 * 2
CHANNEL_ID = -1001110839197
ADMINS = [182524440]
UNAUTH_MESSAGE = "You must be an admin to use that command."
TIMER = null

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

    def begin_autopost(self):
        print("begin_autopost")
        bot = self.updater.bot
        TIMER = threading.Timer(DELAY, scheduled_post, args=[bot]).start()

# Non-handler helper methods

def get_chats():
    print("get_chats")

    if not os.path.isfile(CHAT_FILE_PATH):
        return []
    else:
        with open(CHAT_FILE_PATH, 'r') as chat_file:
            return chat_file.read().splitlines()

def scheduled_post(bot):
    print("scheduled_post")

    tag = random.choice(TAGS)
    print("tag: " + tag)

    photo_id, photo_url = get_photo(tag)

    chats = get_chats()

    print("sending to channel")
    message = bot.send_photo(chat_id = CHANNEL_ID, photo = photo_url)

    for chat in chats:
        if chat:
            print("sending to chat " + chat)
            bot.forward_message(chat_id = int(chat), from_chat_id = CHANNEL_ID, message_id = message.message_id)

    print("done sending")

    TIMER = threading.Timer(DELAY, scheduled_post, args=[bot]).start()

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
        # if we run out of images, go to next page
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
    with open(ID_FILE_PATH, 'a') as id_file:
        id_file.write(image_info['id'] + "\n")

    return image_info['id'], largest['source']

def is_admin(user):
    return user.id in ADMINS

# command handlers

def handle_getpic(bot, update, args=list()):
    print("handle_getpic args=" + str(args))
    message = update.message

    if args:
        tag = ' '.join(args)
    else:
        tag = random.choice(TAGS)

    print("tag=" + tag)

    photo_id, photo_url = get_photo(tag)
    message.reply_photo(photo=photo_url)

handler_getpic = CommandHandler('getpic', handle_getpic, pass_args=True)

def handle_gettags(bot, update):
    print("handle_gettags")
    message = update.message

    response = ', '.join(TAGS)
    print("current tags: " + response)

    message.reply_text(text="Current tags: " + response)

handler_gettags = CommandHandler('gettags', handle_gettags)
handler_tags = CommandHandler('tags', handle_gettags)

def handle_addtag(bot, update, args=list()):
    print("handle_addtag args=" + str(args))
    message = update.message

    if is_admin(message.from_user):
        tag = ' '.join(args)
        if tag.isspace():
            print('no tag provided')
            response = "Please provide a tag to add."
        elif tag in TAGS:
            print('tag already exists')
            response = "\"" + tag + "\" is already a tag."
        else:
            print('adding tag "' + tag + '"')
            TAGS.append(tag)
            response = "Tag \"" + tag + "\" added. Current tags: " + ', '.join(TAGS)
            
        print("current tags: " + ', '.join(TAGS))
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_addtag = CommandHandler('addtag', handle_addtag, pass_args=True)

def handle_rmtag(bot, update, args=list()):
    print("handle_rmtag args=" + str(args))
    message = update.message

    if is_admin(message.from_user):
        tag = ' '.join(args)
        if tag.isspace():
            print('no tag provided')
            response = "Please provide a tag to remove."
        elif tag in TAGS:
            print('removing tag "' + tag + '"')
            TAGS.remove(tag)
            response = "Tag \"" + tag + "\" removed. Current tags: " + ', '.join(TAGS)
        else:
            print('couldnt find tag "' + tag + '"')
            response = "No tag matching \"" + tag + "\" could be found."
            
        print("current tags: " + ', '.join(TAGS))
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_rmtag = CommandHandler('rmtag', handle_rmtag, pass_args=True)

def handle_register(bot, update):
    print("handle_register")
    message = update.message

    if is_admin(message.from_user):
        chat = str(message.chat.id)
        print('chat: ' + chat)

        chats = get_chats()

        if chat in chats:
            print("already registered")
            response = "This chat is already registered."
        else:
            with open(CHAT_FILE_PATH, 'a') as chat_file:
                chat_file.write(chat + '\n')

            print("chat added")
            response = "Chat has been registered."
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_register = CommandHandler('register', handle_register)

def handle_unregister(bot, update):
    print("handle_unregister")
    message = update.message

    if is_admin(message.from_user):
        chat = str(message.chat.id)
        print('chat: ' + chat)

        chats = get_chats()

        if chat in chats:
            print("removing chat")

            f = open(CHAT_FILE_PATH, "r")
            lines = f.readlines()
            f.close()
            f = open(CHAT_FILE_PATH, "w")
            for line in lines:
                if line != chat + "\n":
                    f.write(line)
            f.close()

            response = "Chat has been unregistered."
        else:
            print("already not registered")
            response = "This chat is already not registered.."
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_unregister = CommandHandler('unregister', handle_unregister)

def handle_clearhistory(bot, update):
    print("handle_clearhistory")
    message = update.message

    if is_admin(message.from_user):
        PAST_IDS = []
        open(ID_FILE_PATH, 'w').close()
        response = "Image history has been cleared."
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_clearhistory = CommandHandler('clearhistory', handle_clearhistory)

def handle_stop(bot, update):
    print("handle_stop")
    message = update.message

    if is_admin(message.from_user):
        print("cancelling timer")
        if (TIMER):
            TIMER.cancel()
            TIMER = null
            response = "Automatic posting disabled."
        else:
            response = "Automatic posting is already disabled."
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_stop = CommandHandler('stop', handle_stop)

def handle_start(bot, update):
    print("handle_start")
    message = update.message

    if is_admin(message.from_user):
        print("posting")
        if (TIMER):
            response = "Automatic posting is already enabled."
            scheduled_post(bot)
        else:
            response = "Automatic posting enabled."
    else:
        response = UNAUTH_MESSAGE

    message.reply_text(text=response)

handler_start = CommandHandler('start', handle_start)

def main():
    print("main")
    # find everything that starts with 'handler_' and add it as a handler
    handlers = [v for k, v in globals().items() if k.startswith('handler')]

    with open(ID_FILE_PATH, 'r') as id_file:
        PAST_IDS = id_file.read().splitlines()

    quote = PhotoBot(BOT_TOKEN, handlers)
    quote.begin_autopost()
    quote.run()

if __name__ == '__main__':
    main()