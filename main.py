from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

import re

from PIL import Image, ImageDraw, ImageFont
import random

TOKEN = ""

message_list = []
user_score_dict = {}

get_msg_btn = 'Получить письмо'
send_msg_btn = 'Отправить письмо'
cancel_btn = 'отмена'

reply_keyboard = [
    [get_msg_btn],
    [send_msg_btn],
]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

CHOOSING, TYPING_REPLY = range(2)


def made_photo(caption):
    import textwrap
    wrapper = textwrap.TextWrapper(width=45)
    word_list = wrapper.wrap(text=caption)
    caption_new = ''
    for ii in word_list[:-1]:
        caption_new = caption_new + ii + '\n'
    caption_new += word_list[-1]

    image = Image.open(r"template1.png")
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(r"ofont.ru_Kobzar KS.ttf", size=35)
    w_text, h_text = draw.textsize(caption_new, font=font)
    w_image, h_image = image.size

    print(w_text, h_text)
    print(w_image, h_image)

    x, y = 0.5 * (w_image - w_text), 0.5 * (h_image - h_text)

    draw.multiline_text((x, y), caption_new, (0, 0, 0), font=font)
    image.save('output.png')
    photo = open(r"output.png", 'rb')
    return photo


def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.chat.id
    user_score_dict[user_id] = 0
    update.message.reply_text(
        "Привет, я бот с посланиями! Я могу отправлять твои собщения незнакомцам и получать сообщения от них",
        reply_markup=markup
    )
    return CHOOSING


def help(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Номера телефонов: \n03 \n112\n103\n051-8-495-051",
        reply_markup=markup
    )
    return CHOOSING


def get_message(update: Update, context: CallbackContext):
    print("Message list", message_list)

    user_id = update.message.chat.id

    print(f'User id: {user_id} with score:{user_score_dict[user_id]} try to get message')

    if user_score_dict[user_id] > 0:
        chat_id = update.message.chat_id
        inx_in_msg_list = []
        for i in range(len(message_list)):
            if message_list[i].chat_id != chat_id:
                inx_in_msg_list.append(i)

        is_empty = True if (len(inx_in_msg_list) == 0) else False
        if not is_empty:

            i = random.randrange(len(inx_in_msg_list))  # get random index

            inx_in_frs_list = inx_in_msg_list[i]
            message_list[inx_in_frs_list], message_list[-1] = message_list[-1], message_list[
                inx_in_frs_list]  # swap with the last element
            message = message_list.pop()
            print(message)
            text = message.text

            photo = made_photo(text)
            update.message.reply_photo(photo, reply_markup=markup)

            print(update.message.chat_id)

            frst_name = update.message.chat.first_name if update.message.chat.first_name is not None else ' '
            sec_name = update.message.chat.last_name if update.message.chat.last_name is not None else ' '
            username = '@' + update.message.chat.username if update.message.chat.username is not None else ' '
            id_us = 'id:' + str(update.message.chat.id) if update.message.chat.id is not None else ' '
            message.reply_text(
                f'Твое сообщение было прочитано. \nЕго прочитал: \n[{frst_name} {sec_name}\n{username}\n{id_us}]',
                reply_markup=markup, )
            print(message_list)

            user_score_dict[user_id] = user_score_dict[user_id] - 1
        else:
            update.message.reply_text('Извини, нет сообщений', reply_markup=markup, )
        return CHOOSING
    else:
        update.message.reply_text('Сперва отправь какое-нибудь сообщение', reply_markup=markup, )
    return CHOOSING


def send_message(update: Update, context: CallbackContext):
    update.message.reply_text(f'Напиши сообщение, которое хочешь отправить. Если передумал, напиши *{cancel_btn}*',
                              parse_mode='Markdown'
                              )
    return TYPING_REPLY


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Отменяем.')
    update.message.reply_text('Выбери, что ты хочешь сделать', reply_markup=markup, )

    return CHOOSING


def received_information(update: Update, context: CallbackContext):
    if len(update.message.text) > 450:
        update.message.reply_text("Слишком длинное сообщение:( \nПостарайся сформулировать мысль покороче")
        return TYPING_REPLY
    else:
        message_list.append(update.message)
        update.message.reply_text("Спасибо за сообщение! Мы тебя оповестим, когда твое сообщение будет прочитано.",
                                  reply_markup=markup)
        user_id = update.message.chat.id
        user_score_dict[user_id] = user_score_dict[user_id] + 1

        print(f'User id:{user_id} try to send message: {update.message}')
        return CHOOSING


def incorrect_input(update: Update, context: CallbackContext):
    update.message.reply_text('Некорректный ввод, попробуй еще раз', reply_markup=markup)


def incorrect_text_input(update: Update, context: CallbackContext):
    update.message.reply_text('Некорректный ввод, попробуй еще раз')


def done(update: Update, context: CallbackContext):
    update.message.reply_text('Ok')
    return CHOOSING


def main() -> None:
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    for_reg_cancel = re.compile(cancel_btn, re.IGNORECASE)
    for_reg_get = '^' + get_msg_btn + '$'
    for_reg_send = '^' + send_msg_btn + '$'

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex(for_reg_get), get_message),
                MessageHandler(Filters.regex(for_reg_send), send_message),
                MessageHandler(Filters.command('help'), help),
                MessageHandler(Filters.text & ~(
                            Filters.regex(for_reg_get) | Filters.regex(for_reg_send) | Filters.command('help')),
                               incorrect_input)
            ],

            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex(for_reg_get) | Filters.regex(
                        for_reg_send) | Filters.regex(for_reg_cancel)),
                    received_information,
                ),
                MessageHandler(Filters.command | Filters.regex(for_reg_get) | Filters.regex(for_reg_send),
                               incorrect_text_input),
                MessageHandler(Filters.regex(for_reg_cancel), cancel),

            ],

        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
