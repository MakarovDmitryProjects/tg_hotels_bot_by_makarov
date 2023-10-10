import telebot
import re
import config
from data_manager import *

bot = telebot.TeleBot(config.token)


@bot.message_handler(content_types='text')
def start_messages(message):
    """Приветствие и предложение выбрать категорию в виде Inline клавиатуры """
    if message.text in ['/start', '/hello_world', '/help']:
        bot.send_message(message.from_user.id, 'Привет, {}! Здесь Вы можете подобрать лучшие предложения отелей по '
                                               'заданным критериям'.format(message.from_user.first_name))
        keyboard = types.InlineKeyboardMarkup()
        key_lowprice = types.InlineKeyboardButton(text='Самые дешёвые', callback_data='/lowprice')
        keyboard.add(key_lowprice)
        key_highprice = types.InlineKeyboardButton(text='Самые дорогие', callback_data='/highprice')
        keyboard.add(key_highprice)
        key_bestdeal = types.InlineKeyboardButton(text='Лучшая цена', callback_data='/bestdeal')
        keyboard.add(key_bestdeal)
        key_history = types.InlineKeyboardButton(text='История поиска', callback_data='/history')
        keyboard.add(key_history)
        bot.send_message(message.from_user.id, text='Выберите категорию', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Я вас не понимаю. Напиши /help.")


@bot.callback_query_handler(func=lambda call: call.data in ['/lowprice', '/highprice', '/bestdeal'])
def choosing_category(call) -> None:
    """Установка сортирующей функции, определение следующего шага обработчика"""
    set_sorted_func(chat_id=call.message.chat.id, func=call.data)
    bot.send_message(chat_id=call.message.chat.id, text='Какой город ищем?')
    bot.register_next_step_handler(message=call.message, callback=search_city)


@bot.callback_query_handler(func=lambda call: call.data in ['/history'])
def history(call) -> None:
    """Вывод истории поиска"""
    if call.data == '/history':
        i_history = get_history(call.message.chat.id)
        if i_history:
            message_list = list()
            for i_query, i_hotels in i_history.items():
                location = re.search('>(.+?)</a>', i_query)
                date = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', i_query)
                func = location.group(1) + '\n' + str(*date)
                temp = bot.send_message(chat_id=call.message.chat.id, text='{func}\n\n{hotels}'.format(
                    func=func, hotels='\n'.join(i_hotels)), parse_mode='HTML', disable_web_page_preview=True)

                message_list.append(str(temp.id))
            else:
                set_message_list(chat_id=call.message.chat.id, i_key=message_list[-1], i_value=message_list)
                keyword = types.InlineKeyboardMarkup(row_width=2)
                buttons = [types.InlineKeyboardButton(text=text, callback_data=text)
                           for text in ('Очистить', 'Скрыть')]
                keyword.add(*buttons)
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=int(message_list[-1]),
                                              reply_markup=keyword)
        else:
            bot.send_message(chat_id=call.message.chat.id, text='Ваша история поиска пуста!')


@bot.callback_query_handler(func=lambda call: call.data in ('Очистить', 'Скрыть'))
def operation_for_history(call: types.CallbackQuery) -> None:
    """Обработка сообщений истории поиска (Очистить, Скрыть)"""
    if call.data in [value for value in ('Очистить', 'Скрыть')]:
        clear_history(call.message.chat.id)
    for i_message_id in get_message_list(chat_id=call.message.chat.id, message_id=call.message.id):
        bot.delete_message(chat_id=call.message.chat.id, message_id=int(i_message_id))


def search_city(message: types.Message) -> None:
    """Обработка запроса пользователя по поиску города, вывод Inline клавиатуры с результатами"""
    temp = bot.send_message(message.chat.id, text='Выполняю поиск...', parse_mode='HTML')
    city_list = get_city_list(message)
    keyboard = types.InlineKeyboardMarkup()
    if not city_list:
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id, text='Город не найден', parse_mode='HTML')
    else:
        for city_name, city_id in city_list.items():
            keyboard.add(types.InlineKeyboardButton(text=city_name, callback_data=city_id))
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id, text='Результат поиска',
                              reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def city_handler(call: types.CallbackQuery) -> None:
    """Обработка данных искомого города (id, name), определение следующего шага обработчика"""
    set_city(call.message.chat.id, call.data)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    if flag_advanced_question(call.message.chat.id):
        ask_for_price_range(call.message)
    else:
        ask_for_hotels_value(call.message)


def ask_for_price_range(message: types.Message) -> None:
    """Запрос ценового диапазона у пользователя, определение следующего шага обработчика"""
    bot.send_message(chat_id=message.chat.id, text='Уточните ценовой диапазон за ночь (Долларов):'
                                                   '\n(В формате например: 1000-2000)')
    bot.register_next_step_handler(message=message, callback=ask_for_dist_range)


def ask_for_dist_range(message: types.Message) -> None:
    """Обработка значений ценового диапазона пользователя, запрос диапазона дистанции,
    определение следующего шага обработчика"""
    price_range = list(set(map(int, map(lambda string: string.replace(',', '.'),
                                        re.findall(r'\d+[.,\d+]?\d?', message.text)))))
    if len(price_range) != 2:
        raise ValueError('Range Error')
    else:
        set_price_range(chat_id=message.chat.id, value=price_range)
        bot.send_message(chat_id=message.chat.id, text='Уточните диапазон расстояния от центра (км), на котором '
                                                       'находится отель: '
                                                       '\n(В формате например: 1-3)')
        bot.register_next_step_handler(message=message, callback=ask_for_hotels_value)


def ask_for_hotels_value(message: types.Message) -> None:
    """Обработка значений диапазона дистанции пользователя, запрос количества отелей,
    определение следующего шага обработчика"""
    if flag_advanced_question(message.chat.id):
        dist_range = list(set(map(float, map(lambda string: string.replace(',', '.'),
                                             re.findall(r'\d+[.,\d+]?\d?', message.text)))))
        if len(dist_range) != 2:
            raise ValueError('Range Error')
        else:
            set_dist_range(chat_id=message.chat.id, value=dist_range)
    bot.send_message(chat_id=message.chat.id, text='Укажите дату заезда (в формате ДД-ММ-ГГГГ)')
    bot.register_next_step_handler(message=message, callback=ask_for_check_in)


def ask_for_check_in(message: types.Message) -> None:
    set_check_in(chat_id=message.chat.id, value=message.text)
    bot.send_message(chat_id=message.chat.id, text='Укажите дату выезда (в формате ДД-ММ-ГГГГ)')
    bot.register_next_step_handler(message=message, callback=ask_for_check_out)


def ask_for_check_out(message: types.Message) -> None:
    set_check_out(chat_id=message.chat.id, value=message.text)
    bot.send_message(chat_id=message.chat.id, text='Сколько отелей смотрим? (не более 10)')
    bot.register_next_step_handler(message=message, callback=photo_needed)


def photo_needed(message: types.Message) -> None:
    """Обработка значения кол-ва отелей пользователя, запрос необходимости вывода фото в виде Inline клавиатуры"""
    set_hotels_value(chat_id=message.chat.id, value=abs(int(message.text)))
    keyboard = types.InlineKeyboardMarkup()
    [keyboard.add(types.InlineKeyboardButton(x, callback_data=x)) for x in ('Да', 'Нет')]
    bot.send_message(message.chat.id, text='Интересуют фотографии отелей?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ('Да', 'Нет'))
def set_photo_needed(call: types.CallbackQuery) -> None:
    """Обработка ответа пользователя о необходимости вывода фото, определение хода действий."""
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    if call.data == 'Да':
        set_needed_photo(chat_id=call.message.chat.id, value=True)
        number_of_photo(call.message)
    else:
        set_needed_photo(chat_id=call.message.chat.id, value=False)
        result(call.message)


def number_of_photo(message: types.Message) -> None:
    """Запрос кол-ва фото у пользователя, определение следующего шага обработчика"""
    bot.send_message(chat_id=message.chat.id,
                     text='Сколько фотографий по каждому отелю? (не более 10)')
    bot.register_next_step_handler(message=message, callback=result)


def result(message: types.Message) -> None:
    """Обработка значения кол-ва фото, выполнение поиска вариантов, представление результатов"""
    if get_needed_photo(chat_id=message.chat.id):
        set_photos_value(chat_id=message.chat.id, value=abs(int(message.text)))
    temp = bot.send_message(chat_id=message.chat.id, text='Выполняю поиск...')
    hotels_dict, search_link = get_hotels(user_id=message.chat.id)

    if hotels_dict:
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id,
                              text='Я нашёл для вас следующие варианты...')
        for index, i_data in enumerate(hotels_dict.values()):
            if index + 1 > get_hotels_value(chat_id=message.chat.id):
                break
            text = '\n\n{e_hotel}{name}{e_hotel}' \
                   '\n\n{e_address}Адрес: <a href="{address_link}">{address}</a>' \
                   '\n\n{e_dist}Расстояние от центра (км): {distance}' \
                   '\n\n{e_price}Цена за ночь: {price}' \
                   '\n\n{e_link}<a href="{link}">Подробнее на hotels.com</a>'.format(
                    name=i_data['name'], address=i_data['address'], distance=i_data['destination'],
                    price=i_data['price'], e_hotel=emoji['hotel'], e_address=emoji['address'],
                    e_dist=emoji['landmarks'], e_price=emoji['price'], e_link=emoji['link'],
                    link='https://hotels.com/ho' + str(i_data['id']),
                    address_link='https://www.google.ru/maps/place/' + i_data['address'])

            if get_needed_photo(chat_id=message.chat.id):
                photo_list = get_photos(user_id=message.chat.id, hotel_id=int(i_data['id']), text=text)
                for i_size in ['z', 'y', 'd', 'n', '_']:
                    try:
                        bot.send_media_group(chat_id=message.chat.id, media=photo_list)
                        break
                    except telebot.apihelper.ApiTelegramException:
                        photo_list = [types.InputMediaPhoto(caption=obj.caption, media=obj.media[:-5] + f'{i_size}.jpg',
                                                            parse_mode=obj.parse_mode) for obj in photo_list]
            else:
                bot.send_message(message.chat.id, text, parse_mode='HTML', disable_web_page_preview=True)

        bot.send_message(chat_id=message.chat.id,
                         text='Не нашли подходящий вариант?\nЕщё больше отелей по вашему запросу\\: [смотреть]({link})'
                              '\nХотите продолжить работу с ботом? /start'.format(link=search_link),
                         parse_mode='MarkdownV2', disable_web_page_preview=True)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id,
                              text='По вашему запросу ничего не найдено...\nХотите продолжить работу с ботом? /start')


bot.polling(none_stop=True, interval=0)
