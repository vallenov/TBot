import datetime
import random
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import json

import config

from loaders.loader import Loader, check_permission
from markup import custom_markup
from helpers import dict_to_str, is_phone_number, exception_catch
from loggers import get_logger
from helpers import check_config_attribute
from exceptions import (
    ConfigAttributeNotFoundError,
    EmptySoupDataError,
    BadResponseStatusError,
    WrongParameterTypeError,
    WrongParameterCountError,
    WrongParameterValueError,
)

logger = get_logger(__name__)


class InternetLoader(Loader):
    """
    Work with internet
    """

    def __init__(self, name):
        super().__init__(name)
        self.book_genres = {}

    @staticmethod
    def site_to_lxml(url: str) -> BeautifulSoup or None:
        """
        Get site and convert it to the lxml
        :param url: https://site.com/
        :return: BeautifulSoup object
        """
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Connection': 'close'
        }
        try:
            logger.info(f'Try to get info from {url}')
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'lxml')
                if soup is None:
                    raise EmptySoupDataError(url)
            else:
                logger.error(f'Status of response: {resp.status_code}')
                raise BadResponseStatusError(resp.status_code)
        except EmptySoupDataError:
            raise
        except BadResponseStatusError:
            raise
        except Exception as _ex:
            logger.exception(f'Exception in {__name__}:\n{_ex}')
            raise
        else:
            logger.info(f'Get successful')
        return soup

    @check_permission()
    def get_exchange(self, **kwargs) -> dict:
        """
        Get exchange from internet
        :param:
        :return: string like {'USD': '73,6059', 'EUR':'83,1158'}
        """
        resp = {}
        try:
            url = check_config_attribute('exchange_url')
            ex = ['USD', 'EUR']
            soup = InternetLoader.site_to_lxml(url)
            parse = soup.find_all('tr')
            exchange = {}
            for item in parse[1:]:
                inf = item.find_all('td')
                if inf[1].text not in ex:
                    continue
                exchange[inf[1].text] = inf[4].text
            resp['text'] = dict_to_str(exchange, ' = ')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp("Empty soup data")
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_weather(self, **kwargs) -> dict:
        """
        Get weather from internet
        :param:
        :return: dict like {'Сегодня': '10°/15°', 'ср 12': '11°/18°'}
        """
        resp = {}
        try:
            url = check_config_attribute('weather_url')
            soup = InternetLoader.site_to_lxml(url)
            parse = soup.find_all('div',
                                  class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
            weather = {}
            for i in parse:
                h2 = i.find('h2')
                div = i.find('div')
                span = div.find_all('span')
                span = list(map(lambda x: x.text, span))
                weather[h2.text] = ''.join(span[:-1])
            resp['text'] = dict_to_str(weather, ' = ')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_quote(self, **kwargs) -> dict:
        """
        Get quote from internet
        :param:
        :return: dict like {'quote1': 'author1', 'quote2: 'author2'}
        """
        resp = {}
        try:
            url = check_config_attribute('quote_url')
            soup = InternetLoader.site_to_lxml(url)
            quotes = soup.find_all('div', class_='quote')
            random_quote = random.choice(quotes)
            author = random_quote.find('a')
            text = random_quote.find('div', class_='quote_name')
            quote = dict()
            quote[text.text] = author.text
            resp['text'] = dict_to_str(quote, '\n')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_wish(self, **kwargs) -> dict:
        """
        Get wish from internet
        :param:
        :return: wish string
        """
        resp = {}
        try:
            url = check_config_attribute('wish_url')
            soup = InternetLoader.site_to_lxml(url)
            wishes = soup.find_all('ol')
            wish_list = wishes[0].find_all('li')
            resp['text'] = random.choice(wish_list).text
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_news(self, text: str, **kwargs) -> dict:
        """
        Get news from internet
        :param:
        :return: wish string
        """
        resp = {}
        count = 5
        lst = text.split(' ')
        try:
            if len(lst) > 1:
                try:
                    count = int(lst[1])
                except ValueError:
                    raise WrongParameterTypeError(lst[1])
            url = check_config_attribute('news_url')
            soup = InternetLoader.site_to_lxml(url)
            div_raw = soup.find_all('div', class_='cell-list__item-info')
            news = {}
            for n in div_raw:
                news_time = n.find('span', class_='elem-info__date')
                text = n.find('span', class_='share')
                if news_time and text:
                    news[news_time.text] = text.get('data-title')
                if len(news) == count:
                    break
            resp['text'] = dict_to_str(news, '\n')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        except WrongParameterTypeError:
            logger.exception('Count of news is not number')
            return Loader.error_resp('Count of news is not number')
        else:
            return resp

    @check_permission()
    def get_affirmation(self, **kwargs) -> dict:
        """
        Get affirmation from internet
        :param:
        :return: affirmation string
        """
        resp = {}
        try:
            url = check_config_attribute('affirmation_url')
            soup = InternetLoader.site_to_lxml(url)
            aff_list = []
            ul = soup.find_all('ul')
            for u in ul:
                li = u.find_all('em')
                for em in li:
                    if em.text[0].isupper():
                        aff_list.append(em.text)
            resp['text'] = random.choice(aff_list)
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        except WrongParameterTypeError:
            logger.exception('Count of news is not number')
            return Loader.error_resp('Count of news is not number')
        else:
            return resp

    async def _get_url(self, session, url) -> None:
        """
        Get async url data
        """
        async with session.get(url) as res:
            data = await res.text()
            if res.status == 200:
                logger.info(f'Get successful ({url})')
            else:
                logger.error(f'Get unsuccessful ({url})')
                raise BadResponseStatusError(url)
            self.async_url_data.append(data)

    @check_permission()
    async def async_events(self, **kwargs) -> dict:
        """
        Get events from internet (async)
        :param:
        :return: events digest
        """
        self.async_url_data = []
        tasks = []
        resp = {}
        try:
            url = check_config_attribute('events_url')
            async with aiohttp.ClientSession() as session:
                tasks.append(asyncio.create_task(self._get_url(session, url)))
                await asyncio.gather(*tasks)
                tasks = []
                soup = BeautifulSoup(self.async_url_data.pop(), 'lxml')
                if not soup:
                    raise EmptySoupDataError(url)
                links = {}
                div = soup.find_all('div', class_='site-nav-events')
                raw_a = div[0].find_all('a')
                for a in raw_a:
                    links[a.text] = a.get('href')
                for _, link in links.items():
                    tasks.append(asyncio.create_task(self._get_url(session, link)))
                await asyncio.gather(*tasks)
                events = {}
                for raw in self.async_url_data:
                    events_links = []
                    soup_curr = BeautifulSoup(raw, 'lxml')
                    if not soup_curr:
                        raise EmptySoupDataError
                    name = soup_curr.find('title').text.split('.')[0]
                    raw_div = soup_curr.find('div', class_='feed-container')
                    article = raw_div.find_all('article', class_='post post-rect')
                    for art in article:
                        h2s = art.find_all('h2', class_='post-title')
                        for raw_h2 in h2s:
                            a = raw_h2.find('a')
                            descr = a.text.replace('\n', '')
                            events_links.append(f"{descr}\n{a.get('href')}\n")
                    events[name] = random.choice(events_links)
                resp['text'] = dict_to_str(events, '\n')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_restaurant(self, **kwargs) -> dict:
        """
        Get restaurant from internet
        :param:
        :return: restaurant string
        """
        resp = {}
        try:
            url = check_config_attribute('restaurant_url')
            soup = InternetLoader.site_to_lxml(url + '/msk/catalog/restaurants/all/')
            div_nav_raw = soup.find('div', class_='pagination-wrapper')
            a_raw = div_nav_raw.find('a')
            page_count = int(a_raw.get('data-nav-page-count'))
            rand_page = random.choice(range(1, page_count + 1))
            if rand_page > 1:
                soup = InternetLoader.site_to_lxml(config.LINKS['restaurant_url']
                                                   + '/msk/catalog/restaurants/all/'
                                                   + f'?page={rand_page}')
            names = soup.find_all('a', class_='name')
            restaurant = random.choice(names)
            soup = InternetLoader.site_to_lxml(config.LINKS['restaurant_url'] + restaurant.get('href'))
            div_raw = soup.find('div', class_='props one-line-props')
            final_restaurant = dict()
            final_restaurant[0] = restaurant.text
            for d in div_raw:
                name = d.find('div', class_='name')
                if name:
                    name = name.text
                value = d.find('a')
                if value:
                    value = value.text.strip().replace('\n', '')
                if name is not None and value is not None:
                    final_restaurant[name] = value
            final_restaurant[1] = config.LINKS['restaurant_url'] + restaurant.get('href')
            resp['text'] = dict_to_str(final_restaurant, ' ')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_poem(self, **kwargs) -> dict:
        """
        Get poem from internet
        :param:
        :return: poesy string
        """
        resp = {}
        try:
            url = check_config_attribute('poesy_url')
            soup = InternetLoader.site_to_lxml(url)
            div_raw = soup.find('div', class_='_2uPBE')
            a_raw = div_raw.find_all('a', class_='GmJ5E')
            count = int(a_raw[-1].text)
            rand = random.randint(1, count)
            if rand > 1:
                soup = InternetLoader.site_to_lxml(config.LINKS['poesy_url'] + f'?page={rand}')
            poems_raw = soup.find('div', class_='_2VELq')
            poems_raw = poems_raw.find_all('div', class_='_1jGw_')
            rand_poem_raw = random.choice(poems_raw)
            href = rand_poem_raw.find('a', class_='_2A3Np').get('href')
            link = '/'.join(config.LINKS['poesy_url'].split('/')[:-3]) + href

            soup = InternetLoader.site_to_lxml(link)

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
            resp['text'] = f'{author}\n\n{name}\n\n{poem}{year}'
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_phone_number_info(self, text: str, **kwargs) -> dict:
        """
        Get phone number info from internet
        :param:
        :return: poesy string
        """
        resp = {}
        try:
            url = check_config_attribute('kodi_url')
            lst = text.split()
            number = is_phone_number(lst[1])
            res = requests.post(url, data={'number': number})
            if 'Ошибка: Номер не найден' in res.text:
                return Loader.error_resp('Number not found/Номер не найден')
            soup = BeautifulSoup(res.text, 'lxml')
            div_raw = soup.find('div', class_='content__in')
            table = div_raw.find('table', class_='teltr tel-mobile')
            tr_raw = table.find_all('tr', class_='')
            td_raw = tr_raw[-1].find_all('td')
            phone_info = dict()
            phone_info['Страна'] = td_raw[0].find('strong').text
            operator_info = td_raw[1].find('strong').text
            phone_info['Регион'] = operator_info.split('[')[1].replace(']', '').replace(',', '')
            phone_info['Изначальный оператор'] = operator_info.split(' ')[0]
            p_raw = div_raw.find('p', style='')
            span_raw = p_raw.find_all('span')
            phone_info['Текущий оператор'] = span_raw[-1].text
            resp['text'] = dict_to_str(phone_info, ': ')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_random_movie(self, text: str, **kwargs) -> dict:
        """
        Get random movie from internet
        :param:
        :return: random movie string
        """
        resp = {}
        command = text.split(' ')
        year_from = 0
        year_to = 0
        try:
            if len(command) > 2:
                raise WrongParameterCountError(len(command))
            if len(command) == 1:
                resp['text'] = 'Выберите промежуток'
                resp['markup'] = custom_markup('movie',
                                               ['1950-1960', '1960-1970', '1970-1980',
                                                '1980-1990', '1990-2000', '2000-2010', '2010-2020'],
                                               '🎞')
                return resp
            elif len(command) == 2:
                if '-' not in command[1]:
                    try:
                        act_year_from = int(command[1])
                        act_year_to = act_year_from
                        year_from = act_year_from
                        year_to = act_year_to
                    except ValueError as e:
                        return Loader.error_resp('Format of data is not valid')
                    else:
                        if act_year_from < 1890 or act_year_to > 2022:
                            return Loader.error_resp(f'Year may be from 1890 to {datetime.datetime.now().year}')
                else:
                    try:
                        split_years = command[1].split('-')
                        act_year_from = int(split_years[0])
                        act_year_to = int(split_years[1])
                        if act_year_from < 1890 or act_year_to > 2022:
                            return Loader.error_resp(f'Year may be from 1890 to {datetime.datetime.now().year}')
                        elif act_year_from > act_year_to:
                            return Loader.error_resp(f'Start year may be greater then finish year')
                        year_from = random.choice(range(int(split_years[0]), int(split_years[1]) + 1))
                        year_to = year_from
                    except ValueError as e:
                        return Loader.error_resp('Format of data is not valid')
            url = check_config_attribute('random_movie_url')
            soup = InternetLoader.site_to_lxml(url)
            result_top = soup.find('div', class_='search_results_top')
            span_raw = result_top.find('span')
            is_result = int(span_raw.text.split(' ')[-1])
            if not is_result:
                return Loader.error_resp(f'Movies by {year_from}-{year_to} is not found')
            div_raw = soup.find('div', class_='search_results search_results_last')
            div_nav = div_raw.find('div', class_='navigator')
            from_to = div_nav.find('div', class_='pagesFromTo').text.split(' ')[0].split('—')
            per_page = int(from_to[1]) - int(from_to[0]) - 1
            page_count = int(div_nav.find('div', class_='pagesFromTo').text.split(' ')[-1]) // per_page
            current_try = 0
            max_try = 5
            while current_try < max_try:
                current_try += 1
                random_page_number = str(random.choice(range(1, page_count)))
                movie_soup = InternetLoader.site_to_lxml(url + str(random_page_number))
                movie_div_raw = movie_soup.find('div', class_='search_results search_results_last')
                div_elements = movie_div_raw.find_all('div', class_='element')
                div_elements = list(filter(lambda x: 'no-poster' not in x.find('img').get('title'), div_elements))
                if not div_elements:
                    logger.warning(f'No elements with poster')
                    continue
                try_count = 0
                symbols = 'аоуыэяеёюибвгдйжзклмнпрстфхцчшщьъАОУЫЭЯЕЁЮИБВГДЙЖЗКЛМНПРСТФХЦЧШЩЬЪ'
                while True:
                    random_movie_raw = random.choice(div_elements)
                    p_raw = random_movie_raw.find('p', class_='name')
                    name = p_raw.text
                    name = name.replace('видео', '')
                    name = name.replace('ТВ', '')
                    for simb in name:
                        if simb in symbols:
                            movie_id = p_raw.find('a').get('href')
                            movie_url = '/'.join(url.split('/')[:3])
                            text = f'Случайный фильм {act_year_from}-{act_year_to} годов'
                            link = movie_url + movie_id
                            resp['text'] = f'{text}\n{link}'
                            return resp
                    try_count += 1
                    if try_count > per_page:
                        logger.warning(f'No elements with cyrillic symbols')
                        break
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        except WrongParameterCountError:
            logger.exception('Wrong parameter count')
            return Loader.error_resp('Wrong parameter count')
        else:
            return Loader.error_resp(f'Movie {year_from}-{year_to} years not found')

    def get_book_genres(self):
        """
        Get list of book's genres
        :param:
        :return: book genres
        """
        if self.book_genres:
            return
        try:
            url = check_config_attribute('book_url')
            soup = InternetLoader.site_to_lxml(url)
            genre_raw = soup.find_all('div', class_='card-white genre-block')
            for genre in genre_raw:
                title_raw = genre.find('a', class_='main-genre-title')
                if title_raw.text:
                    self.book_genres[title_raw.text] = title_raw.get('href')
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()

    @check_permission()
    def get_book(self, text, **kwargs):
        """
        Get random book from internet
        :param:
        :return: book
        """
        resp = {}
        try:
            err = self.get_book_genres()
            if err:
                return err
            lst = text.split()
            if len(lst) == 1:
                resp['text'] = 'Выберите жанр'
                resp['markup'] = custom_markup('book', self.book_genres, '📖')
                return resp
            category = ''
            for genre in self.book_genres.keys():
                if genre.lower().startswith(lst[1]):
                    category = self.book_genres[genre]
            if not category:
                return Loader.error_resp('Genre is not valid')
            site = '/'.join(config.LINKS['book_url'].split('/')[:3])
            soup = InternetLoader.site_to_lxml(f'{site}{category}/listview/biglist/~6')
            if soup is None:
                logger.error(f'Empty soup data')
                return Loader.error_resp()
            a_raw = soup.find_all('a', class_='pagination-page pagination-wide')
            last_page_raw = a_raw[-1].get('href')
            last_page = last_page_raw.split('~')[-1]
            random_page = random.choice(range(1, int(last_page) + 1))
            soup = InternetLoader.site_to_lxml(f'{site}{category}/listview/biglist/~{random_page}')
            div_raw = soup.find('div', class_='blist-biglist')
            book_list = div_raw.find_all('div', class_='book-item-manage')
            random_book_raw = random.choice(book_list)
            random_book = random_book_raw.find('a', class_='brow-book-name with-cycle')
            resp['text'] = f"{random_book.get('title')}\n"
            resp['text'] += f"{site}{random_book.get('href')}"
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission()
    def get_russian_painting(self, **kwargs) -> dict:
        """
        Get russian painting from internet
        :param:
        :return: dict
        """
        resp = {}
        try:
            url = check_config_attribute('russian_painting_url')
            soup = InternetLoader.site_to_lxml(url)
            div_raw = soup.find_all('div', class_='pic')
            random_painting = random.choice(div_raw)
            a_raw = random_painting.find('a')
            href = a_raw.get('href')
            site = '/'.join(config.LINKS['russian_painting_url'].split('/')[:3])
            link = site + href
            soup = InternetLoader.site_to_lxml(link)
            p_raw = soup.find('p', class_='xpic')
            img_raw = p_raw.find('img')
            picture = img_raw.get('src')
            if picture:
                resp['photo'] = picture
            else:
                logger.info('Picture not found')
                Loader.error_resp()
            text = img_raw.get('title')
            if text:
                text = text.split('900')[0]
            else:
                text = 'Picture'
            resp['text'] = text
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        else:
            return resp

    @check_permission(needed_level='root')
    def get_server_ip(self, **kwargs) -> dict:
        """
        Get server ip
        :param:
        :return: dict with ip
        """
        resp = {}
        data = requests.get(config.LINKS['system-monitor'] + 'ip')
        data_dict = json.loads(data.text)
        resp['text'] = data_dict.get('ip', 'Something wrong')
        return resp

    @check_permission(needed_level='root')
    def ngrok(self, text: str, **kwargs) -> dict:
        """
        Actions with ngrok
        :param:
        :return: operation status or tunnel's info
        """
        resp = {}
        try:
            url = check_config_attribute('system-monitor')
            command = text.split(' ')
            valid_actions = ['start', 'stop', 'restart', 'tunnels']
            if len(command) > 2:
                raise WrongParameterCountError(len(command))
            if len(command) == 1:
                resp['text'] = 'Выберите действие'
                resp['markup'] = custom_markup('ngrok',
                                               valid_actions,
                                               '🖥')
                return resp
            if command[1] not in valid_actions:
                raise WrongParameterValueError(command[1])
            data = requests.get(url + f'ngrok_{command[1]}')
            if data.status_code != 200:
                raise BadResponseStatusError(data.status_code)
            else:
                sys_mon_res = json.loads(data.text)
                if isinstance(sys_mon_res['msg'], str):
                    resp['text'] = sys_mon_res['msg']
                elif isinstance(sys_mon_res['msg'], list):
                    if len(sys_mon_res['msg']) == 0:
                        resp['text'] = 'Отсутствуют открытые туннели'
                        return resp
                    resp['text'] = '\n\n'.join(
                        ['\n'.join([f"url: {i['url']}",
                                    f"port: {i['port']}",
                                    f"protocol: {i['protocol']}",
                                    f"forwards_to: {i['forwards_to']}"]) for i in sys_mon_res['msg']
                         ]
                    )
        except ConfigAttributeNotFoundError:
            logger.exception('Config attribute not found')
            return Loader.error_resp("I can't do this yet😔")
        except EmptySoupDataError:
            logger.exception('Empty soup data')
            return Loader.error_resp()
        except BadResponseStatusError:
            logger.exception('Bad response status')
            return Loader.error_resp()
        except WrongParameterCountError:
            logger.exception('Wrong parameter count')
            return Loader.error_resp('Wrong parameter count')
        except WrongParameterValueError as e:
            logger.exception('Wrong parameter value')
            return Loader.error_resp(f'Wrong parameter value: {e.val}')
        else:
            return resp

    @check_permission(needed_level='root')
    def ngrok_db(self, text: str, **kwargs) -> dict:
        """
        Actions with ngrok_db
        :param:
        :return: operation status
        """
        resp = {}
        if config.LINKS.get('system-monitor', None):
            system_monitor = config.LINKS['system-monitor']
        else:
            return Loader.error_resp("I can't do this yet😔")
        command = text.split(' ')
        valid_actions = ['start', 'stop', 'restart']
        if len(command) > 2:
            return Loader.error_resp('Format of data is not valid')
        if len(command) == 1:
            resp['text'] = 'Выберите действие'
            resp['markup'] = custom_markup('ngrok_db',
                                           valid_actions,
                                           '📦')
            return resp
        if command[1] not in valid_actions:
            return Loader.error_resp('Command is not valid')
        try:
            data = requests.get(system_monitor + f'ngrok_db_{command[1]}')
            if data.status_code != 200:
                logger.error(f'requests status is not valid: {data.status_code}')
                return Loader.error_resp('Something wrong')
            else:
                sys_mon_res = json.loads(data.text)
                resp['text'] = sys_mon_res['msg']
                return resp
        except Exception as ex:
            logger.exception(f'Exception: {ex}')
