import os
import requests
from typing import Any, Optional
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
if TOKEN is None:
    raise ValueError('ошибка в нахождении токена в файле .env')

# Убраны лишние пробелы
URL = f"https://api.telegram.org/bot{TOKEN}"


def get_me() -> None:
    """Автоматическая проверка токена.

    Вызывает метод getMe.
    """
    url = f"{URL}/getMe"
    response = requests.get(url)
    if response.status_code == 200:
        data: dict[str, Any] = response.json()
        if data.get("ok") is True:
            print(f"бот работает: {data['result']['first_name']}")
        else:
            print("бот получен но есть какая то ошибка")
    else:
        print("Ошибка при запросе к API")


def send_message(chat_id: int, text: str) -> Any:
    """Отправка сообщения пользователю.

    Args:
        chat_id: ID чата куда отправить сообщение.
        text: Текст сообщения.

    Returns:
        Ответ API в формате словаря.
    """
    url = f"{URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, json=payload)
    return response.json()


def get_updates(offset: Optional[int] = None,
                timeout: int = 30) -> Any:
    """Получение обновлений.

    Args:
        offset: ID обновления, с которого начать получение.
        timeout: Время ожидания новых обновлений
          на стороне сервера Telegram.

    Returns:
        Ответ API в формате словаря.
    """
    url = f"{URL}/getUpdates"
    params: dict[str, Any] = {'timeout': timeout}
    if offset is not None:
        params['offset'] = offset
    response = requests.get(url, params=params)
    return response.json()


def get_daily_quote() -> str:
    """Функция получения цитаты и автора с citaty.info.

    Returns:
        Цитата и автор или сообщение об ошибке.
    """
    try:
        url = "https://citaty.info/random"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        random_quote_div = soup.find('a',
                                     class_='citaty_info-quote alink')
        if not isinstance(random_quote_div, Tag):
            return "не найден контейнер с цитатой"

        quote_p = random_quote_div.find('p')
        if not isinstance(quote_p, Tag):
            return "не найден тег <p> с цитатой"

        quote_text = quote_p.get_text(strip=True)

        author_div = soup.find('div', class_="field-item even")
        if not isinstance(author_div, Tag):
            return "не найден контейнер с автором"

        author_link = author_div.find('a')
        if not isinstance(author_link, Tag):
            return "не найден тег с автором"

        author = author_link.get_text(strip=True)

        if author:
            return f"“{quote_text}” - {author}"
        else:
            return f"“{quote_text}”"

    except Exception as e:
        return f"ошибка при запросе к сайту: {e}"


def main() -> None:
    """Основной цикл бота."""
    get_me()
    offset: Optional[int] = None
    while True:
        updates = get_updates(offset=offset, timeout=30)
        if updates.get('ok') and 'result' in updates:
            for update in updates['result']:
                offset = update['update_id'] + 1
                message = update.get('message')
                if message:
                    chat_id = message['chat']['id']
                    text = message.get('text', '')
                    if text == '/start':
                        send_message(chat_id,
                                     "Это эхо-бот. Напиши что-нибудь")
                    elif text == '/quote':
                        quote = get_daily_quote()
                        send_message(chat_id, quote)
                    else:
                        send_message(chat_id, f"Вы сказали: {text}")


if __name__ == '__main__':
    main()
