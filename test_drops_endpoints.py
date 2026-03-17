import requests

base = 'http://127.0.0.1:8000/api/v1/drops'

for path in ['/', '/live/', '/upcoming/', '/ss25-launch-drop/', '/coal-city-pack/']:
    url = base.rstrip('/') + path
    r = requests.get(url, timeout=10)
    print(path, r.status_code)
    try:
        data = r.json()
        if isinstance(data, list):
            print('  length', len(data))
        else:
            print('  keys', list(data.keys()))
            print('  status', data.get('status'), 'countdown', data.get('countdown_seconds'), 'drop_products', len(data.get('drop_products', [])))
    except Exception as e:
        print('  non-json', e)
