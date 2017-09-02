# -*- coding: utf-8 -*-

import api_keys as keys
import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from uber_rides.session import Session, OAuth2Credential
from uber_rides.client import UberRidesClient
from uber_rides.auth import AuthorizationCodeGrant
from uber_rides.errors import HTTPError
import json
import random
import datetime as dt
import urllib.parse as urlparse
from models import db_session, User, Request, Fare
from utils import make_deep_link, estimate_price, get_real_price, update_access_token, tuple_of_stickers

# states
START_LOCATION, END_LOCATION = range(2)


# get price depending on authorization. If the user is authorized, the price will be precise, otherwise it's estimation
def get_price_for_client(user, last_request):
    if user.uber_credentials:
        credential = user.uber_credentials
        credential_dict = json.loads(credential)
        oauth2credential = OAuth2Credential(
            client_id=credential_dict.get('client_id'),
            access_token=credential_dict.get('access_token'),
            expires_in_seconds=credential_dict.get('expires_in_seconds'),
            scopes=credential_dict.get('scopes'),
            grant_type=credential_dict.get('grant_type'),
            redirect_url=credential_dict.get('redirect_url'),
            client_secret=credential_dict.get('client_secret'),
            refresh_token=credential_dict.get('refresh_token'))
        session = Session(oauth2credential=oauth2credential)
        client = UberRidesClient(session)
        try:
            response = client.get_products(last_request.start_latitude, last_request.start_longitude)
            products = response.json.get('products')
            product_id = products[0].get('product_id')
            fixed = get_real_price(client, product_id, last_request.start_latitude, last_request.start_longitude,
                                   last_request.end_latitude, last_request.end_longitude)
        except HTTPError as e:
            if '401' in repr(e):
                credential_dict = update_access_token(credential_dict)
                user.uber_credentials = json.dumps(credential_dict)
                db_session.commit()
                oauth2credential = OAuth2Credential(
                    client_id=credential_dict.get('client_id'),
                    access_token=credential_dict.get('access_token'),
                    expires_in_seconds=credential_dict.get('expires_in_seconds'),
                    scopes=credential_dict.get('scopes'),
                    grant_type=credential_dict.get('grant_type'),
                    redirect_url=credential_dict.get('redirect_url'),
                    client_secret=credential_dict.get('client_secret'),
                    refresh_token=credential_dict.get('refresh_token'))
                session = Session(oauth2credential=oauth2credential)
                client = UberRidesClient(session)

                response = client.get_products(last_request.start_latitude, last_request.start_longitude)
                products = response.json.get('products')
                product_id = products[0].get('product_id')
                fixed = get_real_price(client, product_id, last_request.start_latitude, last_request.start_longitude,
                                       last_request.end_latitude, last_request.end_longitude)
            else:
                raise e
    else:
        session = Session(server_token=keys.UBER_SERVER_TOKEN)
        client = UberRidesClient(session)
        fixed = estimate_price(client, last_request.start_latitude, last_request.start_longitude,
                               last_request.end_latitude, last_request.end_longitude)
    return fixed


# price every minute
def reply_price_every_minute(bot, job):
    chat_id = job.context
    user = User.query.filter(User.chat_id == chat_id).first()
    last_request = user.get_last_request()

    fixed = get_price_for_client(user, last_request)

    fare = Fare(fare=fixed, time=dt.datetime.now(), request_id=last_request.id)
    db_session.add(fare)
    db_session.commit()

    deep_link = make_deep_link(last_request.start_latitude, last_request.start_longitude,
                               last_request.end_latitude, last_request.end_longitude)

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

    fixed = get_price_for_client(user, last_request)

    fare = Fare(fare=fixed, time=dt.datetime.now(), request_id=last_request.id)
    db_session.add(fare)
    db_session.commit()

    if fixed < min_price:
        cheap_notification.schedule_removal()
        deep_link = make_deep_link(last_request.start_latitude, last_request.start_longitude,
                                   last_request.end_latitude, last_request.end_longitude)

        keyboard = [[InlineKeyboardButton('Ок, еду', url=deep_link)],
                    [InlineKeyboardButton('Хочу еще дешевле!', callback_data='cheaper')],
                    [InlineKeyboardButton('Хватит', callback_data='stop')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=chat_id, text='Теперь {}'.format(fixed), reply_markup=reply_markup)


def msg(bot, update):
    update.message.reply_text('Нажми /start для выбора начальной точки поездки')


def stop_notification(bot, update, chat_data):
    if 'job' in chat_data:
        job = chat_data['job']
        job.schedule_removal()
        del chat_data['job']

    if 'cheap_notification' in chat_data:
        cheap_notification = chat_data['cheap_notification']
        cheap_notification.schedule_removal()
        del chat_data['cheap_notification']

    bot.send_message(chat_id=chat_data['chat_id'],
                     text='Окей, больше не буду. Нажми /start для выбора начальной точки поездки')


def get_help(bot, update):
    update.message.reply_text('Нажми /start для выбора начальной точки поездки')


def authorize(bot, update):
    auth_flow = AuthorizationCodeGrant(
        keys.UBER_CLIENT_ID,
        {'request'},
        keys.UBER_CLIENT_SECRET,
        keys.UBER_REDIRECT_URL,
    )
    auth_url = auth_flow.get_authorization_url()
    parsed_url = urlparse.urlparse(auth_url)
    state = urlparse.parse_qs(parsed_url.query)['state'][0]

    user = User.query.filter(User.chat_id == update.message.chat_id).first()
    user.uber_state = state
    db_session.commit()

    keyboard = [[InlineKeyboardButton('Авторизоваться', url=auth_url)],
                [InlineKeyboardButton('Готово', callback_data='auth_done')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Нажми готово по завершении', reply_markup=reply_markup)


def check_authorization(bot, chat_id):
    user = User.query.filter(User.chat_id == chat_id).first()
    if not user.uber_credentials:
        bot.send_message(chat_id=chat_id, text='Что-то пошло не так, попробуй авторизоваться еще раз /auth или '
                                               'отправь начальную точку поездки для примерной цены')
    else:
        bot.send_message(chat_id=chat_id,
                         text='Авторизация прошла успешно. Выбери начальную точку поездки')


def greet_user(bot, update):
    location_keyboard = KeyboardButton(text="Отправить мое местоположение", request_location=True)
    custom_keyboard = [[location_keyboard],
                       ['/start', '/cancel']]
    update.message.reply_text('Привет, откуда едем? Для точной цены надо авторизоваться /auth',
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
    ReplyKeyboardRemove()
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
    fixed = get_price_for_client(user, last_request)

    if user.uber_credentials:
        update.message.reply_text('Будет {}'.format(fixed))
    else:
        update.message.reply_text('Будет примерно {}'.format(fixed))

    chat_data['fare'] = fixed
    chat_data['chat_id'] = update.message.chat_id

    fare = Fare(fare=fixed, time=dt.datetime.now(), request_id=last_request.id)
    db_session.add(fare)
    db_session.commit()
    return make_decision(bot, update)


def make_decision(bot, update):
    user = User.query.filter(User.chat_id == update.message.chat_id).first()
    last_request = user.get_last_request()

    deep_link = make_deep_link(last_request.start_latitude, last_request.start_longitude,
                               last_request.end_latitude, last_request.end_longitude)

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

    elif query.data == 'auth_done':
        check_authorization(bot, chat_id)


def cancel(bot, update):
    update.message.reply_text('Пока! Нажми /start для начала новой поездки')
    return ConversationHandler.END


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )


def reply_sticker(bot, update):
    random_sticker = random.choice(tuple_of_stickers)
    bot.send_sticker(update.message.chat_id, random_sticker)


def main():
    updater = Updater(keys.TELEGRAM_TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('help', get_help))
    dp.add_handler(CommandHandler('stop', stop_notification, pass_chat_data=True))
    dp.add_handler(CommandHandler('auth', authorize))
    dp.add_handler(MessageHandler(Filters.text, msg))
    dp.add_handler(MessageHandler(Filters.sticker, reply_sticker))
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
