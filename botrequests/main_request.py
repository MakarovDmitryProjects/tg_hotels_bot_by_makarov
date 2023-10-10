"""
Модуль main_request.py
Описывает взаимодействие с Hotels API (rapidapi.com).
"""

import config
from telebot import types
from typing import Callable, Dict, List, Tuple, Union, Any
import requests
import json

city_url = 'https://hotels4.p.rapidapi.com/locations/v3/search'
hotel_url = 'https://hotels4.p.rapidapi.com/properties/v2/list'
detail_url = "https://hotels4.p.rapidapi.com/properties/v2/detail"
photo_url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'

headers = {
    "content-type": "application/json",
    'X-RapidAPI-Host': config.RAPIDHOST,
    'X-RapidAPI-Key': config.RAPIDAPIKEY
}


def location_search(message: types.Message) -> Dict[str, str]:
    """
    Выполнение HTTP-запроса к Hotels API (rapidapi.com) (Поиск городов).
    :param message: сообщение пользователя
    :return: словарь, содержащий сведения городов
    """

    querystring = {"q": message.text, "locale": "ru_RU"}
    headers["X-RapidAPI-Key"] = "6b8b325077msh1ea43dfe7b05001p1003bejsn334522aa35dc"
    response = requests.request("GET", city_url, headers=headers, params=querystring, timeout=10)
    data = json.loads(response.text)

    city_dict = {city['regionNames']['displayName']: city['essId']['sourceId']
                 for city in data['sr']}

    return city_dict


def hotels_search(data: Dict[str, Union[int, str, None, List[Union[int, float]], Dict[str, Union[str, List[str]]]]],
                  sorted_func: Callable) -> \
        Union[Tuple[Union[Dict[str, Dict[str, Union[str, None]]], None], Union[str, None]]]:
    """
    Выполнение HTTP-запроса к Hotels API (rapidapi.com) (поиск отелей).
    :param data: данные пользователя
    :param sorted_func: функция, выполняющая http-запрос
    :return: кортеж, содержащий словарь со сведениями отелей и url-ссылку
    """
    if data['sorted_func'] == 'bestdeal':
        hotels_data = sorted_func(user_city_id=data['city_id'], lang=data['lang'], cur=data['cur'],
                                  hotels_value=data['hotels_value'], hotel_url=hotel_url, detail_url=detail_url,
                                  headers=headers, price_range=data['price_range'],
                                  dist_range=data['dist_range'], check_in=data['check_in'], check_out=data['check_out'])
    else:
        hotels_data = sorted_func(user_city_id=data['city_id'], lang=data['lang'], cur=data['cur'],
                                  hotels_value=data['hotels_value'], hotel_url=hotel_url, detail_url=detail_url,
                                  headers=headers, check_in=data['check_in'], check_out=data['check_out'])
    return hotels_data


def photos_search(data: Dict[str, Union[int, str, None, List[Union[int, float]], Dict[str, Union[str, List[str]]]]],
                  hotel_id: int) -> List[Dict[str, Union[str, Any]]]:
    """
    Выполнение HTTP-запроса к Hotels API (rapidapi.com) (поиск фото).
    :param data: данные пользователя
    :param hotel_id: hotel id
    :return: список url-адресов фото отеля
    """

    photo_payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "propertyId": str(hotel_id)
    }
    headers["X-RapidAPI-Key"] = "6b8b325077msh1ea43dfe7b05001p1003bejsn334522aa35dc"

    photo_response = requests.request("POST", detail_url, headers=headers, json=photo_payload, timeout=10)
    photo_data = json.loads(photo_response.text)

    photos_address = [url['image']['url'] for url in photo_data['data']['propertyInfo']['propertyGallery']['images']][:data['photos_value']]
    return photos_address
