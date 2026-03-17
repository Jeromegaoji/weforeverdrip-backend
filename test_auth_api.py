import json
import requests

BASE_URL = "http://localhost:8000/api/v1/auth"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def print_test(test_name):
    print(f"\n{GREEN}=== {test_name} ==={RESET}")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

# Test 1: Register User
print_test("TEST 1: Register User")
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
test_email = f"test_{timestamp}@weforeverdrip.com"

register_data = {
    "email": test_email,
    "first_name": "Tobe",
    "last_name": "Drip",
    "password": "Wfd2025!",
    "confirm_password": "Wfd2025!"
}

try:
    response = requests.post(f"{BASE_URL}/register/", json=register_data)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 201:
        print_success("User registered successfully")
        print(json.dumps({
            "email": body['user']['email'],
            "first_name": body['user']['first_name'],
            "access_token": body['access'][:20] + "..."
        }, indent=2))
        access_token = body['access']
        refresh_token = body['refresh']
    else:
        print_error(f"Registration failed: {body}")
        exit(1)
except Exception as e:
    print_error(f"Error: {e}")
    exit(1)

# Test 2: Login User
print_test("TEST 2: Login User")
login_data = {
    "email": test_email,
    "password": "Wfd2025!"
}

try:
    response = requests.post(f"{BASE_URL}/login/", json=login_data)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 200:
        print_success("Login successful")
        print(f"User: {body['user']['email']}")
        access_token = body['access']
        refresh_token = body['refresh']
    else:
        print_error(f"Login failed: {body}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 3: Get User Profile
print_test("TEST 3: Get User Profile")
headers = {"Authorization": f"Bearer {access_token}"}

try:
    response = requests.get(f"{BASE_URL}/profile/", headers=headers)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 200:
        print_success("Profile retrieved successfully")
        print(json.dumps({
            "email": body['email'],
            "first_name": body['first_name'],
            "last_name": body['last_name']
        }, indent=2))
    else:
        print_error(f"Profile retrieval failed: {body}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 4: Create Address
print_test("TEST 4: Create Address")
address_data = {
    "street": "12 Independence Layout",
    "city": "Enugu",
    "state": "Enugu State",
    "country": "Nigeria",
    "is_default": True
}

try:
    response = requests.post(f"{BASE_URL}/addresses/", json=address_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 201:
        print_success("Address created successfully")
        print(json.dumps({
            "id": body['id'],
            "street": body['street'],
            "city": body['city'],
            "is_default": body['is_default']
        }, indent=2))
        address_id = body['id']
    else:
        print_error(f"Address creation failed: {body}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 5: Get All Addresses
print_test("TEST 5: Get All Addresses")
try:
    response = requests.get(f"{BASE_URL}/addresses/", headers=headers)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 200:
        print_success(f"Found {len(body)} address(es)")
        for addr in body:
            print(f"  - {addr['street']}, {addr['city']}")
    else:
        print_error(f"Failed to get addresses: {body}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 6: Logout
print_test("TEST 6: Logout User")
logout_data = {"refresh": refresh_token}

try:
    response = requests.post(f"{BASE_URL}/logout/", json=logout_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 200:
        print_success(f"Logout successful: {body['message']}")
    else:
        print_error(f"Logout failed: {body}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 7: Try to use blacklisted refresh token
print_test("TEST 7: Try to Refresh with Blacklisted Token")
refresh_data = {"refresh": refresh_token}

try:
    response = requests.post(f"{BASE_URL}/token/refresh/", json=refresh_data)
    print(f"Status Code: {response.status_code}")
    body = response.json()
    
    if response.status_code == 401:
        print_success("Token properly blacklisted (401 Unauthorized)")
    else:
        print_error(f"Token should have been blacklisted. Status: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

print(f"\n{GREEN}=== ALL TESTS COMPLETED ==={RESET}\n")
