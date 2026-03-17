import requests

# Quick test
lr = requests.post('http://localhost:8000/api/v1/auth/login/', json={'email': 'admin@weforeverdrip.com', 'password': 'admin123'}, timeout=5)
print(f'Login: {lr.status_code}')

if lr.status_code == 200:
    token = lr.json()['access']
    h = {'Authorization': f'Bearer {token}'}
    
    endpoints = [
        'dashboard/stats', 'dashboard/orders/recent', 'dashboard/low-stock',
        'dashboard/top-products', 'dashboard/order-breakdown', 'dashboard/revenue',
        'orders', 'inventory', 'customers'
    ]
    
    passed = 0
    for ep in endpoints:
        try:
            r = requests.get(f'http://localhost:8000/api/v1/admin/{ep}/', headers=h, timeout=5)
            status = 'PASS' if r.status_code == 200 else f'FAIL {r.status_code}'
            print(f'{ep}: {status}')
            if r.status_code == 200:
                passed += 1
        except Exception as e:
            print(f'{ep}: ERROR {e}')
    
    print(f'\nTotal: {passed}/{len(endpoints)} endpoints working')
    
    # Test 403 rejection
    print('\n--- Testing 403 Rejection for Non-Admin ---')
    try:
        nr = requests.post('http://localhost:8000/api/v1/auth/login/', json={'email': 'testuser@example.com', 'password': 'testpass123'}, timeout=5)
        if nr.status_code == 200:
            user_token = nr.json()['access']
            user_h = {'Authorization': f'Bearer {user_token}'}
            
            fr = requests.get('http://localhost:8000/api/v1/admin/dashboard/stats/', headers=user_h, timeout=5)
            print(f'Non-admin access to dashboard/stats: {fr.status_code}')
            if fr.status_code == 403:
                print('403 Rejection works correctly')
    except Exception as e:
        print(f'Error testing 403: {e}')
