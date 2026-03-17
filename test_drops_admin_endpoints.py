import requests

base = 'http://127.0.0.1:8000/api/v1'

# Login admin
r = requests.post(base + '/auth/login/', json={'email': 'admin@weforeverdrip.com', 'password': 'admin123'})
print('login', r.status_code, r.json())
if r.status_code != 200:
    raise SystemExit('Login failed')
token = r.json().get('access')
headers = {'Authorization': f'Bearer {token}'}

# Create drop
payload = {
    'name': 'Test Drop',
    'description': 'Test',
    'status': 'draft',
    'launch_date': '2030-12-01T12:00:00Z',
    'is_published': False,
}
r = requests.post(base + '/drops/', json=payload, headers=headers)
print('create drop', r.status_code, r.json())

# Add product to drop (product_id 1 maybe exists)
r = requests.post(base + '/drops/test-drop/products/', json={'product_id': 1, 'drop_price': 900000, 'quantity_limit': 20}, headers=headers)
print('add product', r.status_code, r.text)

# Activate drop
r = requests.post(base + '/drops/test-drop/activate/', headers=headers)
print('activate', r.status_code, r.json())

# Remove product
r = requests.delete(base + '/drops/test-drop/products/1/', headers=headers)
print('remove product', r.status_code)
