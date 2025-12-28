import requests
import sys
import json
import os
API_URL='http://du-webui/api/v1/auths/signin'
# Ensure the required environment variables are set
#if len(sys.argv) < 2:
#    print("Usage: python3.12 api_login.py <API_URL>")
#    sys.exit(1)

#API_URL = sys.argv[1]
USERNAME = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASS")
print(USERNAME,PASSWORD)
if not USERNAME or not PASSWORD:
    print("Error: API_USER and API_PASS environment variables must be set.")
    sys.exit(1)

headers={'accept':'application/json', 'Content-Type':'application/json'}
data={'email':USERNAME,'password':PASSWORD}
print(data)
try:
    # Example: POST request with username/password for authentication
    response = requests.post(API_URL, headers=headers, data=data)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    
    # Assuming the API returns a JSON with an 'access_token'
    token_data = response.json()
    access_token = token_data.get("access_token")

    if access_token:
        # Print the token to standard output so the shell script can capture it
        print(f"TOKEN:{access_token}")
    else:
        print("Error: Access token not found in the response.")
        sys.exit(1)

except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
    sys.exit(1)
