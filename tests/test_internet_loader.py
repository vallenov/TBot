import re
from bs4 import BeautifulSoup

from loaders.internet_loader import InternetLoader


def test_ip():
    il = InternetLoader()
    res = il.get_server_ip(privileges=50)
    ip = res.get('text', False)
    assert ip, 'No response data'
    fnd = re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)
    if fnd:
        fnd = fnd.group(0)
        assert fnd
    else:
        assert False, f"Not ip in response ({res.get('text', '')})"


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
