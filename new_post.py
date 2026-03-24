#!/usr/bin/env python3
"""
new_post.py — Neuen Blog-Post erstellen und in 5 Sprachen übersetzen.

Liest post_draft.md:
    # Titel des Posts

    Text hier. Mehrere Absätze durch Leerzeile getrennt.

Übersetzt via Claude API nach EN/ES/PT/FR/RU und schreibt in posts.json (neueste zuerst).

Aufruf:
    python3 new_post.py
"""

import json
import os
import re
import sys
from datetime import date
import anthropic

DRAFT_FILE = "post_draft.md"
POSTS_FILE = "posts.json"

LANG_NAMES = {
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
    "fr": "French",
    "ru": "Russian",
}


def read_draft():
    if not os.path.exists(DRAFT_FILE):
        print(f"Fehler: {DRAFT_FILE} nicht gefunden.")
        print(f"Bitte erstelle {DRAFT_FILE} mit folgendem Format:")
        print("  # Titel des Posts")
        print()
        print("  Textinhalt hier...")
        sys.exit(1)

    with open(DRAFT_FILE, encoding="utf-8") as f:
        content = f.read().strip()

    lines = content.split("\n")
    title = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()

    if not title:
        print("Fehler: Kein Titel gefunden. Erste Zeile muss mit '# ' beginnen.")
        sys.exit(1)
    if not body:
        print("Fehler: Kein Text gefunden.")
        sys.exit(1)

    return title, body


def translate(client, title, body, lang):
    lang_name = LANG_NAMES[lang]
    prompt = f"""Translate the following German blog post to {lang_name}.
Keep the same tone, style, and paragraph structure.
Return ONLY a JSON object with keys "title" and "body". No other text, no markdown code blocks.

Title: {title}

Body:
{body}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def make_id(posts):
    base = date.today().isoformat()
    existing = {p["id"] for p in posts}
    if base not in existing:
        return base
    for i in range(2, 100):
        candidate = f"{base}-{i}"
        if candidate not in existing:
            return candidate
    return f"{base}-{len(posts)}"


def main():
    title_de, body_de = read_draft()
    print(f"Post: {title_de}")
    print()

    client = anthropic.Anthropic()
    translations = {"de": {"title": title_de, "body": body_de}}

    for lang in ["en", "es", "pt", "fr", "ru"]:
        print(f"  Übersetze → {lang.upper()} ...", end=" ", flush=True)
        t = translate(client, title_de, body_de, lang)
        translations[lang] = t
        print("✓")

    posts = []
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, encoding="utf-8") as f:
            posts = json.load(f)

    post = {
        "id": make_id(posts),
        "date": date.today().isoformat(),
        "translations": translations,
    }
    posts.insert(0, post)

    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print()
    print(f"✓ Post gespeichert ({POSTS_FILE}, {len(posts)} Einträge gesamt)")
    print("Nächster Schritt: /deployen")


if __name__ == "__main__":
    main()
