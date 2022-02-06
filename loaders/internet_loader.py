import datetime
import random
import logging
import traceback

import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp

from loaders.loader import Loader

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class InternetLoader(Loader):

    @staticmethod
    def _site_to_lxml(url: str) -> BeautifulSoup or None:
        """
        Get site and convert it to the lxml

        :param url: https://site.com/
        :return: BeautifulSoup object
        """
        try:
            soup = BeautifulSoup(requests.get(url).text, 'lxml')
        except Exception as _ex:
            logger.exception(f'Exception in {__name__}:\n{_ex}')
            return None
        else:
            logger.info(f'Get successful ({url})')
        return soup

    def get_exchange(self) -> dict:
        """
        Get exchange from internet
        :param:
        :return: string like {'USD': '73,6059', 'EUR':'83,1158'}
        """
        logger.info('get_exchange')
        resp = {}
        if self.config.has_option('URL', 'exchange_url'):
            exchange_url = self.config['URL']['exchange_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        ex = ['USD', 'EUR']
        soup = InternetLoader._site_to_lxml(exchange_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        parse = soup.find_all('tr')
        for item in parse[1:]:
            inf = item.find_all('td')
            if inf[1].text not in ex:
                continue
            '''
            Structure of inf:
            tmp = {}
            tmp['id'] = inf[0].text
            tmp['name'] = inf[1].text
            tmp['e'] = inf[2].text
            tmp['descr'] = inf[3].text
            tmp['exchange'] = inf[4].text
            '''
            resp[inf[1].text] = inf[4].text
        resp['res'] = 'OK'
        return resp

    def get_weather(self) -> dict:
        """
        Get weather from internet
        :param:
        :return: dict like {'Сегодня': '10°/15°', 'ср 12': '11°/18°'}
        """
        logger.info('get_weather')
        resp = {}
        if self.config.has_option('URL', 'weather_url'):
            weather_url = self.config['URL']['weather_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(weather_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        parse = soup.find_all('div', class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
        for i in parse:
            h2 = i.find('h2')
            div = i.find('div')
            span = div.find_all('span')
            span = list(map(lambda x: x.text, span))
            resp[h2.text] = ''.join(span[:-1])
        resp['res'] = 'OK'
        return resp

    def get_quote(self) -> dict:
        """
        Get quote from internet
        :param:
        :return: dict like {'quote1': 'author1', 'quote2: 'author2'}
        """
        logger.info('get_quote')
        resp = {}
        if self.config.has_option('URL', 'quote_url'):
            quote_url = self.config['URL']['quote_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(quote_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        quotes = soup.find_all('div', class_='quote')
        for quote in quotes:
            author = quote.find('a')
            text = quote.find('div', class_='quote_name')
            resp[text.text] = author.text
        random_key = random.choice(list(resp.keys()))
        return {'res': 'OK', random_key: resp[random_key]}

    def get_wish(self) -> dict:
        """
        Get wish from internet
        :param:
        :return: wish string
        """
        logger.info('get_wish')
        resp = {}
        if self.config.has_option('URL', 'wish_url'):
            wish_url = self.config['URL']['wish_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(wish_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        wishes = soup.find_all('ol')
        wish_list = wishes[0].find_all('li')
        resp['res'] = 'OK'
        resp[1] = random.choice(wish_list).text
        return resp

    def get_news(self, text: str) -> dict:
        """
        Get news from internet
        :param:
        :return: wish string
        """
        logger.info('get_news')
        resp = {}
        count = 5
        lst = text.split(' ')
        if len(lst) > 1:
            try:
                count = int(lst[1])
            except ValueError:
                resp['res'] = 'ERROR'
                resp['descr'] = "Count of news is not number"
                return resp
        if self.config.has_option('URL', 'news_url'):
            news_url = self.config['URL']['news_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(news_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        news = soup.find_all('div', class_='cell-list__item-info')
        for n in news:
            news_time = n.find('span', class_='elem-info__date')
            text = n.find('span', class_='share')
            if news_time and text:
                resp[news_time.text] = text.get('data-title')
            if len(resp) == count:
                break
        resp['res'] = 'OK'
        return resp

    def get_affirmation(self) -> dict:
        """
        Get affirmation from internet
        :param:
        :return: affirmation string
        """
        logger.info('get_affirmationx')
        resp = {}
        if self.config.has_option('URL', 'affirmation_url'):
            affirmation_url = self.config['URL']['affirmation_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(affirmation_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        aff_list = []
        ul = soup.find_all('ul')
        for u in ul:
            li = u.find_all('em')
            for em in li:
                if em.text[0].isupper():
                    aff_list.append(em.text)
        resp['res'] = 'OK'
        resp[1] = random.choice(aff_list)
        return resp

    async def _get_url(self, session, url) -> None:
        async with session.get(url) as res:
            data = await res.text()
            if res.status == 200:
                logger.info(f'Get successful ({url})')
            else:
                logger.error(f'Get unsuccessful ({url})')
            self.async_url_data.append(data)

    async def async_events(self) -> dict:
        """
        Get events from internet (async)
        :param:
        :return: events digest
        """
        logger.info('get_events')
        self.async_url_data = []
        tasks = []
        resp = {}
        if self.config.has_option('URL', 'events_url'):
            events_url = self.config['URL']['events_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        async with aiohttp.ClientSession() as session:
            tasks.append(asyncio.create_task(self._get_url(session, events_url)))
            await asyncio.gather(*tasks)
            tasks = []
            soup = BeautifulSoup(self.async_url_data.pop(), 'lxml')
            links = {}
            div = soup.find_all('div', class_='site-nav-events')
            raw_a = div[0].find_all('a')
            for a in raw_a:
                links[a.text] = a.get('href')
            for _, link in links.items():
                tasks.append(asyncio.create_task(self._get_url(session, link)))
            await asyncio.gather(*tasks)
            for raw in self.async_url_data:
                events_links = []
                soup_curr = BeautifulSoup(raw, 'lxml')
                name = soup_curr.find('title').text.split('.')[0]
                raw_div = soup_curr.find('div', class_='feed-container')
                article = raw_div.find_all('article', class_='post post-rect')
                for art in article:
                    h2s = art.find_all('h2', class_='post-title')
                    for raw_h2 in h2s:
                        a = raw_h2.find('a')
                        descr = a.text.replace('\n', '')
                        events_links.append(f"{descr}\n{a.get('href')}\n")
                resp[name] = random.choice(events_links)
            resp['res'] = 'OK'
            return resp

    def get_events(self) -> dict:
        """
        Get events from internet
        :param:
        :return: events digest
        """
        logger.info('get_events')
        resp = {}
        if self.config.has_option('URL', 'events_url'):
            events_url = self.config['URL']['events_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(events_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        links = {}
        div = soup.find_all('div', class_='site-nav-events')
        raw_a = div[0].find_all('a')
        for a in raw_a:
            links[a.text] = a.get('href')
        for name, link in links.items():
            events_links = []
            name = name.replace('\n', '')
            raw_data = InternetLoader._site_to_lxml(link)
            h2s = raw_data.find_all('h2', class_='post-title')
            for raw_h2 in h2s:
                a = raw_h2.find('a')
                descr = a.text.replace('\n', '')
                events_links.append(f"{descr}\n{a.get('href')}\n")
            resp[name] = random.choice(events_links)
        resp['res'] = 'OK'
        return resp

    def get_restaurant(self) -> dict:
        """
        Get restaurant from internet
        :param:
        :return: restaurant string
        """
        logger.info('get_restaurant')
        resp = {}
        if self.config.has_option('URL', 'restaurant_url'):
            restaurant_url = self.config['URL']['restaurant_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(restaurant_url + '/msk/catalog/restaurants/all/')
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        div_nav_raw = soup.find('div', class_='pagination-wrapper')
        a_raw = div_nav_raw.find('a')
        page_count = int(a_raw.get('data-nav-page-count'))
        rand_page = random.choice(range(1, page_count+1))
        if rand_page > 1:
            soup = InternetLoader._site_to_lxml(self.config['URL']['restaurant_url']
                                           + '/msk/catalog/restaurants/all/'
                                           + f'?page={rand_page}')
        names = soup.find_all('a', class_='name')
        restaurant = random.choice(names)
        soup = InternetLoader._site_to_lxml(self.config['URL']['restaurant_url'] + restaurant.get('href'))
        div_raw = soup.find('div', class_='props one-line-props')
        final_restaurant = dict()
        final_restaurant[1] = restaurant.text
        for d in div_raw:
            name = d.find('div', class_='name')
            if name:
                name = name.text
            value = d.find('a')
            if value:
                value = value.text.strip().replace('\n', '')
            if name is not None and value is not None:
                final_restaurant[name] = value
        final_restaurant[2] = self.config['URL']['restaurant_url'] + restaurant.get('href')
        final_restaurant['res'] = 'OK'
        return final_restaurant

    def get_poem(self) -> dict:
        """
        Get respoesy from internet
        :param:
        :return: poesy string
        """
        logger.info('get_poesy')
        resp = {}
        if self.config.has_option('URL', 'poesy_url'):
            poesy_url = self.config['URL']['poesy_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(poesy_url)
        if soup is None:
            resp['res'] = 'ERROR'
            return resp

        div_raw = soup.find('div', class_='_2uPBE')
        a_raw = div_raw.find_all('a', class_='GmJ5E')
        count = int(a_raw[-1].text)
        rand = random.randint(1, count)
        if rand > 1:
            soup = InternetLoader._site_to_lxml(self.config['URL']['poesy_url'] + f'?page={rand}')
        poems_raw = soup.find('div', class_='_2VELq')
        poems_raw = poems_raw.find_all('div', class_='_1jGw_')
        rand_poem_raw = random.choice(poems_raw)
        href = rand_poem_raw.find('a', class_='_2A3Np').get('href')
        link = '/'.join(self.config['URL']['poesy_url'].split('/')[:-3]) + href

        soup = InternetLoader._site_to_lxml(link)

        div_raw = soup.find('div', class_='_1MTBU _3RpDE _47J4f _3IEeu')
        author = div_raw.find('div', class_='_14JnI').text
        name = div_raw.find('div', class_='_2jzeL').text
        strings_raw = div_raw.find('div', class_='_3P9bi')
        year = ''
        year_raw = strings_raw.find('div')
        if year_raw:
            year = f'\n\n{year_raw.text}'
        raw_p = strings_raw.find_all('p', class_='')
        quatrains = []
        for p in raw_p:
            quatrain = p.decode()
            quatrain = quatrain.replace('<p class="">', '')
            quatrain = quatrain.replace('<strong>', '\t')
            quatrain = quatrain.replace('</strong>', '')
            quatrain = quatrain.replace('<em>', '')
            quatrain = quatrain.replace('</em>', '')
            quatrain = quatrain.replace('</p>', '')
            quatrain = quatrain.replace('<br/>', '\n')
            quatrains.append(quatrain)
        poem = '\n\n'.join(quatrains)
        resp['res'] = 'OK'
        resp[author] = f'\n\n{name}\n\n{poem}{year}'
        return resp

    def get_phone_number_info(self, number) -> dict:
        """
        Get phone number info from internet
        :param:
        :return: poesy string
        """
        logger.info('get_phone_number_info')
        resp = {}
        if self.config.has_option('URL', 'kodi_url'):
            kodi_url = self.config['URL']['kodi_url']
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        headers = {'Connection': 'close'}
        res = requests.post(kodi_url, data={'number': number}, headers=headers)
        if 'Ошибка: Номер не найден' in res.text:
            resp['res'] = 'ERROR'
            resp['descr'] = 'Number not found/Номер не найден'
            return resp
        soup = BeautifulSoup(res.text, 'lxml')
        div_raw = soup.find('div', class_='content__in')
        table = div_raw.find('table', class_='teltr tel-mobile')
        tr_raw = table.find_all('tr', class_='')
        td_raw = tr_raw[-1].find_all('td')
        resp['Страна'] = td_raw[0].find('strong').text
        operator_info = td_raw[1].find('strong').text
        resp['Регион'] = operator_info.split('[')[1].replace(']', '').replace(',', '')
        resp['Изначальный оператор'] = operator_info.split(' ')[0]
        p_raw = div_raw.find('p', style='')
        span_raw = p_raw.find_all('span')
        resp['Текущий оператор'] = span_raw[-1].text
        resp['res'] = 'OK'
        return resp

    def get_random_movie(self, text: str) -> dict:
        """
        Get random movie from internet
        :param:
        :return: random movie string
        """
        logger.info('get_random_movie')
        resp = {}
        year = datetime.datetime.now().year
        command = text.split(' ')
        if len(command) > 1:
            try:
                year = int(command[1])
            except ValueError as e:
                resp['res'] = 'ERROR'
                resp['descr'] = 'Format of data is not valid'
                return resp
            else:
                if year < 1890 or year > 2022:
                    resp['res'] = 'ERROR'
                    resp['descr'] = f'Year may be from 1890 to {datetime.datetime.now().year}'
                    return resp
        if self.config.has_option('URL', 'random_movie_url'):
            random_movie_url = self.config['URL']['random_movie_url'].format(year, year)
        else:
            resp['res'] = 'ERROR'
            resp['descr'] = "I can't do this yet😔"
            return resp
        soup = InternetLoader._site_to_lxml(random_movie_url)
        result_top = soup.find('div', class_='search_results_top')
        span_raw = result_top.find('span')
        is_result = int(span_raw.text.split(' ')[-1])
        if not is_result:
            resp['res'] = 'ERROR'
            resp['descr'] = f'Movies by {year} is not found'
            return resp
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        div_raw = soup.find('div', class_='search_results search_results_last')
        div_nav = div_raw.find('div', class_='navigator')
        from_to = div_nav.find('div', class_='pagesFromTo').text.split(' ')[0].split('—')
        per_page = int(from_to[1]) - int(from_to[0]) - 1
        page_count = int(div_nav.find('div', class_='pagesFromTo').text.split(' ')[-1]) // per_page
        random_page_number = 1
        if page_count > 1:
            random_page_number = str(random.choice(range(1, page_count)))
        movie_soup = InternetLoader._site_to_lxml(random_movie_url + str(random_page_number))
        movie_div_raw = movie_soup.find('div', class_='search_results search_results_last')
        div_elements = movie_div_raw.find_all('div', class_='element')
        random_movie_raw = random.choice(div_elements)
        p_raw = random_movie_raw.find('p', class_='name')
        movie_id = p_raw.find('a').get('href')
        movie_url = '/'.join(random_movie_url.split('/')[:3])
        resp['res'] = 'OK'
        resp[0] = f'Случайный фильм {year} года'
        resp[1] = movie_url+movie_id
        return resp
