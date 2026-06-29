import json
import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})

login = s.post(
    'https://sso-api.trendagent.ru/v1/login',
    json={'phone': '+79650412059', 'password': 'N7FXpa6'},
    timeout=30,
).json()
token = login['auth_token']
city_id = login['user']['agency']['city']['_id']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

# search block by name
name = 'Аструм'
r = s.get(f'{base}/apartments/search', headers=headers, params={'query': name, 'city': city_id}, timeout=30)
print('search status', r.status_code)
search = r.json()
open('data/search_astrum.json', 'w', encoding='utf-8').write(json.dumps(search, ensure_ascii=False, indent=2)[:50000])

items = (search.get('data') or {}).get('list') or []
print('items', len(items))
if items:
    block = items[0]
    print('first keys', list(block.keys())[:30])
    block_id = block.get('_id') or block.get('id')
    print('block_id', block_id, 'name', block.get('name'))

    # try detail endpoints
    detail_paths = [
        f'/blocks/{block_id}',
        f'/block/{block_id}',
        f'/blocks/{block_id}/',
        f'/apartments/block/{block_id}',
        f'/apartments/blocks/{block_id}',
        f'/apartments?block_id={block_id}',
    ]
    for path in detail_paths:
        url = base + path.split('?')[0]
        params = {}
        if '?' in path:
            params = dict(x.split('=') for x in path.split('?')[1].split('&'))
        r2 = s.get(url, headers=headers, params={**params, 'city': city_id}, timeout=20)
        if r2.status_code == 200:
            print('DETAIL', path, r2.text[:400])
            open(f'data/detail_{path.replace("/","_")}.json', 'w', encoding='utf-8').write(r2.text[:100000])

    # apartments list for block
    apt_paths = [
        f'/apartments/search?block_id={block_id}',
        f'/apartments/search?block={block_id}',
        f'/apartments?block_id={block_id}',
        f'/blocks/{block_id}/apartments',
        f'/blocks/{block_id}/units',
    ]
    for path in apt_paths:
        url = base + path.split('?')[0]
        params = {'city': city_id}
        if '?' in path:
            params.update(dict(x.split('=') for x in path.split('?')[1].split('&')))
        r3 = s.get(url, headers=headers, params=params, timeout=20)
        if r3.status_code == 200 and 'apartment' in r3.text.lower():
            data = r3.json()
            lst = data.get('data', {})
            if isinstance(lst, dict):
                lst = lst.get('list') or lst.get('apartments') or []
            print('APT', path, 'count', len(lst) if isinstance(lst, list) else type(lst))
            open(f'data/apts_{block_id[:8]}.json', 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False)[:200000])
