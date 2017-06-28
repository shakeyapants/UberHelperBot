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
    # del user_rides[update.message.chat_id]
    return make_decision(bot, update)


def make_decision(bot, update):
    keyboard = [[InlineKeyboardButton('Ок, еду', callback_data='ok')],
                [InlineKeyboardButton('Когда будет дешевле?', callback_data='cheaper')],
                [InlineKeyboardButton('Сообщай мне каждую минуту', callback_data='every_minute')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Ну что?', reply_markup=reply_markup)
    return ConversationHandler.END


def button(bot, update):
    query = update.callback_query

    if query.data == 'ok':
        bot.edit_message_text(text='Хорошего пути!',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    elif query.data == 'cheaper':
        # call some function
        bot.edit_message_text(text='Сообщу, как подешевеет',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    elif query.data == 'every minute':
        # call some function
        bot.edit_message_text(text='Для отмены пришли /cancel',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def get_start_point(bot, update):
    user_text = update.message.text
    start_coordinates = re.findall(pattern, user_text)
    if not start_coordinates:
        update.message.reply_text('Такого не бывает!')
    else:
        dict_start_coordinates = user_rides.setdefault(update.message.chat_id, {'start': None})
        dict_start_coordinates['start'] = start_coordinates
    if check_endpoints(update.message.chat_id) is True:
        fixed = estimate_price(user_rides[update.message.chat_id])
        del user_rides[update.message.chat_id]
        update.message.reply_text('Будет примерно {}'.format(fixed))


def get_end_point(bot, update):
    user_text = update.message.text
    end_coordinates = re.findall(pattern, user_text)
    if not end_coordinates:
        update.message.reply_text('Такого не бывает!')
    else:
        dict_end_coordinates = user_rides.setdefault(update.message.chat_id, {'end': None})
        dict_end_coordinates['end'] = end_coordinates
    if check_endpoints(update.message.chat_id) is True:
        fixed = estimate_price(user_rides[update.message.chat_id])
        del user_rides[update.message.chat_id]
        update.message.reply_text('Будет примерно {}'.format(fixed))


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
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
    dp.add_handler(CommandHandler('от', get_start_point))
    dp.add_handler(CommandHandler('до', get_end_point))
    #dp.add_handler(MessageHandler(Filters.text, msg))
    dp.add_handler(CallbackQueryHandler(button))

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
