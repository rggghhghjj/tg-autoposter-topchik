# bot.py — автопостер: берёт запись на СЕГОДНЯ (по Москве) из posts.csv и публикует в канал.
import csv, os, html, requests
from datetime import datetime, timezone, timedelta

BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ.get("CHANNEL_ID") or "@topchik_market"

# Москва = UTC+3
MSK = timezone(timedelta(hours=3))
TODAY = datetime.now(MSK).date().isoformat()  # YYYY-MM-DD

def build_caption(title, text, tags):
    cap = f"<b>{html.escape(title)}</b>\n\n{html.escape(text)}"
    if tags:
        cap += f"\n\n<code>{tags}</code>"
    return cap[:1024]

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

def main():
    print(f"[DEBUG] Moscow date TODAY = {TODAY}")
    rows = []
    with open("posts.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Печатаем все даты, которые видим в файле
    print("[DEBUG] Dates in posts.csv:", [r.get("date", "").strip() for r in rows])

    # Ищем строку ровно на сегодня
    today_rows = [r for r in rows if r.get("date", "").strip() == TODAY]

    selected = None
    if today_rows:
        selected = today_rows[0]
        print(f"[DEBUG] Found TODAY row: {selected}")
    else:
        # Если на сегодня не нашли — возьмём ближайшую будущую дату (для теста)
        try:
            pairs = []
            for r in rows:
                d = r.get("date", "").strip()
                if not d:
                    continue
                pairs.append((datetime.strptime(d, "%Y-%m-%d").date(), r))
            pairs.sort(key=lambda x: x[0])
            # берём первую дату >= сегодня
            for d, r in pairs:
                if d >= datetime.strptime(TODAY, "%Y-%m-%d").date():
                    selected = r
                    print(f"[DEBUG] Fallback picked row for date {d}: {selected}")
                    break
            # если и это не получилось — берём самую последнюю строку
            if not selected and pairs:
                selected = pairs[-1][1]
                print(f"[DEBUG] Fallback picked LAST row: {selected}")
        except Exception as e:
            print("[DEBUG] Date parse error:", e)

    if not selected:
        print("На сегодня записей нет. Добавь строку в posts.csv с датой", TODAY)
        return

    title       = (selected.get("title") or "").strip()
    text        = (selected.get("text") or "").strip()
    image_url   = (selected.get("image_url") or "").strip()
    button_text = (selected.get("button_text") or "Посмотреть").strip()
    button_url  = (selected.get("button_url") or "").strip()
    tags        = (selected.get("tags") or "").strip()

    if not image_url:
        print("[ERROR] image_url пустой")
        return
    if not button_url:
        print("[WARN] button_url пустой — кнопка откроет yandex.ru")
        button_url = "https://yandex.ru"

    caption = build_caption(title or "Без названия", text or "", tags)
    resp = send_photo_with_button(image_url, caption, button_text, button_url)
    print("OK:", resp)

if __name__ == "__main__":
    main()
