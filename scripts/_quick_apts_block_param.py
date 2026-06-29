# -*- coding: utf-8 -*-
import os
import requests

phone = os.environ.get('TRENDAGENT_PHONE', '+79650412059')
password = os.environ.get('TRENDAGENT_PASSWORD', 'N7FXpa6')
s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})
login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=60).json()
token = login['auth_token']
city = '58c665588b6aa52311afa01b'
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'
block_id = '5fbbc8b7a4336b0008df6fda'

all_items = []
offset = 0
while True:
    r = s.get(f'{base}/apartments/search', headers=headers, params={
        'city': city, 'block': block_id, 'count': 50, 'offset': offset,
    }, timeout=60)
    d = r.json().get('data') or {}
    lst = d.get('list') or []
    all_items.extend(lst)
    print('offset', offset, 'page', len(lst), 'total', len(all_items), 'apartmentsCount', d.get('apartmentsCount'))
    if len(lst) < 50:
        break
    offset += 50

blocks = {x.get('block_name') for x in all_items}
print('unique block names:', blocks)
print('done', len(all_items))
