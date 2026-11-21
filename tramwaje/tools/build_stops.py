"""Pobiera listę przystanków ZTM Gdańsk i zapisuje jej lekką wersję do tramwaje/stops.json."""
import json, sys, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

URL = ('https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/'
       'resource/4c4025f0-01bf-41f7-a39f-d156d201b82b/download/stops.json')

import time
from urllib.parse import quote

SOURCES = [URL, 'https://tramwaje.mrukboj.workers.dev/?url=' + quote(URL, safe='')]
data = None
for attempt in range(3):
    for src in SOURCES:
        try:
            req = urllib.request.Request(src, headers={'User-Agent': 'ktory-tramwaj/1.0'})
            data = json.load(urllib.request.urlopen(req, timeout=90))
            break
        except Exception as e:
            print(f'nie udało się ({src[:40]}…): {e}')
    if data:
        break
    time.sleep(60)
if not data:
    sys.exit('serwer ZTM z listą przystanków nie odpowiada, spróbuję przy następnym uruchomieniu')

today = datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%Y-%m-%d')
keys = [k for k, v in data.items() if isinstance(v, dict) and isinstance(v.get('stops'), list)]
named = lambda k: sum(1 for x in data[k]['stops'] if x.get('stopName'))
key = today if today in keys and named(today) > 500 else max(keys, key=named)

seen, out = set(), []
for x in data[key]['stops']:
    if not x.get('stopName') or x.get('virtual') or x.get('nonpassenger') or x.get('depot'):
        continue
    if x['stopId'] in seen:
        continue
    seen.add(x['stopId'])
    out.append({'id': x['stopId'], 'n': x['stopName'], 'c': x.get('stopCode') or '',
                'z': x.get('zoneName') or '', 't': x.get('type')})

if len(out) < 500:
    sys.exit(f'za mało przystanków: {len(out)} (klucz {key})')

with open('tramwaje/stops.json', 'w', encoding='utf-8') as f:
    json.dump({'date': key, 'stops': out}, f, ensure_ascii=False, separators=(',', ':'))
print(f'{len(out)} przystanków z dnia {key}')
