import re
import os
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import pytest

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


@pytest.mark.asyncio
async def test_routes():
    """Test all the routes"""
    il = InternetLoader()
    tasks = []
    il.async_url_data = []
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Connection': 'close'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        for name, url in config.LINKS.items():
            if name in (
                'system-monitor'
            ):
                continue
            url = check_config_attribute(name)
            tasks.append(asyncio.create_task(il._get_url(session, url)))
        await asyncio.gather(*tasks)
        for res in il.async_url_data:
            assert res.status == 200


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
