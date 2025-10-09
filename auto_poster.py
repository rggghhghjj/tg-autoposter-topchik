import os, time, random, hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

BOT_TOKEN      = os.getenv("BOT_TOKEN")
CHANNEL_ID     = os.getenv("CHANNEL_ID")
AFFIL_TEMPLATE = os.getenv("AFFIL_TEMPLATE")            # напр. https://market.yandex.ru/cc/7kgFor?url={URL}
CATEGORY_URL   = os.getenv("CATEGORY_URL")              # напр. https://market.yandex.ru/catalog--odezhda-obuv-i-aksessuary/54432/list
POSTS_PER_RUN  = int(os.getenv("POSTS_PER_RUN", "2"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9"
}

def affil(url: str) -> str:
    # Подставляем в шаблон и экранируем
    return AFFIL_TEMPLATE.replace("{URL}", quote(url, safe=""))

def fetch_products(list_url: str):
    """Тянем только реальные карточки /product--… с категории/поиска."""
    r = requests.get(list_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    products = []
    # 1) Жёсткий фильтр: только анкоры со ссылкой на карточку товара
    for a in soup.select('a[href*="/product--"]'):
        href = a.get("href") or ""
        full = urljoin("https://market.yandex.ru", href)  # нормализация (никаких двойных доменов)

        # Заголовок
        title = a.get("title") or a.get_text(" ", strip=True)
        if not title:
            # иногда текст в родителе
            p = a.find_parent()
            if p:
                title = p.get_text(" ", strip=True)
        title = (title or "").strip()
        if not title:
            continue

        # Картинка рядом/внутри
        img = None
        img_tag = a.find("img")
        if img_tag:
            img = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-lazy-src")
            if img:
                img = urljoin("https://market.yandex.ru", img)

        products.append({"title": title[:120], "url": full, "img": img})

    # Удаляем дубли по URL
    uniq = {}
    for p in products:
        uniq[p["url"]] = p
    products = list(uniq.values())

    # Фильтрация на всякий случай: только /product--… (ещё раз)
    products = [p for p in products if "/product--" in p["url"]]

    return products

def send_to_telegram(title: str, link: str, image: str | None):
    caption = f"<b>{title}</b>\n\n🛒 Купить: {link}"
    if image:
        # фото с подписью
        files = {}
        try:
            img_bytes = requests.get(image, headers=HEADERS, timeout=20).content
            files = {"photo": ("img.jpg", img_bytes)}
            data = {"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"}
            r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=data, files=files, timeout=30)
        except Exception:
            # если картинка не скачалась — отправим текст
            r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                              data={"chat_id": CHANNEL_ID, "text": caption, "parse_mode": "HTML"}, timeout=30)
    else:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          data={"chat_id": CHANNEL_ID, "text": caption, "parse_mode": "HTML"}, timeout=30)
    r.raise_for_status()

def main():
    assert BOT_TOKEN and CHANNEL_ID and AFFIL_TEMPLATE and CATEGORY_URL, "ENV vars missing"
    print("[INFO] CATEGORY_URL:", CATEGORY_URL)

    items = fetch_products(CATEGORY_URL)
    print(f"[INFO] найдено карточек: {len(items)}")
    if not items:
        print("[WARN] На странице не нашли /product--*. Проверь CATEGORY_URL.")
        return

    random.shuffle(items)
    take = min(POSTS_PER_RUN, len(items))
    picked = items[:take]

    for i, it in enumerate(picked, 1):
        ref = affil(it["url"])
        print(f"[POST {i}/{take}] {it['title']} -> {ref}")
        try:
            send_to_telegram(it["title"], ref, it["img"])
            time.sleep(2)
        except Exception as e:
            print("[ERR]", e)

    print("[DONE] Готово.")

if __name__ == "__main__":
    main()
