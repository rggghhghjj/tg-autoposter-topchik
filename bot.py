# bot.py — простой автопостер: берёт пост на сегодня из posts.csv и публикует в канал
import csv, os, datetime, html, requests

BOT_TOKEN  = os.environ["BOT_TOKEN"]                 # токен бота из BotFather (добавим позже в Secrets)
CHANNEL_ID = os.environ.get("CHANNEL_ID") or "@topchik_market"  # твой канал

TODAY = datetime.datetime.utcnow().date().isoformat()  # дата по UTC, формат YYYY-MM-DD

def build_caption(title, text, tags):
    # подпись под фото (лимит Telegram ~1024 символа)
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
    posted_any = False
    with open("posts.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["date"].strip() == TODAY:
                title       = row["title"].strip()
                text        = row["text"].strip()
                image_url   = row["image_url"].strip()
                button_text = (row.get("button_text") or "Посмотреть").strip()
                button_url  = row["button_url"].strip()
                tags        = (row.get("tags") or "").strip()

                caption = build_caption(title, text, tags)
                resp = send_photo_with_button(image_url, caption, button_text, button_url)
                print("OK:", resp)
                posted_any = True

    if not posted_any:
        print("На сегодня записей нет. Добавь строку в posts.csv с датой", TODAY)

if __name__ == "__main__":
    main()
