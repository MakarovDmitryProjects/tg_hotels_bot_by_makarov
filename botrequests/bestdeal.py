import requests
import json
from typing import List, Tuple, Dict, Union


def bestdeal(user_city_id: str, lang: str, cur: str, hotels_value: int, hotel_url: str, detail_url: str,
             headers: Dict[str, str], check_in: str, check_out: str, price_range: List[int], dist_range: List[float]) -> \
        Union[Tuple[Union[Dict[str, Dict[str, Union[str, None]]], None], Union[str, None]]]:
    """
    HTTP-запрос к Hotels API (rapidapi.com) (запрос отелей).

    :param user_city_id: id города
    :param lang: язык пользователя
    :param cur: валюта пользователя
    :param hotels_value: кол-во отелей
    :param hotel_url: url-ссылка на отель
    :param detail_url: url-ссылка на детальное описание отеля
    :param headers: headers
    :param price_range: ценовой диапазон
    :param dist_range: диапазон расстояния
    :param check_in: дата заезда
    :param check_out: дата выезда
    :return: кортеж, содержащий словарь со сведениями отелей и url-ссылку
    """

    payload = {
        "currency": cur,
        "eapid": 1,
        "locale": lang,
        "destination": {"regionId": user_city_id},
        "checkInDate": {
            "day": int(check_in.split('-')[0]),
            "month": int(check_in.split('-')[1]),
            "year": int(check_in.split('-')[2])
        },
        "checkOutDate": {
            "day": int(check_out.split('-')[0]),
            "month": int(check_out.split('-')[1]),
            "year": int(check_out.split('-')[2])
        },
        "rooms": [
            {
                "adults": 1,
                "children": []
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": hotels_value,
        "sort": "DISTANCE_FROM_LANDMARK",
        "filters": {"price": {
            "max": int(price_range[0]),
            "min": int(price_range[1])
        }}
    }

    headers["X-RapidAPI-Key"] = "6b8b325077msh1ea43dfe7b05001p1003bejsn334522aa35dc"

    url = f'https://hotels.com/search.do?destination-id={user_city_id}&q-check-in={check_in}&q-check-out={check_out}' \
          f'&q-rooms=1&q-room-0-adults=2&q-room-0-children=0&f-price-min={min(price_range)}' \
          f'&f-price-max={max(price_range)}&f-price-multiplier=1&sort-order={payload["sort"]}'

    hotels_list = list()

    while len(hotels_list) < hotels_value:
        try:
            hotel_response = requests.request("POST", hotel_url, headers=headers, json=payload, timeout=10)
            hotel_data = json.loads(hotel_response.text)
            temp_hotels_list = hotel_data['data']['propertySearch']['properties']

            if not temp_hotels_list:
                return None, None
            for i_hotel in temp_hotels_list:
                distance = i_hotel['destinationInfo']['distanceFromDestination']['value']
                if float(distance) > max(dist_range):
                    raise ValueError('Превышено максимальное расстояние от центра города')
                elif float(distance) >= min(dist_range):
                    hotels_list.append(i_hotel)

            payload['eapid'] += 1

        except ValueError:
            break

    hotels_dict = {hotel['name']: {'id': hotel.get('id', '-'),
                                   'name': hotel.get('name', '-'),
                                   'price': hotel['price']['lead'].get('formatted', '-'),
                                   'destination': hotel['destinationInfo']['distanceFromDestination'].get('value', '-')}
                   for hotel in hotels_list}

    for hotel in hotels_dict.values():
        detail_payload = {
            "currency": "USD",
            "eapid": 1,
            "locale": "en_US",
            "siteId": 300000001,
            "propertyId": hotel['id']
        }

        detail_response = requests.request("POST", detail_url, headers=headers, json=detail_payload, timeout=10)
        detail_data = json.loads(detail_response.text)
        address_data = detail_data['data']['propertyInfo']['summary']['location']['address']
        hotel['address'] = address_data.get('addressLine', '-')

    return hotels_dict, url
