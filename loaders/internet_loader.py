import datetime
import random
import logging
import string
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp

from loaders.loader import Loader, check_permission
#from loaders.loader import

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class InternetLoader(Loader):
    """
    Work with internet
    """

    def __init__(self, name):
        super().__init__(name)
        self.book_genres = {}

    @staticmethod
    def _site_to_lxml(url: str, headers: dict = None) -> BeautifulSoup or None:
        """
        Get site and convert it to the lxml
        :param url: https://site.com/
        :return: BeautifulSoup object
        """
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'lxml')
            else:
                logger.error(f'Status of response: {resp.status_code}')
                return None
        except Exception as _ex:
            logger.exception(f'Exception in {__name__}:\n{_ex}')
            return None
        else:
            logger.info(f'Get successful ({url})')
        return soup

    @check_permission()
    def get_exchange(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        ex = ['USD', 'EUR']
        soup = InternetLoader._site_to_lxml(exchange_url)
        if soup is None:
            logger.error('Empty soup data')
            return Loader.error_resp("Empty soup data")
        parse = soup.find_all('tr')
        exchange = {}
        for item in parse[1:]:
            inf = item.find_all('td')
            if inf[1].text not in ex:
                continue
            exchange[inf[1].text] = inf[4].text
        resp['text'] = Loader.dict_to_str(exchange, ' = ')
        return resp

    @check_permission()
    def get_weather(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(weather_url)
        if soup is None:
            logger.error('Empty soup data')
            return Loader.error_resp("Empty soup data")
        parse = soup.find_all('div', class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
        weather = {}
        for i in parse:
            h2 = i.find('h2')
            div = i.find('div')
            span = div.find_all('span')
            span = list(map(lambda x: x.text, span))
            weather[h2.text] = ''.join(span[:-1])
        resp['text'] = Loader.dict_to_str(weather, ' = ')
        return resp

    @check_permission()
    def get_quote(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(quote_url)
        if soup is None:
            logger.error('Empty soup data')
            return Loader.error_resp("Empty soup data")
        quotes = soup.find_all('div', class_='quote')
        random_quote = random.choice(quotes)
        author = random_quote.find('a')
        text = random_quote.find('div', class_='quote_name')
        quote = dict()
        quote[text.text] = author.text
        resp['text'] = Loader.dict_to_str(quote, '\n')
        return resp

    @check_permission()
    def get_wish(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(wish_url)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
        wishes = soup.find_all('ol')
        wish_list = wishes[0].find_all('li')
        resp['text'] = random.choice(wish_list).text
        return resp

    @check_permission()
    def get_news(self, text: str, **kwargs) -> dict:
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
                return Loader.error_resp('Count of news is not number')
        if self.config.has_option('URL', 'news_url'):
            news_url = self.config['URL']['news_url']
        else:
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(news_url)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
        div_raw = soup.find_all('div', class_='cell-list__item-info')
        news = {}
        for n in div_raw:
            news_time = n.find('span', class_='elem-info__date')
            text = n.find('span', class_='share')
            if news_time and text:
                news[news_time.text] = text.get('data-title')
            if len(news) == count:
                break
        resp['text'] = Loader.dict_to_str(news, '\n')
        return resp

    @check_permission()
    def get_affirmation(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(affirmation_url)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
        aff_list = []
        ul = soup.find_all('ul')
        for u in ul:
            li = u.find_all('em')
            for em in li:
                if em.text[0].isupper():
                    aff_list.append(em.text)
        resp['text'] = random.choice(aff_list)
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
            self.async_url_data.append(data)

    @check_permission()
    async def async_events(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
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
            events = {}
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
                events[name] = random.choice(events_links)
            resp['text'] = Loader.dict_to_str(events, '\n')
            return resp

    @check_permission()
    def get_events(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(events_url)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
        links = {}
        div = soup.find_all('div', class_='site-nav-events')
        raw_a = div[0].find_all('a')
        for a in raw_a:
            links[a.text] = a.get('href')
        events = {}
        for name, link in links.items():
            events_links = []
            name = name.replace('\n', '')
            raw_data = InternetLoader._site_to_lxml(link)
            h2s = raw_data.find_all('h2', class_='post-title')
            for raw_h2 in h2s:
                a = raw_h2.find('a')
                descr = a.text.replace('\n', '')
                events_links.append(f"{descr}\n{a.get('href')}\n")
            events[name] = random.choice(events_links)
        resp['text'] = Loader.dict_to_str(events, ' ')
        return resp

    @check_permission()
    def get_restaurant(self, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(restaurant_url + '/msk/catalog/restaurants/all/')
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
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
        final_restaurant[1] = self.config['URL']['restaurant_url'] + restaurant.get('href')
        resp['text'] = Loader.dict_to_str(final_restaurant, ' ')
        return resp

    @check_permission()
    def get_poem(self, **kwargs) -> dict:
        """
        Get poem from internet
        :param:
        :return: poesy string
        """
        logger.info('get_poem')
        resp = {}
        if self.config.has_option('URL', 'poesy_url'):
            poesy_url = self.config['URL']['poesy_url']
        else:
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(poesy_url)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
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
        resp['text'] = f'{author}\n\n{name}\n\n{poem}{year}'
        return resp

    @check_permission()
    def get_phone_number_info(self, number, **kwargs) -> dict:
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
            return Loader.error_resp("I can't do this yet😔")
        headers = {'Connection': 'close'}
        res = requests.post(kodi_url, data={'number': number}, headers=headers)
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
        resp['text'] = Loader.dict_to_str(phone_info, ': ')
        return resp

    @check_permission()
    def get_random_movie(self, text: str, **kwargs) -> dict:
        """
        Get random movie from internet
        :param:
        :return: random movie string
        """
        logger.info('get_random_movie')
        resp = {}
        command = text.split(' ')
        year_from = 0
        year_to = 0
        if len(command) == 1:
            resp['text'] = 'Выберите промежуток'
            return resp
        elif len(command) == 2:
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
        elif len(command) > 2:
            try:
                act_year_from = int(command[1])
                act_year_to = int(command[2])
                if act_year_from < 1890 or act_year_to > 2022:
                    return Loader.error_resp(f'Year may be from 1890 to {datetime.datetime.now().year}')
                elif act_year_from > act_year_to:
                    return Loader.error_resp(f'Start year may be greater then finish year')
                year_from = random.choice(range(int(command[1]), int(command[2]) + 1))
                year_to = year_from
            except ValueError as e:
                return Loader.error_resp('Format of data is not valid')
        if self.config.has_option('URL', 'random_movie_url'):
            random_movie_url = self.config['URL']['random_movie_url'].format(year_from, year_to)
        else:
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(random_movie_url)
        result_top = soup.find('div', class_='search_results_top')
        span_raw = result_top.find('span')
        is_result = int(span_raw.text.split(' ')[-1])
        if not is_result:
            return Loader.error_resp(f'Movies by {year_from}-{year_to} is not found')
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
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
            movie_soup = InternetLoader._site_to_lxml(random_movie_url + str(random_page_number))
            movie_div_raw = movie_soup.find('div', class_='search_results search_results_last')
            div_elements = movie_div_raw.find_all('div', class_='element')
            div_elements = list(filter(lambda x: 'no-poster' not in x.find('img').get('title'), div_elements))
            if not div_elements:
                logger.warning(f'No elements with poster')
                continue
            try_count = 0
            #simbols = string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation
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
                        movie_url = '/'.join(random_movie_url.split('/')[:3])
                        text = f'Случайный фильм {act_year_from}-{act_year_to} годов'
                        link = movie_url + movie_id
                        resp['text'] = f'{text}\n{link}'
                        return resp
                try_count += 1
                if try_count > per_page:
                    logger.warning(f'No elements with cyrillic symbols')
                    break
        return Loader.error_resp(f'Movie {year_from}-{year_to} years not found')

    def get_book_genres(self):
        """
        Get list of book's genres
        :param:
        :return: book genres
        """
        logger.info('get_genres')
        if self.config.has_option('URL', 'book_url'):
            book_url = self.config['URL']['book_url']
        else:
            return Loader.error_resp("I can't do this yet😔")
        soup = InternetLoader._site_to_lxml(book_url)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
        genre_raw = soup.find_all('div', class_='card-white genre-block')
        for genre in genre_raw:
            title_raw = genre.find('a', class_='main-genre-title')
            if title_raw.text:
                self.book_genres[title_raw.text] = title_raw.get('href')

    @check_permission()
    def get_book(self, text, **kwargs):
        """
        Get random book from internet
        :param:
        :return: book
        """
        logger.info('get_book')
        resp = {}
        err = self.get_book_genres()
        if err:
            return err
        lst = text.split()
        if len(lst) == 1:
            resp['text'] = 'Выберите жанр'
            return resp
        interval = {'today': 'where lr.date_ins between  current_date() and current_date() + interval 1 day ',
                    'week': 'where lr.date_ins between current_date() - interval 7 day and current_date() ',
                    'month': 'where lr.date_ins between current_date() - interval 30 day and current_date() ',
                    'all': ''}
        if lst[1] not in interval.keys():
            return Loader.error_resp('Interval is not valid')
        return resp

    @check_permission()
    def get_russian_painting(self, **kwargs) -> dict:
        """
        Get russian painting from internet
        :param:
        :return: dict
        """
        logger.info('get_russian_painting')
        resp = {}
        if self.config.has_option('URL', 'russian_painting_url'):
            russian_painting_url = self.config['URL']['russian_painting_url']
        else:
            return Loader.error_resp("I can't do this yet😔")
        headers = {
            'User-Agent': 'Mozilla/5.0'}
        soup = InternetLoader._site_to_lxml(russian_painting_url, headers)
        if soup is None:
            logger.error(f'Empty soup data')
            return Loader.error_resp()
        div_raw = soup.find_all('div', class_='pic')
        random_painting = random.choice(div_raw)
        a_raw = random_painting.find('a')
        href = a_raw.get('href')
        site = '/'.join(self.config['URL']['russian_painting_url'].split('/')[:3])
        link = site + href
        soup = InternetLoader._site_to_lxml(link, headers)
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
        return resp
