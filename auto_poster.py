# auto_poster.py — тянет товары с Яндекс.Маркета из категории/поиска, постит 2–4 раза в день.
# Требуются секреты: BOT_TOKEN, CHANNEL_ID, AFFIL_TEMPLATE, CATEGORY_URL, POSTS_PER_RUN (опц.)
import os, re, time, hashlib, json, random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

BOT_TOKEN       = os.getenv("BOT_TOKEN")
CHANNEL_ID      = os.getenv("CHANNEL_ID")
AFFIL_TEMPLATE  = os.getenv("AFFIL_TEMPLATE")               # напр. https://market.yandex.ru/cc/7kgFor?url={URL}
CATEGORY_URL    = os.getenv("CATEGORY_URL")                 # ссылка на категорию/поиск (например, одежда)
POSTS_PER_RUN   = int(os.getenv("POSTS_PER_RUN", "2"))      # сколько постов за запуск (2–4)
USER_AGENT      = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

POSTED_FILE     = "posted.json"  # храним уже опубликованные товары (чтобы не дублировать)

def load_posted():
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_posted(s):
    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(s)), f, ensure_ascii=False, indent=2)

def affiliate(url: str) -> str:
    if not url:
        return url
    if "{URL}" in AFFIL_TEMPLATE:
        return AFFIL_TEMPLATE.replace("{URL}", quote(url, safe=""))
    return AFFIL_TEMPLATE  # на крайний случай

def fetch_list(url: str):
    """Парсим карточки с первой страницы списка. Работает и для категорий, и для поиска."""
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    items = []
    # Ссылки на карточки: /product--.../ID
    for a in soup.select("a[href*='/product--']"):
        href = a.get("href") or ""
        full = urljoin("https://market.yandex.ru", href)
        # Заголовок
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        # Картинка — попробуем найти ближайшее img
        img = None
        pic = a.find("img")
        if pic and (pic.get("src") or pic.get("data-src")):
            img = pic.get("src") or pic.get("data-src")
        # Уберём служебные мусорные урлы
        if not re.search(r"/product--", full):
            continue
        # Если заголовка нет, попытаемся вытащить из текста-родителя
        if not title:
            parent = a.find_parent()
            if parent:
                title = parent.get_text(" ", strip=True)[:120]
        if not title:
            continue
        items.append({
            "title": title[:120],
            "url": full.split("?")[0],  # чистим хвост
            "image": img
        })

    # Удалим дубликаты по url
    uniq = {}
    for it in items:
        uniq[it["url"]] = it
    return list(uniq.values())

def send_photo(title, photo_url, button_url):
    caption = f"🛍️ {title}\n\nПерейти ➜"
    payload = {
        "chat_id": CHANNEL_ID,
        "photo": photo_url or "https://picsum.photos/1200/675?random=777",
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": [[{"text": "Посмотреть на Маркете", "url": button_url}]]}
    }
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def main():
    assert BOT_TOKEN and CHANNEL_ID and AFFIL_TEMPLATE and CATEGORY_URL, "ENV vars missing"

    posted = load_posted()
    print("[DEBUG] already posted:", len(posted))

    items = fetch_list(CATEGORY_URL)
    random.shuffle(items)
    print(f"[DEBUG] parsed {len(items)} items from list")

    sent = 0
    for it in items:
        if sent >= POSTS_PER_RUN:
            break
        uid = hashlib.md5(it["url"].encode("utf-8")).hexdigest()
        if uid in posted:
            continue
        ref = affiliate(it["url"])
        try:
            print("[POST]", it["title"], it["url"])
            res = send_photo(it["title"], it.get("image"), ref)
            print("OK:", res.get("result", {}).get("message_id"))
            posted.add(uid)
            sent += 1
            time.sleep(2)
        except Exception as e:
            print("[ERR]", e)

    save_posted(posted)
    if sent == 0:
        print("Новых карточек не нашли. Попробуй другую ссылку CATEGORY_URL или очисти posted.json.")

if __name__ == "__main__":
    main()
