# -*- coding: utf-8 -*-
"""지구 실시간 보기 — 중계 서버 (God's Eye View 한국어 경량판)

사용: python server.py [--port 8780] [--open]
- 이 폴더의 index.html·fonts 를 보여 주고,
- 키 없이 쓰는 공개 데이터(항공기·위성·지진·로켓 발사)를 대신 받아 와서(브라우저 CORS 문제 해결)
  잠깐 저장(캐시)해 두었다가 화면에 넘겨 준다.
- 127.0.0.1(이 PC)에서만 열린다. 표준 라이브러리만 사용(설치할 것 없음).
"""
import json, os, sys, threading, time, urllib.parse, urllib.request, webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(ROOT, '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def set_cache_dir(path):
    """다른 프로그램(예: 전광판원격)이 이 파일을 모듈로 쓸 때 저장본 폴더를 바꾼다."""
    global CACHE_DIR
    CACHE_DIR = path
    os.makedirs(CACHE_DIR, exist_ok=True)


def handle_api(path, query_string):
    """API 한 건 처리 → (상태코드, Content-Type, 본문 bytes). 다른 프로그램에서도 부름."""
    if path not in ROUTES:
        return 404, 'application/json; charset=utf-8', b'{"error":"not found"}'
    try:
        data, _stale = ROUTES[path](urllib.parse.parse_qs(query_string))
        ctype = 'text/plain; charset=utf-8' if path == '/api/sats' else 'application/json; charset=utf-8'
        return 200, ctype, data
    except Exception as e:
        return 502, 'application/json; charset=utf-8', json.dumps({'error': str(e)}, ensure_ascii=False).encode()
UA = 'GlobeViewer-KR/1.0 (personal, non-commercial)'

_mem = {}            # key -> (time, bytes)
_lock = threading.Lock()


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def cached(key, ttl, producer, disk=False):
    """ttl 초 동안은 저장본을 돌려줌. 받아오기 실패하면 오래된 저장본이라도 돌려줌."""
    now = time.time()
    with _lock:
        hit = _mem.get(key)
    if hit is None and disk:
        p = os.path.join(CACHE_DIR, key.replace('/', '_') + '.bin')
        if os.path.exists(p):
            hit = (os.path.getmtime(p), open(p, 'rb').read())
            with _lock:
                _mem[key] = hit
    if hit and now - hit[0] < ttl:
        return hit[1], False
    try:
        data = producer()
    except Exception:
        if hit:
            return hit[1], True      # 오래된 자료(stale)
        raise
    with _lock:
        _mem[key] = (now, data)
    if disk:
        with open(os.path.join(CACHE_DIR, key.replace('/', '_') + '.bin'), 'wb') as f:
            f.write(data)
    return data, False


# ---------- 데이터 원천 ----------
def flights(q):
    lat = round(float(q.get('lat', ['35.87'])[0]) * 2) / 2      # 0.5도 단위로 묶어 캐시
    lon = round(float(q.get('lon', ['128.6'])[0]) * 2) / 2
    dist = max(10, min(250, int(float(q.get('dist', ['250'])[0]))))

    def prod():
        raw = json.loads(fetch(f'https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist}'))
        out = []
        for a in raw.get('ac', []):
            if a.get('lat') is None or a.get('lon') is None:
                continue
            alt = a.get('alt_baro')
            out.append({
                'id': a.get('hex'), 'cs': (a.get('flight') or '').strip(), 'reg': a.get('r') or '',
                'type': a.get('t') or '', 'desc': a.get('desc') or '', 'lat': a['lat'], 'lon': a['lon'],
                'alt': 0 if alt == 'ground' else (alt or a.get('alt_geom') or 0),
                'gnd': alt == 'ground', 'gs': a.get('gs') or 0, 'trk': a.get('track') or a.get('true_heading') or 0,
                'vr': a.get('baro_rate') or 0, 'sq': a.get('squawk') or '',
                'mil': bool((a.get('dbFlags') or 0) & 1), 'seen': a.get('seen_pos') or 0,
            })
        return json.dumps({'t': time.time(), 'center': [lat, lon], 'dist': dist, 'ac': out}).encode()
    return cached(f'flights_{lat}_{lon}_{dist}', 8, prod)


SAT_GROUPS = {'stations', 'visual', 'gps-ops', 'weather', 'starlink', 'active', 'geo', 'resource', 'science'}


def sats(q):
    g = q.get('group', ['stations'])[0]
    if g not in SAT_GROUPS:
        raise ValueError('unknown group')
    # CelesTrak 요청 규칙: 같은 자료는 2시간에 한 번만 → 디스크에도 저장
    return cached(f'tle_{g}', 2 * 3600, lambda: fetch(
        f'https://celestrak.org/NORAD/elements/gp.php?GROUP={g}&FORMAT=tle', 60), disk=True)


def quakes(q):
    p = q.get('period', ['day'])[0]
    feed = {'day': '2.5_day', 'week': '4.5_week', 'hour': 'all_hour'}.get(p, '2.5_day')
    return cached(f'quakes_{feed}', 60, lambda: fetch(
        f'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{feed}.geojson'))


def launches(q):
    def prod():
        raw = json.loads(fetch('https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=12&mode=list'))
        out = []
        for l in raw.get('results', []):
            pad = l.get('pad') or {}
            out.append({'name': l.get('name'), 'net': l.get('net'), 'status': (l.get('status') or {}).get('abbrev', ''),
                        'provider': l.get('lsp_name') or '', 'pad': pad.get('name') if isinstance(pad, dict) else l.get('pad'),
                        'loc': l.get('location') or '',
                        'lat': float(l['latitude']) if l.get('latitude') else None,
                        'lon': float(l['longitude']) if l.get('longitude') else None})
        return json.dumps({'t': time.time(), 'launches': out}).encode()
    # The Space Devs 무료 한도(시간당 15회) → 30분 캐시, 디스크 저장
    return cached('launches', 1800, prod, disk=True)


ROUTES = {'/api/flights': flights, '/api/sats': sats, '/api/quakes': quakes, '/api/launches': launches}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        p = urllib.parse.urlparse(self.path).path      # ?board=1 같은 꼬리는 떼고 판단
        self.send_header('Cache-Control', 'no-store' if p.startswith('/api/') or p.endswith('.html') or p == '/' else 'max-age=86400')
        super().end_headers()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ROUTES:
            try:
                data, stale = ROUTES[u.path](urllib.parse.parse_qs(u.query))
                ctype = 'text/plain; charset=utf-8' if u.path == '/api/sats' else 'application/json; charset=utf-8'
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('X-Stale', '1' if stale else '0')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                body = json.dumps({'error': str(e)}, ensure_ascii=False).encode()
                self.send_response(502)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return
        if u.path.startswith('/.cache') or u.path.endswith('.py') or u.path.endswith('.bat'):
            self.send_error(404)
            return
        super().do_GET()


def main():
    port = int(os.environ.get('PORT') or 8780)
    if '--port' in sys.argv and not os.environ.get('PORT'):
        port = int(sys.argv[sys.argv.index('--port') + 1])
    url = f'http://127.0.0.1:{port}/'
    try:
        srv = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    except OSError:
        print(f'이미 실행 중입니다 → {url}')
        if '--open' in sys.argv:
            webbrowser.open(url)
        return
    print(f'지구 실시간 보기 서버 시작: {url}  (이 창을 닫으면 꺼집니다)', flush=True)
    if '--open' in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    srv.serve_forever()


if __name__ == '__main__':
    main()
