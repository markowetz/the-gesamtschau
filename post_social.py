#!/usr/bin/env python3
"""
post_social.py — Neueste Neuigkeit auf LinkedIn (EN) und Facebook (DE) posten.

Liest den ersten Eintrag aus posts.json und postet:
  LinkedIn: Englische Version
  Facebook: Deutsche Version

Benötigte Umgebungsvariablen:
  LINKEDIN_ACCESS_TOKEN
  FACEBOOK_PAGE_TOKEN
  FACEBOOK_PAGE_ID

Aufruf:
  python3 post_social.py
"""

import json
import os
import sys
import requests

POSTS_FILE = "posts.json"
WEBSITE_URL = "https://www.the-gesamtschau.de"


def load_latest_post():
    if not os.path.exists(POSTS_FILE):
        print(f"Fehler: {POSTS_FILE} nicht gefunden.")
        sys.exit(1)
    with open(POSTS_FILE, encoding="utf-8") as f:
        posts = json.load(f)
    if not posts:
        print("Keine Einträge in posts.json.")
        sys.exit(1)
    return posts[0]


def post_to_linkedin(post_text: str, access_token: str) -> str:
    me_r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    me_r.raise_for_status()
    person_urn = me_r.json()["sub"]
    if not person_urn.startswith("urn:li:person:"):
        person_urn = f"urn:li:person:{person_urn}"

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.headers.get("x-restli-id", "?")


def post_to_facebook(post_text: str, page_token: str, page_id: str) -> str:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{page_id}/feed",
        data={"message": post_text, "access_token": page_token},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("id", "?")


def format_post(title: str, body: str) -> str:
    return f"{title}\n\n{body}\n\n{WEBSITE_URL}"


def main():
    post = load_latest_post()

    en = post["translations"]["en"]
    de = post["translations"]["de"]

    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    fb_token = os.getenv("FACEBOOK_PAGE_TOKEN")
    fb_page_id = os.getenv("FACEBOOK_PAGE_ID")

    errors = []

    # LinkedIn (English)
    if linkedin_token:
        print("→ LinkedIn (EN) ...", end=" ", flush=True)
        try:
            urn = post_to_linkedin(format_post(en["title"], en["body"]), linkedin_token)
            print(f"✓ ({urn})")
        except Exception as e:
            print(f"✗ ({e})")
            errors.append(f"LinkedIn: {e}")
    else:
        print("⚠ LinkedIn übersprungen (LINKEDIN_ACCESS_TOKEN fehlt)")

    # Facebook (German)
    if fb_token and fb_page_id:
        print("→ Facebook (DE) ...", end=" ", flush=True)
        try:
            post_id = post_to_facebook(format_post(de["title"], de["body"]), fb_token, fb_page_id)
            print(f"✓ ({post_id})")
        except Exception as e:
            print(f"✗ ({e})")
            errors.append(f"Facebook: {e}")
    else:
        print("⚠ Facebook übersprungen (FACEBOOK_PAGE_TOKEN oder FACEBOOK_PAGE_ID fehlt)")

    if errors:
        print("\nFehler aufgetreten:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
