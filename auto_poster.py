import requests
import csv
import os
from bs4 import BeautifulSoup
import random
import time

# Загружаем переменные из секретов GitHub
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CATEGORY_URL = os.getenv("CATEGORY_URL")
AFFIL_TEMPLATE = os.getenv("AFFIL_TEMPLATE")
POSTS_PER_RUN = int(os.getenv("POSTS_PER_RUN", "2"))  # по умолчанию 2 поста

# --- Функция отправки сообщений в Telegram ---
def send_to_telegram(text, image_url=None):
    try:
        if image_url:
            # Отправляем фото с подписью
            photo_data = requests.get(image_url).content
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={
                    "chat_id": CHANNEL_ID,
                    "caption": text,
                    "parse_mode": "HTML"
                },
                files={"photo": ("image.jpg", photo_data)}
            )
        else:
            # Только текст
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": CHANNEL_ID,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")


# --- Функция получения товаров с Яндекс.Маркета ---
def get_products():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CATEGORY_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Ищем карточки товаров (адаптировано под структуру Маркета)
    cards = soup.select("article") or soup.select("div[data-zone-name='snippet-card']")
    products = []

    for card in cards:
        title_tag = card.select_one("h3") or card.select_one("a")
        img_tag = card.select_one("img")
        link_tag = card.select_one("a[href]")

        if not title_tag or not link_tag:
            continue

        title = title_tag.text.strip()
        img = img_tag["src"] if img_tag and img_tag.get("src") else None
        url = "https://market.yandex.ru" + link_tag["href"]

        # создаём партнёрскую ссылку
        affil_url = AFFIL_TEMPLATE.replace("{URL}", url)
        products.append({"title": title, "img": img, "url": affil_url})

    return products


# --- Основной процесс ---
def main():
    print("🔄 Получаем список товаров...")
    products = get_products()
    if not products:
        print("⚠️ Не удалось получить товары. Проверь ссылку CATEGORY_URL.")
        return

    print(f"✅ Найдено товаров: {len(products)}")

    # выбираем случайные товары (чтобы посты были разными)
    selected = random.sample(products, min(POSTS_PER_RUN, len(products)))

    for product in selected:
        text = f"<b>{product['title']}</b>\n\n🛒 Купить: {product['url']}"
        print(f"📤 Отправляем: {product['title']}")
        send_to_telegram(text, product["img"])
        time.sleep(5)  # пауза между постами

    print("✅ Публикация завершена!")


if __name__ == "__main__":
    main()

