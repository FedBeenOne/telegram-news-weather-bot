# Telegram-бот: новости, погода, цитаты

Асинхронный Telegram-бот на чистом [Telegram Bot API](https://core.telegram.org/bots/api), без фреймворков вроде aiogram.
Long polling, `getUpdates`, `sendMessage` и учёт `offset` реализованы вручную.

## Что умеет

| Команда | Что делает |
|---|---|
| `/start`, `/help` | Список команд |
| `/headlines` | Параллельно собирает свежие заголовки с трёх новостных сайтов (РБК, РИА Новости, музыкальные новости) |
| `/weather` | Спрашивает город и присылает текущую погоду через OpenWeatherMap API |
| `/quote` | Случайная цитата с citaty.info |
| любой другой текст | Эхо-ответ |

## Как устроено

- **Асинхронность.** `aiohttp` + `asyncio`. Одна `ClientSession` на всё приложение передаётся во все функции, которые ходят в сеть.
- **Конкурентные запросы.** `/headlines` запускает три парсера одновременно через `asyncio.gather(..., return_exceptions=True)`, поэтому ошибка одного сайта не ломает ответ целиком.
- **Блокирующий код вне event loop.** Синхронный парсер цитат на `requests` вызывается через `asyncio.to_thread`.
- **Состояние диалога.** После `/weather` бот запоминает, что ждёт от пользователя название города (простая машина состояний на словаре `user_states`).
- **Обработка ошибок.** Отдельно обрабатываются сетевые ошибки, HTTP-статусы (200, 404 и прочие) и сбои парсинга HTML.
- **Конфигурация.** Токены и адреса лежат в `.env` и в репозиторий не попадают.

В репозитории две версии:

- `async_bot.py` — основная, асинхронная (aiohttp), со всеми командами;
- `sync_bot.py` — первая синхронная версия на `requests` (эхо и `/quote`), оставлена для сравнения подходов.

## Запуск

Нужен Python 3.9+.

```bash
git clone https://github.com/FedBeenOne/telegram-news-weather-bot.git
cd telegram-news-weather-bot

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # и заполнить своими значениями
python async_bot.py
```

### Переменные окружения

| Переменная | Что это |
|---|---|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `WEATHER_API` | API-ключ [OpenWeatherMap](https://openweathermap.org/api) |
| `OPENWEATHERSITE` | Адрес API погоды |
| `RBK`, `RIA`, `MUSIC` | Адреса страниц, с которых парсятся заголовки |

## Стек

Python · asyncio · aiohttp · requests · BeautifulSoup4 · python-dotenv · Telegram Bot API · OpenWeatherMap API

## Ограничения

Заголовки достаются парсингом HTML по CSS-классам. Если сайт поменяет вёрстку, соответствующий парсер начнёт возвращать сообщение об ошибке, а остальные продолжат работать.
