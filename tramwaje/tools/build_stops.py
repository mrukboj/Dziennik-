"""Buduje lekką listę przystanków ZTM Gdańsk w tramwaje/stops.json.

Źródło główne: otwarte dane ZTM (CKAN). Gdy ich serwer nie działa, zapasowo
bierze przystanki z rozkładu GTFS ZTM Gdańsk przechowywanego w Mobility Database.
Kopia zapasowa nie nadpisuje świeższej listy pobranej wcześniej z ZTM.
"""
import csv, io, json, os, re, sys, urllib.request, zipfile
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

OUT = 'tramwaje/stops.json'
CKAN = ('https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/'
        'resource/4c4025f0-01bf-41f7-a39f-d156d201b82b/download/stops.json')
CKAN_SOURCES = [CKAN, 'https://tramwaje.mrukboj.workers.dev/?url=' + quote(CKAN, safe='')]
GTFS = 'https://files.mobilitydatabase.org/mdb-2093/latest.zip'
TODAY = datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%Y-%m-%d')


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': 'ktory-tramwaj/1.0'})
    return urllib.request.urlopen(req, timeout=timeout).read()


def from_ckan():
    for src in CKAN_SOURCES:
        try:
            data = json.loads(get(src))
        except Exception as e:
            print(f'CKAN niedostępny ({src[:40]}…): {e}')
            continue
        keys = [k for k, v in data.items() if isinstance(v, dict) and isinstance(v.get('stops'), list)]
        named = lambda k: sum(1 for x in data[k]['stops'] if x.get('stopName'))
        key = TODAY if TODAY in keys and named(TODAY) > 500 else max(keys, key=named)
        seen, out = set(), []
        for x in data[key]['stops']:
            if not x.get('stopName') or x.get('virtual') or x.get('nonpassenger') or x.get('depot'):
                continue
            if x['stopId'] in seen:
                continue
            seen.add(x['stopId'])
            out.append({'id': x['stopId'], 'n': x['stopName'], 'c': x.get('stopCode') or '',
                        'z': x.get('zoneName') or '', 't': x.get('type')})
        return out, 'ztm', key
    return None


def from_gtfs():
    try:
        z = zipfile.ZipFile(io.BytesIO(get(GTFS, 120)))
    except Exception as e:
        print(f'GTFS niedostępny: {e}')
        return None
    rd = lambda name: csv.DictReader(io.TextIOWrapper(z.open(name), encoding='utf-8-sig'))
    route_type = {r['route_id']: r['route_type'] for r in rd('routes.txt')}
    trip_type = {t['trip_id']: route_type.get(t['route_id']) for t in rd('trips.txt')}
    tram_stops, any_stops = set(), set()
    for st in rd('stop_times.txt'):
        any_stops.add(st['stop_id'])
        if trip_type.get(st['trip_id']) == '0':
            tram_stops.add(st['stop_id'])
    out = []
    for s in rd('stops.txt'):
        if s['stop_id'] not in any_stops or not s['stop_id'].isdigit():
            continue
        name = s['stop_name'].strip()
        m = re.match(r'^(.*\S)\s+(\d{2})$', name)
        n, c = (m.group(1), m.group(2)) if m else (name, s.get('stop_code') or '')
        out.append({'id': int(s['stop_id']), 'n': n, 'c': c, 'z': '',
                    't': 'TRAM' if s['stop_id'] in tram_stops else 'BUS'})
    feed_date = ''
    if 'feed_info.txt' in z.namelist():
        fi = next(rd('feed_info.txt'), {})
        feed_date = fi.get('feed_start_date', '')
    return out, 'gtfs', feed_date


result = from_ckan()
if not result:
    if os.path.exists(OUT) and json.load(open(OUT, encoding='utf-8')).get('source') == 'ztm':
        sys.exit('ZTM nie odpowiada, zostawiam dotychczasową listę z ZTM')
    result = from_gtfs()
if not result:
    sys.exit('żadne źródło przystanków nie odpowiada, spróbuję przy następnym uruchomieniu')

stops, source, date = result
if len(stops) < 500:
    sys.exit(f'za mało przystanków: {len(stops)} ({source} {date})')
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'source': source, 'date': date, 'stops': stops}, f, ensure_ascii=False, separators=(',', ':'))
print(f'{len(stops)} przystanków, źródło {source} {date}')
