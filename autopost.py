import os
import requests
import random

# Телеграм данные
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Партнёрская ссылка
AFFIL_TEMPLATE = os.getenv("AFFIL_TEMPLATE")

# Пример популярных товаров (можно заменить своими)
PRODUCTS = [
    {
        "title": "Женская тёплая кофта на молнии",
        "url": "https://market.yandex.ru/product--zhenskaia-kofta-na-molnii/123456",
        "image": "https://avatars.mds.yandex.net/get-mpic/5231234/img_id123456.jpeg/600x600"
    },
    {
        "title": "Удлинённая женская парка зимняя",
        "url": "https://market.yandex.ru/product--zhenskaia-zimniaia-parka/789012",
        "image": "https://avatars.mds.yandex.net/get-mpic/5231234/img_id789012.jpeg/600x600"
    },
    {
        "title": "Тёплое худи oversize",
        "url": "https://market.yandex.ru/product--zhenskoe-hudi-oversize/345678",
        "image": "https://avatars.mds.yandex.net/get-mpic/5231234/img_id345678.jpeg/600x600"
    }
]

# Выбираем случайный товар
product = random.choice(PRODUCTS)

# Формируем партнёрскую ссылку
ref_link = AFFIL_TEMPLATE.replace("{URL}", product["url"])

# Формируем текст поста
caption = f"🔥 {product['title']}\n\nКупить со скидкой ➡️ {ref_link}"

# Отправляем пост в Telegram
send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
data = {
    "chat_id": CHAT_ID,
    "caption": caption,
    "photo": product["image"]
}
response = requests.post(send_url, data=data)
print(response.text)
