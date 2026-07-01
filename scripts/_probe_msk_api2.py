# -*- coding: utf-8 -*-
import json
import os
import requests

phone = os.environ.get('TRENDAGENT_PHONE', '+79650412059')
password = os.environ.get('TRENDAGENT_PASSWORD', 'N7FXpa6')

for origin in ['https://msk.trendagent.ru', 'https://spb.trendagent.ru']:
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': origin,
        'Referer': f'{origin}/',
    })
    login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=60).json()
    h = {**s.headers, 'Authorization': 'Bearer ' + login['auth_token']}
    user = login['user']
    print('origin', origin, 'agency', user['agency'].get('name'), 'city', user['agency']['city'].get('name'))
    base = 'https://api.trendagent.ru/v4_29'
    msk = '58c665588b6aa52311afa01a'
    for params in [
        {'city': msk, 'show_type': 'map'},
        {'city': msk, 'show_type': 'list', 'count': 5, 'offset': 0},
        {'city': msk, 'query': 'СТОУН'},
        {'city': msk, 'text': 'Симоновский'},
    ]:
        r = s.get(base + '/blocks/search', headers=h, params=params, timeout=60)
        key = list(params.keys())
        print(' ', params, '->', r.status_code, end='')
        if r.ok:
            d = r.json().get('data') or {}
            res = d.get('results') or d.get('list') or []
            print(' n=', len(res) if isinstance(res, list) else type(res))
        else:
            print(' ', r.text[:80])
