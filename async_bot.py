import asyncio
import aiohttp
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup, Tag
from typing import Dict, Optional, Any
import http

load_dotenv()

RBK = os.getenv("RBK")
TOKEN = os.getenv("BOT_TOKEN")
RIA = os.getenv("RIA")
MUSIC_NEWS = os.getenv("MUSIC")
WEATHER_API = os.getenv("WEATHER_API")
STATE_WAITING_FOR_CITY = 'waiting_for_city'
OPENWEATHERSITE = os.getenv("OPENWEATHERSITE")

if not TOKEN:
    raise ValueError('ошибка в нахождении токена в файле .env')

URL = f"https://api.telegram.org/bot{TOKEN}"

user_states: Dict[int, str] = {}


async def send_message(session: aiohttp.ClientSession,
                       chat_id: int, text: str) -> Any:
    # session задан в main. это объект который управляет http соединениями
    """Асинхронная отправка сообщений """
    url = f"{URL}/sendMessage"
    loading = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    async with session.post(url, json=loading) as response:
        return await response.json()


async def get_updates(session: aiohttp.ClientSession,
                      offset: Optional[int] = None,
                      timeout: int = 30) -> Any:
    """Асинхронное получение обновлений"""
    url = f"{URL}/getUpdates"
    params = {'timeout': timeout}
    if offset:
        params['offset'] = offset
    async with session.get(url, params=params) as response:
        return await response.json()


def get_daily_quote() -> str:
    """Функция получения цитаты и автора с citaty.info.

    Returns:
        Цитата и автор или сообщение об ошибке.
    """
    try:
        url = "https://citaty.info/random"
        response = requests.get(url)
        response.raise_for_status()  # сразу проверяем на ошибки запроса

        soup = BeautifulSoup(response.text, 'html.parser')

        random_quote_div = soup.find('a', class_='citaty_info-quote alink')
        if not random_quote_div:
            return "не найден контейнер с цитатой"

        quote_p = random_quote_div.find('p')
        if isinstance(quote_p, Tag):
            quote_text = quote_p.get_text(strip=True)
        else:
            return "не найден тег <p> с цитатой"

        author_div = soup.find('div', class_="field-item even")
        if not author_div:
            return "не найден контейнер с автором"
        author_link = author_div.find('a')
        if isinstance(author_link, Tag):
            author = author_link.get_text(strip=True)
        else:
            return "не найдено"

        if author:
            return f"“{quote_text}” - {author}"
        else:
            return f"“{quote_text}”"

    except Exception as e:  # ошибки связанные с request
        return f"ошибка при запросе к сайту: {e}"


async def rbk(session: aiohttp.ClientSession) -> str:
    """Пять последних заголовков с РБК."""
    if RBK is None:
        return "URL для RBK не настроен в .env"
    url = RBK
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html_text = await response.text()  # читает тело http-ответа
            soup = BeautifulSoup(html_text, 'html.parser')
            divs = soup.find_all(
                'span', class_='g-inline-text-badges__text'
            )
            if not divs:
                return "ошибка не найден заголовок"
            all_news = ''
            for item in divs[:5]:
                item_block = item.get_text(separator=' ', strip=True)
                if item_block:
                    all_news += item_block + '\n'

            return f"{all_news}"

    except aiohttp.ClientError as e:  # ловим ошибки aiohttp
        return f"ошибка при запросе к сайту: {e}"
    except Exception as e:  # ловим другие ошибки (например парсинг)
        return f"неизвестная ошибка: {e}"


async def ria(session: aiohttp.ClientSession) -> str:
    """Главный заголовок с РИА Новости."""
    if RIA is None:
        return "URL для RIA не настроен в .env"
    url = RIA
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html_text = await response.text()
            soup = BeautifulSoup(html_text, 'html.parser')

            body_div = soup.find('div', class_='cell-main-photo__title')
            if not body_div:
                return "ошибка не найден заголовок"

            header_text = body_div.get_text(separator=' ', strip=True)

            return f"{header_text}"
    except aiohttp.ClientError as e:  # ловим ошибки aiohttp
        return f"ошибка при запросе к сайту : {e}"
    except Exception as e:  # ловим другие ошибки (например парсинг)
        return f"неизвестная ошибка: {e}"


async def music(session: aiohttp.ClientSession) -> str:
    """Последняя музыкальная новость."""
    if MUSIC_NEWS is None:
        return "URL для MUSIC_NEWS не настроен в .env"
    url = MUSIC_NEWS
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html_text = await response.text()
            soup = BeautifulSoup(html_text, 'html.parser')

            article = soup.find('div', class_='n_d_bl')
            if not article:
                return "ошибка"
            if isinstance(article, Tag):
                body_div = article.find('a', class_='title')
            else:
                return "ошибка: article не является HTML-элементом"
            if isinstance(body_div, Tag):
                text_of_new = body_div.get_text(separator=' ', strip=True)
            else:
                return "ошибка: не найдено"

            return f"“{text_of_new}”"
    except aiohttp.ClientError as e:  # ловим ошибки aiohttp
        return f"ошибка при запросе к сайту (aiohttp): {e}"
    except Exception as e:  # ловим другие ошибки (например парсинг)
        return f"неизвестная ошибка: {e}"


async def get_weather_async(session: aiohttp.ClientSession,
                            city_name: str) -> str:
    """Текущая погода в городе через OpenWeatherMap API."""
    if not WEATHER_API:
        return "API ключ для погоды не настроен"
    if OPENWEATHERSITE is None:
        return "URL для OPENWEATHERSITE не настроен в .env"
    url = OPENWEATHERSITE
    params = {
        'q': city_name,
        'appid': WEATHER_API,
        'units': 'metric',  # для получения температуры в цельсиях
        'lang': 'ru'  # для получения описания погоды на русском языке
    }
    try:
        async with session.get(url, params=params) as response:
            if response.status == http.HTTPStatus.OK:  # 200
                data = await response.json()
                # извлечение данных
                city = data['name']
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']

                weather_info = (
                    f"Погода в {city}:\n"
                    f"Температура: {temp} C "
                    f"(ощущается как {feels_like} C)\n"
                    f"Описание: {description}\n"
                    f"Влажность: {humidity}%\n"
                    f"Скорость ветра: {wind_speed} м/с"
                )
                return weather_info
            elif response.status == http.HTTPStatus.NOT_FOUND:  # 404
                return "Город не найден."
            else:
                return f"Ошибка API погоды: {response.status}"
    except aiohttp.ClientResponseError as e:  # пример BadRequest Unauthorized
        return f"Ошибка HTTP при запросе к API: {e.status} - {e.message}"
    except aiohttp.ClientError as e:
        return f"Ошибка при запросе к API погоды: {e}"
    except Exception as e:
        return f"Неизвестная ошибка при получении погоды: {e}"


async def main() -> None:
    print("Асинхронный бот запускается")
    async with aiohttp.ClientSession() as session:
        offset = None
        while True:
            updates = await get_updates(session, offset=offset, timeout=30)
            if updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    message = update.get('message')
                    if message:
                        chat_id = message['chat']['id']
                        user_id = message['from']['id']
                        text = message.get('text', '')

                        # Проверка состояния
                        if user_id in user_states:
                            if user_states[user_id] == STATE_WAITING_FOR_CITY:
                                if text.strip():
                                    await send_message(
                                        session, chat_id,
                                        f"Получаю погоду для "
                                        f"'{text.strip()}'"
                                    )
                                    weather_result = await get_weather_async(
                                        session, text.strip()
                                    )
                                    await send_message(session, chat_id,
                                                       weather_result)
                                else:
                                    await send_message(session, chat_id,
                                                       "Город не указан.")
                                del user_states[user_id]
                                continue

                        # Обработка команд
                        if text in ('/start', '/help'):
                            await send_message(
                                session, chat_id,
                                "Привет! Команды:\n"
                                "/headlines — свежие заголовки новостей\n"
                                "/weather — погода в городе\n"
                                "/quote — случайная цитата"
                            )
                        elif text == '/quote':
                            quote = await asyncio.to_thread(get_daily_quote)
                            await send_message(session, chat_id, quote)
                        elif text == '/weather':
                            user_states[user_id] = STATE_WAITING_FOR_CITY
                            await send_message(session, chat_id,
                                               "Введите город.")
                        elif text == '/headlines':
                            # Пример конкурентного выполнения
                            ria_task = ria(session)
                            music_task = music(session)
                            rbk_task = rbk(session)
                            results = await asyncio.gather(
                                ria_task,
                                music_task,
                                rbk_task,
                                return_exceptions=True
                            )
                            message_text = (
                                f"Заголовки:\n{results[0]}\n"
                                f"{results[1]}\n{results[2]}"
                            )
                            await send_message(session, chat_id, message_text)
                        else:
                            await send_message(session, chat_id,
                                               f"Вы сказали: {text}")

if __name__ == '__main__':
    asyncio.run(main())