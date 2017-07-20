# -*- coding: utf-8 -*-

import api_keys as keys
import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
import datetime as dt
from models import db_session, User, Request, Fare

# states
START_LOCATION, END_LOCATION = range(2)

# set uber session
session = Session(server_token=keys.UBER_SERVER_TOKEN)
client = UberRidesClient(session)


# price every minute
def reply_price_every_minute(bot, job):
    chat_id = job.context
    user = User.query.filter(User.chat_id == chat_id).first()
    last_request = user.get_last_request()
    fixed = estimate_price(last_request.start_latitude, last_request.start_longitude,
                           last_request.end_latitude, last_request.end_longitude)

    fare = Fare(fare=fixed, time=dt.datetime.now(), request_id=last_request.id)
    db_session.add(fare)
    db_session.commit()

    deep_link = 'https://m.uber.com/ul/?action=setPickup&client_id={client_id}&pickup[formatted_address]=' \
                'start&pickup[latitude]={start_latitude}&pickup[longitude]={start_longitude}&' \
                'dropoff[formatted_address]=end&dropoff[latitude]={end_latitude}&' \
                'dropoff[longitude]={end_longitude}'.format(client_id=keys.UBER_CLIENT_ID,
                                                            start_latitude=last_request.start_latitude,
                                                            start_longitude=last_request.start_longitude,
                                                            end_latitude=last_request.end_latitude,
                                                            end_longitude=last_request.end_longitude)
    # the program doesn't stop if the user press 'OK'
    keyboard = [[InlineKeyboardButton('Ок, еду', url=deep_link)],
                [InlineKeyboardButton('Хватит', callback_data='stop')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text='Сейчас {}'.format(fixed), reply_markup=reply_markup)


# notify when cheaper
def notify_cheaper(bot, cheap_notification):
    chat_id = cheap_notification.context

    user = User.query.filter(User.chat_id == chat_id).first()
    last_request = user.get_last_request()
    min_price_row = Fare.query.filter(Fare.request_id == last_request.id).order_by(Fare.fare).first()
    min_price = min_price_row.fare
    fixed = estimate_price(last_request.start_latitude, last_request.start_longitude,
                           last_request.end_latitude, last_request.end_longitude)

    fare = Fare(fare=fixed, time=dt.datetime.now(), request_id=last_request.id)
    db_session.add(fare)
    db_session.commit()

    if fixed < min_price:
        cheap_notification.schedule_removal()
        deep_link = 'https://m.uber.com/ul/?action=setPickup&client_id={client_id}&pickup[formatted_address]=' \
                    'start&pickup[latitude]={start_latitude}&pickup[longitude]={start_longitude}&' \
                    'dropoff[formatted_address]=end&dropoff[latitude]={end_latitude}&' \
                    'dropoff[longitude]={end_longitude}'.format(client_id=keys.UBER_CLIENT_ID,
                                                                start_latitude=last_request.start_latitude,
                                                                start_longitude=last_request.start_longitude,
                                                                end_latitude=last_request.end_latitude,
                                                                end_longitude=last_request.end_longitude)
        keyboard = [[InlineKeyboardButton('Ок, еду', url=deep_link)],
                    [InlineKeyboardButton('Хочу еще дешевле!', callback_data='cheaper')],
                    [InlineKeyboardButton('Хватит', callback_data='stop')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=chat_id, text='Теперь {}'.format(fixed), reply_markup=reply_markup)


# approximate price from Uber
def estimate_price(start_lat, start_long, end_lat, end_long):
    response = client.get_price_estimates(
        start_latitude=start_lat,
        start_longitude=start_long,
        end_latitude=end_lat,
        end_longitude=end_long,
        seat_count=2
    )

    high = response.json.get('prices')[0]['high_estimate']
    # this calculation is based on experience, not always correct
    fixed = int(high + high / 100 * 13)
    return fixed


def msg(bot, update):
    update.message.reply_text('Нажми /start для выбора начальной точки поездки')


def stop_notification(bot, update, chat_data):
    if 'job' not in chat_data:
        pass

    else:
        job = chat_data['job']
        job.schedule_removal()
        del chat_data['job']

    if 'cheap_notification' not in chat_data:
        pass

    else:
        cheap_notification = chat_data['cheap_notification']
        cheap_notification.schedule_removal()
        del chat_data['cheap_notification']

    bot.send_message(chat_id=chat_data['chat_id'],
                     text='Окей, больше не буду. Нажми /start для выбора начальной точки поездки')


def get_help(bot, update):
    update.message.reply_text('Нажми /start для выбора начальной точки поездки')


def greet_user(bot, update):
    location_keyboard = KeyboardButton(text="Отправить мое местоположение", request_location=True)
    custom_keyboard = [[location_keyboard]]
    update.message.reply_text('Привет, откуда едем?',
                              reply_markup=ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True))
    if not User.query.filter(User.chat_id == update.message.chat_id).first():
        user = User(update.message.chat.first_name, update.message.chat.last_name, update.message.chat_id)
        db_session.add(user)
        db_session.commit()
    return START_LOCATION


def get_start_location(bot, update):
    user_location = update.message.location
    update.message.reply_text('Отлично, куда едем?')
    user = User.query.filter(User.chat_id == update.message.chat_id).first()
    request = Request(start_latitude=user_location['latitude'], start_longitude=user_location['longitude'],
                      user_id=user.id)
    db_session.add(request)
    db_session.commit()
    return END_LOCATION


def get_end_location(bot, update, chat_data):
    user_location = update.message.location
    update.message.reply_text('Супер, сейчас посчитаю...')

    user = User.query.filter(User.chat_id == update.message.chat_id).first()
    request = Request.query.filter(Request.user_id == user.id).order_by(Request.id.desc()).first()
    request.end_latitude = user_location['latitude']
    request.end_longitude = user_location['longitude']
    request.requested = dt.datetime.now()
    db_session.commit()

    last_request = user.get_last_request()

    fixed = estimate_price(last_request.start_latitude, last_request.start_longitude,
                           last_request.end_latitude, last_request.end_longitude)

    chat_data['fare'] = fixed
    chat_data['chat_id'] = update.message.chat_id
    update.message.reply_text('Будет примерно {}'.format(fixed))

    fare = Fare(fare=fixed, time=dt.datetime.now(), request_id=last_request.id)
    db_session.add(fare)
    db_session.commit()
    return make_decision(bot, update)


def make_decision(bot, update):
    user = User.query.filter(User.chat_id == update.message.chat_id).first()
    last_request = user.get_last_request()

    deep_link = 'https://m.uber.com/ul/?action=setPickup&client_id={client_id}&pickup[formatted_address]=' \
                'start&pickup[latitude]={start_latitude}&pickup[longitude]={start_longitude}&' \
                'dropoff[formatted_address]=end&dropoff[latitude]={end_latitude}&' \
                'dropoff[longitude]={end_longitude}'.format(client_id=keys.UBER_CLIENT_ID,
                                                            start_latitude=last_request.start_latitude,
                                                            start_longitude=last_request.start_longitude,
                                                            end_latitude=last_request.end_latitude,
                                                            end_longitude=last_request.end_longitude)

    keyboard = [[InlineKeyboardButton('Ок, еду', url=deep_link)],
                [InlineKeyboardButton('Когда будет дешевле?', callback_data='cheaper')],
                [InlineKeyboardButton('Сообщай мне каждую минуту', callback_data='every_minute')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Ну что?', reply_markup=reply_markup)
    return ConversationHandler.END


def button(bot, update, job_queue, chat_data):
    query = update.callback_query
    chat_id = update.callback_query.message.chat.id

    if query.data == 'cheaper':
        bot.edit_message_text(text='Сообщу, как подешевеет. Нажми /stop для остановки',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

        cheap_notification = job_queue.run_repeating(notify_cheaper, 5, context=chat_id)
        chat_data['cheap_notification'] = cheap_notification

    elif query.data == 'every_minute':
        bot.edit_message_text(text='Для отмены пришли /stop',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

        job = job_queue.run_repeating(reply_price_every_minute, 50, context=chat_id)
        chat_data['job'] = job

    elif query.data == 'stop':
        stop_notification(bot, update, chat_data)


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
    dp.add_handler(CommandHandler('stop', stop_notification, pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.text, msg))
    dp.add_handler(CallbackQueryHandler(button, pass_job_queue=True, pass_chat_data=True))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', greet_user)],

        states={
            START_LOCATION: [MessageHandler(Filters.location, get_start_location)],
            END_LOCATION: [MessageHandler(Filters.location, get_end_location, pass_chat_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.info('Bot started')
    main()
