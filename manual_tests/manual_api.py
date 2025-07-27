import requests, sys
from typing import Dict, Any

login: requests.Response = requests.post('http://localhost:5000/api/v1/auth/login', json={'username':'manager','password':'manager123'})
print('login',login.status_code, login.text)
if login.ok:
    token=login.json()['access_token']
    print('token', token[:50], '...')
    r: requests.Response = requests.get('http://localhost:5000/api/v1/menu/active', headers={'Authorization': f'Bearer {token}'})
    print('menu', r.status_code)
    print(r.text[:1000])
else:
    sys.exit(1)
