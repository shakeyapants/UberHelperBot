import api_keys as keys
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
import re

# dictionary for separate rides for each user
user_rides = {}

# set uber session
session = Session(server_token=keys.UBER_SERVER_TOKEN)
client = UberRidesClient(session)

# RegEx for coordinates
pattern = re.compile('\d+\.\d+')


# First and last name of the user
def get_user_name(update):
    return '{} {}'.format(update.message.chat.first_name, update.message.chat.last_name)


# check that there're both start and end coordinates given
def check_endpoints(chat_id):
    if 'start' and 'end' in user_rides[chat_id]:
        return True
    else:
        return False


# approximate price from Uber
def estimate_price(coordinates):
    response = client.get_price_estimates(
        start_latitude=coordinates['start'][0],
        start_longitude=coordinates['start'][1],
        end_latitude=coordinates['end'][0],
        end_longitude=coordinates['end'][1],
        seat_count=2
    )

    high = response.json.get('prices')[0]['high_estimate']
    fixed = int(high + high / 100 * 13)
    return fixed


def msg(bot, update):
    update.message.reply_text('Прости, пока я ничего не понимаю :(')


def get_help(bot, update):
    update.message.reply_text('Прости, пока я ничего не понимаю, самому бы разобраться :(')


def greet_user(bot, update):
    update.message.reply_text('Привет, {}'.format(get_user_name(update)))


def get_start_point(bot, update):
    user_text = update.message.text
    start_coordinates = re.findall(pattern, user_text)
    if not start_coordinates:
        update.message.reply_text('Такого не бывает!')
    else:
        dict_start_coordinates = user_rides.setdefault(update.message.chat_id, {'start': None})
        dict_start_coordinates['start'] = start_coordinates
        print(user_rides)
    if check_endpoints(update.message.chat_id) is True:
        fixed = estimate_price(user_rides[update.message.chat_id])
        update.message.reply_text('Будет примерно {}'.format(fixed))


def get_end_point(bot, update):
    user_text = update.message.text
    end_coordinates = re.findall(pattern, user_text)
    if not end_coordinates:
        update.message.reply_text('Такого не бывает!')
    else:
        dict_end_coordinates = user_rides.setdefault(update.message.chat_id, {'end': None})
        dict_end_coordinates['end'] = end_coordinates
        print(user_rides)
    if check_endpoints(update.message.chat_id) is True:
        fixed = estimate_price(user_rides[update.message.chat_id])
        update.message.reply_text('Будет примерно {}'.format(fixed))


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )


def main():
    updater = Updater(keys.TELEGRAM_TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', greet_user))
    dp.add_handler(CommandHandler('help', get_help))
    dp.add_handler(CommandHandler('от', get_start_point))
    dp.add_handler(CommandHandler('до', get_end_point))
    dp.add_handler(MessageHandler(Filters.text, msg))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    logging.info('Bot started')
    main()
