import datetime
import random
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import json
import traceback

import config

from loaders.loader import Loader, check_permission
from graph import Graph, BaseGraphInfo, BaseSubGraphInfo
from markup import custom_markup
from helpers import dict_to_str, is_phone_number, check_config_attribute
from loggers import get_logger
from exceptions import TBotException

logger = get_logger(__name__)


class InternetLoader(Loader):
    """
    Work with internet
    """

    def __init__(self):
        try:
            self.get_cities_coordinates()
            self.book_genres = {}
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())

    @staticmethod
    def regular_request(url: str, method: str = 'GET', data: dict = None) -> requests.models.Response:
        """
        Regular request to site
        """
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Connection': 'close'
        }
        try:
            logger.info(f'Try to get info from {url}')
            if method.upper() == 'GET':
                resp = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                resp = requests.post(url, headers=headers, data=data)
            else:
                raise TBotException(code=6, message=f'Method is not allowed: {method}')
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                logger.info(f'Get successful')
                return resp
            else:
                logger.error(f'Bad status of response: {resp.status_code}')
                raise TBotException(code=1, message=f'Bad response status: {resp.status_code}')
        except TBotException:
            raise
        except requests.exceptions.ConnectionError:
            raise TBotException(code=1,
                                message=f"Error connection to {check_config_attribute('system-monitor')}",
                                send=True)
        except Exception:
            raise TBotException(code=100, message=f'Exception in {__name__}', send=True)

    @staticmethod
    def site_to_lxml(url: str) -> BeautifulSoup or None:
        """
        Get site and convert it to the lxml
        :param url: https://site.com/
        :return: BeautifulSoup object
        """
        try:
            resp = InternetLoader.regular_request(url)
            soup = BeautifulSoup(resp.text, 'lxml')
            if soup is None:
                raise TBotException(code=1, message=f'Bad soup parsing {url}')
            return soup
        except TBotException as e:
            raise

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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    def get_cities_coordinates(self) -> None:
        """
        Get cities coordinates from internet to variable
        :param:
        :return:
        """
        url = check_config_attribute('city_coordinates_url')
        soup = InternetLoader.site_to_lxml(url)
        table_raw = soup.find('table', class_='tablesorter')
        tr_raw = table_raw.find_all('tr')
        self.city_coordinates = {}
        for tr in tr_raw[1:]:
            coords = tr.find_all('td')
            if len(coords) < 3:
                continue
            try:
                self.city_coordinates[coords[0].text] = (float(coords[1].text), float(coords[2].text))
            except ValueError:
                continue

    @check_permission()
    def get_weather(self, text: str, **kwargs) -> dict:
        """
        Get weather from internet
        :param:
        :return: picture with graph
        """
        resp = {}
        try:
            if not self.city_coordinates:
                raise TBotException(code=1,
                                    message=f"Coordinates is empty",
                                    send=True)
            cmd = text.split()
            if len(cmd) == 1:
                resp['text'] = 'Выберите город'
                resp['markup'] = custom_markup('weather',
                                               [city for city in self.city_coordinates.keys()
                                                if city in config.CITY_WEATHER],
                                               '⛅')
                return resp
            elif len(cmd) == 2:
                url = check_config_attribute('weather_url')
                needed_coordinates = self.city_coordinates.get(cmd[1])
                if not needed_coordinates:
                    raise TBotException(code=6,
                                        return_message=f'Я не умею определять погоду в городе: {cmd[1]}\n\n'
                                                       f'Список доступных городов: {", ".join(self.city_coordinates.keys())}')
                url += '?latitude={0}&longitude={1}'.format(*needed_coordinates)
                weather_params = ['temperature_2m', 'relativehumidity_2m', 'pressure_msl']
                url += f'&hourly={",".join(weather_params)}'
                url += '&start_date={0}&end_date={0}'.format(str(datetime.datetime.now())[:10])
                data = InternetLoader.regular_request(url)
                weather = json.loads(data.text)
                time = [time[11:] for time in weather['hourly']['time']]
                subplots = []
                for param in weather_params:
                    subplots.append(BaseSubGraphInfo('plot', 5, None, 'Date', param, time, weather['hourly'][param]))
                bgi = BaseGraphInfo('Weather', 'weather', subplots)
                resp['photo'] = Graph.get_base_graph(bgi)
                resp['text'] = f'Погода на сутки в городе {cmd[1]}'
                return resp
            else:
                raise TBotException(code=6, return_message=f'Wrong parameters count: {len(cmd)}')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def get_quote(self, **kwargs) -> dict:
        """
        Get quote from internet
        :param:
        :return: dict like {'text': 'quote_text\n author'}
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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def get_news(self, text: str, **kwargs) -> dict:
        """
        Get news from internet
        :param:
        :return: wish string
        """
        resp = {}
        count = 5
        lst = text.split()
        try:
            if len(lst) > 2:
                raise TBotException(code=6, return_message=f'Wrong parameters count: {len(lst)}')
            elif len(lst) == 2:
                try:
                    count = int(lst[1])
                except ValueError:
                    raise TBotException(code=6,
                                        return_message='Count of news is not number',
                                        message=f'{lst[1]} is not int')
            url = check_config_attribute('news_url')
            soup = InternetLoader.site_to_lxml(url)
            div_raw = soup.find_all('div', class_='cell-list__item-info')
            news = {}
            for n in div_raw:
                news_time = n.find('span', class_='elem-info__date')
                text = n.find('span', class_='share')
                if news_time and text:
                    special_symbols = r'-.'
                    form_text = text.get('data-title')
                    for symbol in special_symbols:
                        form_text = form_text.replace(symbol, fr'\{symbol}')
                    news[news_time.text] = f"[{form_text}]({text.get('data-url')})"
                if len(news) == count:
                    break
            resp['text'] = dict_to_str(news, ' ')
            resp['parse_mode'] = 'MarkdownV2'
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    async def _get_url(self, session, url) -> None:
        """
        Get async url data
        """
        async with session.get(url) as res:
            data = await res.text()
            if res.status >= 400:
                raise TBotException(code=1, message=f'URL: {url}. Bad response status: {res.status}')
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
                    raise TBotException(code=1, message=f'Bad soup parsing {url}')
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
                        raise TBotException(code=1, message=f'Bad soup parsing')
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
                return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
                raise TBotException(code=1, returt_message='Номер не найден')
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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
                raise TBotException(code=6,
                                    return_message=f'Wrong parameters count: {len(command)}',
                                    parameres_count=len(command))
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
                    except ValueError:
                        raise TBotException(code=6, return_message=f'Неправильный тип параметра: {command[1]}')
                    else:
                        if act_year_from < 1890 or act_year_to > 2022:
                            raise TBotException(code=6,
                                                return_message=f'Год должен быть между 1890 и '
                                                               f'{datetime.datetime.now().year}')
                else:
                    try:
                        split_years = command[1].split('-')
                        act_year_from = int(split_years[0])
                        act_year_to = int(split_years[1])
                        if act_year_from < 1890 or act_year_to > 2022:
                            raise TBotException(code=6,
                                                return_message=f'Год должен быть между 1890 и '
                                                               f'{datetime.datetime.now().year}')
                        elif act_year_from > act_year_to:
                            raise TBotException(code=6, return_message='Год начала должен быть меньше, '
                                                                       'чем год конца интервала')
                        year_from = random.choice(range(int(split_years[0]), int(split_years[1]) + 1))
                        year_to = year_from
                    except ValueError:
                        raise TBotException(code=6, return_message='Неправильный тип параметра')
            url = check_config_attribute('random_movie_url')
            soup = InternetLoader.site_to_lxml(url)
            result_top = soup.find('div', class_='search_results_top')
            span_raw = result_top.find('span')
            is_result = int(span_raw.text.split(' ')[-1])
            if not is_result:
                raise TBotException(code=1, return_message=f'Фильмы {year_from}-{year_to} не найдены')
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
            raise TBotException(code=1, return_message=f'Movie {year_from}-{year_to} years not found')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    def get_book_genres(self) -> None or dict:
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
                    self.book_genres[title_raw.text] = title_raw.get('href').replace('/genre/', '')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def get_book(self, text, **kwargs) -> dict:
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
                if genre.startswith(lst[1]):
                    category = self.book_genres[genre].lower()
            if not category:
                raise TBotException(code=2, return_message='Жанр не найден')
            site = '/'.join(config.LINKS['book_url'].split('/')[:3])
            soup = InternetLoader.site_to_lxml(f'{site}/genre/{category.capitalize()}/listview/biglist/~2')
            div_raw = soup.find_all('div', class_='pagination-right')
            a_raw = div_raw[0].find_all('a', class_='pagination-page pagination-wide')
            last_page_raw = a_raw[-1].get('href')
            last_page = last_page_raw.split('~')[-1]
            random_page = random.choice(range(1, int(last_page) + 1))
            soup = InternetLoader.site_to_lxml(f'{site}/genre/{category.capitalize()}/listview/biglist/~{random_page}')
            div_raw = soup.find('div', class_='blist-biglist')
            book_list = div_raw.find_all('div', class_='book-item-manage')
            random_book_raw = random.choice(book_list)
            random_book = random_book_raw.find('a', class_='brow-book-name with-cycle')
            resp['text'] = f"{random_book.get('title')}\n{site}{random_book.get('href')}"
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
                raise TBotException(code=1, message='Картина не найдена')
            text = img_raw.get('title')
            if text:
                text = text.split('900')[0]
            else:
                text = 'Picture'
            resp['text'] = text
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def get_server_ip(self, **kwargs) -> dict:
        """
        Get server ip
        :param:
        :return: dict with ip
        """
        resp = {}
        try:
            url = check_config_attribute('system-monitor')
            data = InternetLoader.regular_request(url + 'ip')
            data_dict = json.loads(data.text)
            resp['text'] = data_dict.get('ip')
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

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
            command = text.split()
            valid_actions = ['start', 'stop', 'restart', 'tunnels']
            if len(command) > 2:
                raise TBotException(code=6, return_message=f'Wrong parameters count: {len(command)}')
            if len(command) == 1:
                resp['text'] = 'Выберите действие'
                resp['markup'] = custom_markup('ngrok',
                                               valid_actions,
                                               '🖥')
                return resp
            action = command[1].lower()
            if action not in valid_actions:
                raise TBotException(code=6, return_message=f'Wrong parameter value: {action}')
            data = InternetLoader.regular_request(url + f'ngrok_{action}')
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
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def ngrok_db(self, text: str, **kwargs) -> dict:
        """
        Actions with ngrok_db
        :param:
        :return: operation status
        """
        resp = {}
        try:
            url = check_config_attribute('system-monitor')
            command = text.split(' ')
            valid_actions = ['start', 'stop', 'restart']
            if len(command) > 2:
                raise TBotException(code=6, return_message=f'Wrong parameters count: {len(command)}')
            if len(command) == 1:
                resp['text'] = 'Выберите действие'
                resp['markup'] = custom_markup('ngrok_db',
                                               valid_actions,
                                               '📦')
                return resp
            action = command[1].lower()
            if action not in valid_actions:
                raise TBotException(code=6, return_message=f'Wrong parameter value: {action}')
            data = InternetLoader.regular_request(url + f'ngrok_db_{action}')
            sys_mon_res = json.loads(data.text)
            resp['text'] = sys_mon_res['msg']
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def tbot_restart(self, **kwargs) -> dict:
        """
        Restart TBot
        :param:
        :return:
        """
        try:
            url = check_config_attribute('system-monitor')
            InternetLoader.regular_request(url + f'tbot_restart')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def system_restart(self, text: str, **kwargs) -> dict:
        """
        Restart system
        :param:
        :return:
        """
        resp = {}
        try:
            url = check_config_attribute('system-monitor')
            cmd = text.split()
            if len(cmd) == 1:
                resp['text'] = 'Подтвердите перезагрузку'
                resp['markup'] = custom_markup('restart_system', ['allow'], '✅')
                return resp
            elif len(cmd) == 2:
                if cmd[1].lower() == 'allow':
                    InternetLoader.regular_request(url + f'system_restart')
                else:
                    raise TBotException(code=6, return_message=f'Wrong parameter value: {cmd[1].lower()}')
            else:
                raise TBotException(code=6, return_message=f'Wrong parameters count: {len(cmd)}')
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def systemctl(self, text: str, **kwargs) -> dict:
        """
        Services control
        :param text: input command
        :return:
        """
        try:
            url = check_config_attribute('system-monitor')
            cmd = text.split()
            if len(cmd) != 3:
                raise TBotException(code=6, return_message=f'Wrong parameters count: {len(cmd)}')
            action = cmd[1].lower()
            service = cmd[2].lower()
            if action not in config.Systemctl.VALID_ACTIONS or service not in config.Systemctl.VALID_SERVICES:
                raise TBotException(code=6, return_message=f'Wrong parameter value: {f"{action} + {service}"}')
            data = InternetLoader.regular_request(url + f'systemctl?action={action}&service={service}')
            text = json.loads(data.text)
            resp = {
                'text': text.get('msg', 'Complete')
            }
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission(needed_level='root')
    def allow_connection(self, **kwargs) -> dict:
        """
        Allow ssh connection
        :return:
        """
        try:
            url = check_config_attribute('system-monitor')
            data = InternetLoader.regular_request(url + f'allow_connection')
            text = json.loads(data.text)
            resp = {
                'text': text.get('msg', 'Complete')
            }
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()
