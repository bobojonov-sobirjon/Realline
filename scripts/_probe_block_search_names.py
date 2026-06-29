import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})

login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': '+79650412059', 'password': 'N7FXpa6'}, timeout=30).json()
token = login['auth_token']
spb_city = login['user']['agency']['city']['_id']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

# Moscow city id (common TA id)
MSK_CITY = '58c665588b6aa52311afa01a'

for city_id, label in [(spb_city, 'spb'), (MSK_CITY, 'msk')]:
    for q in ['Аструм', 'ELEMENT', 'СТОУН', 'Симоновский Вал']:
        for key in ['text', 'query', 'name', 'block_name', 'search_text']:
            params = {'city': city_id, 'show_type': 'list', 'count': 10, 'offset': 0, key: q}
            r = s.get(f'{base}/blocks/search', headers=headers, params=params, timeout=30)
            if r.ok:
                lst = (r.json().get('data') or {}).get('list') or []
                if lst:
                    print(label, key, q, '->', [(x.get('name'), x.get('id')) for x in lst[:3]])
