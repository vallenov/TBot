import re
import os
from bs4 import BeautifulSoup

import config
from loaders.internet_loader import InternetLoader
from loaders.loader import LoaderRequest

from helpers import (
    check_config_attribute
)


def test_ip():
    il = InternetLoader()
    request = LoaderRequest(text='', privileges=50, chat_id='')
    res = il.get_server_ip(request)
    ip = res.text
    assert ip, 'No response data'
    fnd = re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)
    if fnd:
        fnd = fnd.group(0)
        assert fnd
    else:
        assert False, f"Not ip in response ({res.text})"


def test_site_to_lxml():
    il = InternetLoader()
    res = il.site_to_lxml('https://ifconfig.me/ip')
    assert res, 'No response data'
    assert isinstance(res, BeautifulSoup), 'Wrong response type'
    fnd = re.search(r'^<html><body><p>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}</p></body></html>$', str(res))
    if fnd:
        fnd = fnd.group(0)
        assert fnd
    else:
        assert False, f'Wrong response data {res}'


def test_routes():
    """Test all the routes"""
    il = InternetLoader()
    url = check_config_attribute('exchange_url')
    res = il.regular_request(url)
    assert res.status_code == 200


def test_get_exchange():
    il = InternetLoader()
    request = LoaderRequest(text='', privileges=30, chat_id='')
    res = il.get_exchange(request)
    search_raw = re.search(r'\D{3}', res.text)
    assert search_raw
    currency = search_raw.group(0)
    assert currency in config.EXCHANGES_CURRENCIES


def test_get_weather():
    il = InternetLoader()
    request = LoaderRequest(text='weather Москва', privileges=30, chat_id='')
    res = il.get_weather(request)
    search_raw = re.search(r'weather_.*\.png', res.photo)
    assert search_raw
    photo_path = search_raw.group(0)
    assert os.path.exists(os.path.join('tmp', photo_path))
