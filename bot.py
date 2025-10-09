# bot.py — автопостер: берёт запись на СЕГОДНЯ (по Москве) из posts.csv и публикует в канал.
# Сам превращает обычную ссылку Маркета в партнёрскую, если задан AFFIL_TEMPLATE.
import csv, os, html, requests, urllib.parse, re
from datetime import datetime, timezone, timedelta

BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ.get("CHANNEL_ID") or "@topchik_market"

# Москва = UTC+3
MSK = timezone(timedelta(hours=3))
TODAY = datetime.now(MSK).date().isoformat()  # YYYY-MM-DD

# Шаблон партнёрки. Пример для Admitad:
# https://ad.admitad.com/g/ВАШ_КОД/?ulp={URL}
AFFIL_TEMPLATE = os.environ.get("AFFIL_TEMPLATE", "").strip()

def build_caption(title, text, tags):
    cap = f"<b>{html.escape(title)}</b>\n\n{html.escape(text)}"
    if tags:
        cap += f"\n\n<code>{tags}</code>"
    return cap[:1024]

def is_already_affiliate(url: str) -> bool:
    return bool(re.search(r"(admitad|ad\.admitad|partner|aff|utm_source=admitad)", url, re.I))

def make_affiliate_link(market_url: str) -> str:
    """Если задан шаблон, оборачиваем обычную ссылку в партнёрскую."""
    if not market_url:
        return market_url
    if is_already_affiliate(market_url):
        return market_url
    if not AFFIL_TEMPLATE or "{URL}" not in AFFIL_TEMPLATE:
        return market_url
    enc = urllib.parse.quote(market_url, safe="")
    return AFFIL_TEMPLATE.replace("{URL}", enc)

def send_photo_with_button(image_url, caption, button_text, button_url):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": [[{"text": button_text, "url": button_url}]]}
    }
    r = requests.post(api, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def pick_row_for_today(rows):
    # Ищем ровно сегодня
    for r in rows:
        if (r.get("date","").strip() == TODAY):
            return r
    # Если нет — берём ближайшую будущую дату
    pairs = []
    for r in rows:
        d = r.get("date","").strip()
        if not d: 
            continue
        try:
            pairs.append((datetime.strptime(d, "%Y-%m-%d").date(), r))
        except:
            pass
    if not pairs:
        return None
    pairs.sort(key=lambda x: x[0])
    today = datetime.strptime(TODAY, "%Y-%m-%d").date()
    for d, r in pairs:
        if d >= today:
            return r
    return pairs[-1][1]

def main():
    print(f"[DEBUG] Moscow date TODAY = {TODAY}")
    rows = []
    with open("posts.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print("[DEBUG] Dates in posts.csv:", [r.get("date","").strip() for r in rows])

    row = pick_row_for_today(rows)
    if not row:
        print("На сегодня записей нет. Добавь строку в posts.csv с датой", TODAY)
        return

    title       = (row.get("title") or "").strip()
    text        = (row.get("text") or "").strip()
    image_url   = (row.get("image_url") or "").strip()
    button_text = (row.get("button_text") or "Посмотреть").strip()
    market_url  = (row.get("market_url") or row.get("button_url") or "").strip()  # совместимость
    tags        = (row.get("tags") or "").strip()

    if not image_url:
        print("[ERROR] image_url пустой")
        return

    affiliate_url = make_affiliate_link(market_url)
    if not affiliate_url:
        print("[WARN] ссылка пуста — поставим yandex.ru")
        affiliate_url = "https://yandex.ru"

    caption = build_caption(title or "Без названия", text or "", tags)
    resp = send_photo_with_button(image_url, caption, button_text, affiliate_url)
    print("OK:", resp)

if __name__ == "__main__":
    main()
