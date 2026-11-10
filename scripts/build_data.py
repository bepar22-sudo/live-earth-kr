# -*- coding: utf-8 -*-
"""GitHub Actions가 약 10분마다 실행: 브라우저가 직접 받지 못하는(CORS) 자료와
교실에서 여러 명이 한꺼번에 받으면 막힐 수 있는 자료를 data/ 에 저장한다.

- data/flights.json   한반도 주변 항공기 (adsb.lol, 반경 250해리)  — 매번
- data/launches.json  다가오는 로켓 발사 (The Space Devs)          — 매번(시간당 6회, 무료 한도 15회 안)
- data/tle_<무리>.txt 위성 궤도요소 (CelesTrak)                    — 2시간에 한 번 (CelesTrak 요청 규칙)
- data/meta.json      받은 시각

표준 라이브러리만 사용. 실패한 자료는 이전 파일을 그대로 둔다.
"""
import json, os, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
UA = 'LiveEarth-KR-edu/1.0 (educational, non-commercial; GitHub Actions)'
TLE_GROUPS = ['stations', 'visual', 'weather', 'gps-ops', 'geo', 'resource', 'starlink', 'active']
TLE_MAX_AGE = 2 * 3600 - 300
os.makedirs(DATA, exist_ok=True)
meta_path = os.path.join(DATA, 'meta.json')
try:
    meta = json.load(open(meta_path, encoding='utf-8'))
except (OSError, ValueError):
    meta = {}


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save(name, data):
    p = os.path.join(DATA, name)
    with open(p + '.tmp', 'wb') as f:
        f.write(data)
    os.replace(p + '.tmp', p)


def flights():
    lat, lon, dist = 36.0, 127.8, 250
    raw = json.loads(fetch(f'https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist}'))
    out = []
    for a in raw.get('ac', []):
        if a.get('lat') is None or a.get('lon') is None:
            continue
        alt = a.get('alt_baro')
        out.append({'id': a.get('hex'), 'cs': (a.get('flight') or '').strip(), 'reg': a.get('r') or '',
                    'type': a.get('t') or '', 'desc': a.get('desc') or '', 'lat': a['lat'], 'lon': a['lon'],
                    'alt': 0 if alt == 'ground' else (alt or a.get('alt_geom') or 0), 'gnd': alt == 'ground',
                    'gs': a.get('gs') or 0, 'trk': a.get('track') or a.get('true_heading') or 0,
                    'vr': a.get('baro_rate') or 0, 'sq': a.get('squawk') or '',
                    'mil': bool((a.get('dbFlags') or 0) & 1), 'seen': a.get('seen_pos') or 0})
    save('flights.json', json.dumps({'t': time.time(), 'center': [lat, lon], 'dist': dist, 'ac': out},
                                    ensure_ascii=False, separators=(',', ':')).encode())
    return len(out)


def launches():
    raw = json.loads(fetch('https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=12&mode=list'))
    out = []
    for l in raw.get('results', []):
        pad = l.get('pad') or {}
        out.append({'name': l.get('name'), 'net': l.get('net'), 'status': (l.get('status') or {}).get('abbrev', ''),
                    'provider': l.get('lsp_name') or '', 'pad': pad.get('name') if isinstance(pad, dict) else l.get('pad'),
                    'loc': l.get('location') or '',
                    'lat': float(l['latitude']) if l.get('latitude') else None,
                    'lon': float(l['longitude']) if l.get('longitude') else None})
    save('launches.json', json.dumps({'t': time.time(), 'launches': out}, ensure_ascii=False).encode())
    return len(out)


def tles():
    got = 0
    for g in TLE_GROUPS:
        p = os.path.join(DATA, f'tle_{g}.txt')
        if os.path.exists(p) and time.time() - os.path.getmtime(p) < TLE_MAX_AGE:
            continue
        save(f'tle_{g}.txt', fetch(f'https://celestrak.org/NORAD/elements/gp.php?GROUP={g}&FORMAT=tle', 90))
        got += 1
        time.sleep(2)
    return got


for name, fn in (('flights', flights), ('launches', launches), ('tle', tles)):
    try:
        n = fn()
        meta[name] = time.time()
        print(f'{name}: {n}')
    except Exception as e:  # 하나가 실패해도 나머지는 계속
        print(f'{name} 실패: {e}')
meta['built'] = time.time()
save('meta.json', json.dumps(meta).encode())
