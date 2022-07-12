import re

from TBot.loaders.internet_loader import InternetLoader


def test_ip():
    il = InternetLoader('ILoader')
    res = il.get_server_ip(privileges=50)
    ip = res.get('text', False)
    assert ip, 'No response data'
    fnd = re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)
    if fnd:
        fnd = fnd.group(0)
        assert fnd
    else:
        assert False, f"Not ip in response ({res.get('text', '')})"
