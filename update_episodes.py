#!/usr/bin/env python3
"""Fetches the latest episode ID for each language show from Transistor
and updates the data-episode-* attributes in index.html."""

import os
import re
import json
import urllib.request

API_KEY = os.environ['TRANSISTOR_API_KEY']

SHOWS = {
    'de': '75629',
    'en': '75728',
    'es': '75733',
    'pt': '75730',
    'fr': '75731',
    'ru': '75734',
}

episode_ids = {}
for lang, show_id in SHOWS.items():
    url = (
        f'https://api.transistor.fm/v1/episodes'
        f'?show_id={show_id}&status=published&order=desc&pagination[per]=1'
    )
    req = urllib.request.Request(url, headers={'x-api-key': API_KEY})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if not data.get('data'):
        print(f'{lang}: no published episodes yet, skipping')
        continue
    episode = data['data'][0]
    attrs = episode['attributes']
    # Extract embed src from embed_html (e.g. <iframe src="https://share.transistor.fm/e/abc1234" ...>)
    embed_html = attrs.get('embed_html', '') or attrs.get('embed_html_dark', '')
    match = re.search(r'src="https://share\.transistor\.fm/e/([^"]+)"', embed_html)
    if match:
        token = match.group(1)
    else:
        # Fallback: use numeric id
        token = episode['id']
    episode_ids[lang] = token
    print(f'{lang}: {token}')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

for lang, ep_id in episode_ids.items():
    content = re.sub(
        rf'data-episode-{lang}="[^"]*"',
        f'data-episode-{lang}="{ep_id}"',
        content,
    )

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('index.html updated.')
