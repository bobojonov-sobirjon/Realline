import json
import re
import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})

phone = '+79650412059'
password = 'N7FXpa6'

login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=30)
data = login.json()
token = data['auth_token']
city_id = data['user']['agency']['city']['_id']
print('city_id', city_id, data['user']['agency']['city']['name'])

# headers used by portal (from config.js patterns)
header_sets = [
    {'Authorization': f'Bearer {token}'},
    {'auth-token': token},
    {'Auth-Token': token},
    {'Authorization': token},
    {'x-auth-token': token},
]

bases = {
    'apartment': 'https://apartment-api.trendagent.ru',
    'house': 'https://house-api.trendagent.ru',
    'api': 'https://api.trendagent.ru/v4_29',
}

paths = [
    '/blocks',
    '/blocks/search',
    '/search/blocks',
    '/v1/blocks',
    '/v2/blocks',
    '/v1/blocks/search',
    '/v2/blocks/search',
    '/apartments',
    '/apartments/search',
    '/search',
    '/v1/search',
    '/complexes',
    '/estates',
]

for hname, headers in [('Bearer', header_sets[0]), ('auth-token', header_sets[1])]:
    print('\n===', hname, '===')
    h = {**s.headers, **headers, 'city': city_id}
    for bname, base in bases.items():
        for path in paths:
            url = base + path
            for params in [
                {},
                {'city': city_id},
                {'city_id': city_id},
                {'query': 'Аструм'},
                {'name': 'Аструм'},
                {'text': 'Аструм'},
                {'limit': 3},
            ]:
                try:
                    r = s.get(url, headers=h, params=params, timeout=15)
                    if r.status_code == 200 and r.text and r.text[0] in '{[':
                        print('OK', bname, path, params, r.text[:250])
                        break
                except Exception:
                    pass

# grep config for endpoint strings
cfg = open('data/spb_config.js', encoding='utf-8').read()
for m in sorted(set(re.findall(r'apartment-api[^\"\']+|house-api[^\"\']+|/blocks[^\"\']{0,40}', cfg))):
    print('cfg', m[:100])
