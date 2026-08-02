#!/usr/bin/env python3
"""Pick a quote from quotes.xlsx and email it, avoiding yesterday's repeat."""
import argparse
import json
import os
import random
import smtplib
import ssl
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
QUOTES_FILE = ROOT / "quotes.xlsx"
HISTORY_FILE = ROOT / "data" / "history.json"
HISTORY_LIMIT = 60

SENDER_EMAIL = os.environ.get("EMAIL_SENDER", "stanleysunrock@gmail.com")
RECIPIENT_EMAIL = os.environ.get("EMAIL_RECIPIENT", "34ko345@gmail.com")
APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def load_quotes():
    df = pd.read_excel(QUOTES_FILE)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "quote" not in df.columns:
        raise ValueError("quotes.xlsx must have a 'quote' column")

    quotes = []
    for _, row in df.iterrows():
        text = str(row.get("quote", "")).strip()
        if not text or text.lower() == "nan":
            continue
        author = str(row.get("author", "")).strip()
        if author.lower() == "nan":
            author = ""
        tags_raw = row.get("tags", "")
        tags = []
        if isinstance(tags_raw, str) and tags_raw.strip():
            tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
        quotes.append({"quote": text, "author": author, "tags": tags})
    return quotes


def active_seasonal_tags(today: date) -> set:
    """Context tags for today: season, nearby holidays, and day-of-week mood."""
    tags = set()
    m, d = today.month, today.day

    if today.weekday() == 0:  # Monday
        tags.add("monday")

    if m in (12, 1, 2):
        tags.add("winter")
    elif m in (3, 4, 5):
        tags.add("spring")
    elif m in (6, 7, 8):
        tags.add("summer")
    else:
        tags.add("fall")

    if (m, d) >= (12, 26) or (m, d) <= (1, 1):
        tags.add("new_year")
    if m == 2 and 7 <= d <= 14:
        tags.add("valentines")
    if m == 11 and 20 <= d <= 30:
        tags.add("thanksgiving")
    if m == 12 and 1 <= d <= 25:
        tags.add("holidays")
    if d == 1 or m == 1:
        tags.add("new_beginnings")

    return tags


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history[-HISTORY_LIMIT:], indent=2))


def choose_quote(quotes, history, today):
    last_text = history[-1]["quote"] if history else None
    seasonal = active_seasonal_tags(today)

    # Prefer quotes tagged for today's season/holiday, but fall back to the
    # full pool if nothing matches (untagged quotes are always general-purpose).
    pool = quotes
    seasonal_pool = [q for q in quotes if seasonal.intersection(q["tags"])]
    if seasonal_pool:
        pool = seasonal_pool

    candidates = [q for q in pool if q["quote"] != last_text]
    if not candidates:
        candidates = [q for q in quotes if q["quote"] != last_text] or quotes
    return random.choice(candidates)


def build_email(quote):
    lines = [f'"{quote["quote"]}"']
    if quote["author"]:
        lines.append(f'— {quote["author"]}')
    body = "\n\n".join(lines)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Your Daily Quote — {date.today().strftime('%B %d, %Y')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    return msg


def send_email(msg):
    if not APP_PASSWORD:
        raise RuntimeError(
            "EMAIL_APP_PASSWORD environment variable is not set. "
            "Use a Gmail App Password, not your regular password."
        )
    context = ssl.create_default_context()
    # Gmail displays app passwords as "abcd efgh ijkl mnop"; strip any spaces
    # in case the secret was pasted with them.
    password = APP_PASSWORD.strip().replace(" ", "")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SENDER_EMAIL, password)
        server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pick and print today's quote without sending an email or updating history.",
    )
    args = parser.parse_args()

    today = date.today()
    quotes = load_quotes()
    if not quotes:
        raise RuntimeError("No quotes found in quotes.xlsx")

    history = load_history()
    chosen = choose_quote(quotes, history, today)

    if args.dry_run:
        print(f"[dry run] Would send: \"{chosen['quote']}\" — {chosen['author'] or 'Unknown'}")
        print(f"[dry run] Active context tags: {sorted(active_seasonal_tags(today))}")
        return

    send_email(build_email(chosen))

    history.append({
        "date": today.isoformat(),
        "quote": chosen["quote"],
        "author": chosen["author"],
    })
    save_history(history)

    print(f"Sent: \"{chosen['quote']}\" — {chosen['author'] or 'Unknown'}")


if __name__ == "__main__":
    main()
