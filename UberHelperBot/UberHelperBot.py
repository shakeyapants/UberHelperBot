# -*- coding: utf-8 -*-

import api_keys as keys
import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
import re

# states
START_LOCATION, END_LOCATION = range(2)

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


# price every minute
def reply_price_every_minute(bot, job):
    fixed = estimate_price(user_rides[job.context])
    bot.send_message(job.context, text=fixed)


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
    update.message.reply_text('Нажми /start для выбора начальной точки поездки')


def stop_notification(bot, update):
    try:
        job = user_rides[update.message.chat_id]['job']
        job.schedule_removal()
    except KeyError:
        pass
    update.message.reply_text('Окей, больше не буду. Нажми /start для выбора начальной точки поездки')


def get_help(bot, update):
    update.message.reply_text('Прости, пока я ничего не понимаю, самому бы разобраться :(')


def greet_user(bot, update):
    location_keyboard = KeyboardButton(text="Отправить мое местоположение", request_location=True)
    custom_keyboard = [[location_keyboard]]
    update.message.reply_text(
        'Привет, откуда едем?',
        reply_markup=ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True))
    return START_LOCATION


def get_start_location(bot, update):
    user_location = update.message.location
    update.message.reply_text('Отлично, куда едем?')
    dict_start_coordinates = user_rides.setdefault(update.message.chat_id, {'start': None})
    dict_start_coordinates['start'] = [user_location['latitude'], user_location['longitude']]
    return END_LOCATION


def get_end_location(bot, update):
    user_location = update.message.location
    update.message.reply_text('Супер, сейчас посчитаю...')
    dict_end_coordinates = user_rides.setdefault(update.message.chat_id, {'end': None})
    dict_end_coordinates['end'] = [user_location['latitude'], user_location['longitude']]
    fixed = estimate_price(user_rides[update.message.chat_id])
    update.message.reply_text('Будет примерно {}'.format(fixed))
    return make_decision(bot, update)


def make_decision(bot, update):
    chat_id = update.message.chat_id
    deep_link = 'https://m.uber.com/ul/?action=setPickup&client_id={client_id}&pickup[formatted_address]=' \
                'start&pickup[latitude]={start_latitude}&pickup[longitude]={start_longtitude}&' \
                'dropoff[formatted_address]=end&dropoff[latitude]={end_latitude}&' \
                'dropoff[longitude]={end_longtitude}'.format(client_id=keys.UBER_CLIENT_ID,
                                                             start_latitude=user_rides[chat_id]['start'][0],
                                                             start_longtitude=user_rides[chat_id]['start'][1],
                                                             end_latitude=user_rides[chat_id]['end'][0],
                                                             end_longtitude=user_rides[chat_id]['end'][1])

    keyboard = [[InlineKeyboardButton('Ок, еду', callback_data='ok', url=deep_link)],
                [InlineKeyboardButton('Когда будет дешевле?', callback_data='cheaper')],
                [InlineKeyboardButton('Сообщай мне каждую минуту', callback_data='every_minute')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Ну что?', reply_markup=reply_markup)
    return ConversationHandler.END


def button(bot, update, job_queue):
    query = update.callback_query
    chat_id = update.callback_query.message.chat.id

    if query.data == 'cheaper':
        # call some function
        bot.edit_message_text(text='Сообщу, как подешевеет',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    elif query.data == 'every_minute':
        bot.edit_message_text(text='Для отмены пришли /stop',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

        job = job_queue.run_repeating(reply_price_every_minute, 60, context=chat_id)
        user_rides[chat_id].update({'job': job})


def cancel(bot, update):
    update.message.reply_text('Пока!')
    return ConversationHandler.END


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )


def main():
    updater = Updater(keys.TELEGRAM_TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('help', get_help))
    dp.add_handler(CommandHandler('stop', stop_notification))
    dp.add_handler(MessageHandler(Filters.text, msg))
    dp.add_handler(CallbackQueryHandler(button, pass_job_queue=True))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', greet_user)],

        states={
            START_LOCATION: [MessageHandler(Filters.location, get_start_location)],
            END_LOCATION: [MessageHandler(Filters.location, get_end_location)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.info('Bot started')
    main()
