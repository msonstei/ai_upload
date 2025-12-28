import requests
import json

token='sk-f1287dd823de48719bbd29df55d0c5d3'

headers = {
'Authorization': f'Bearer {token}',
'accept': 'application/json',
'Content-Type': 'application/json',
}


url = f"http://du-webui/api/v1/knowledge/list"
response = requests.get(url, headers=headers)
# Parse the JSON response into a Python list of dictionaries
data_list = response.json() 
#print(data_list)
# Create a list comprehension to extract all 'name' values
all_names = [item['name'] for item in data_list]
print("All names:", all_names)

kname='J101730.31.32.33  Bear Paw Phase 2'

if kname in all_names:
    for item in data_list:
        if item.get('name') == kname:
            target_id = item.get('id')
            print(target_id)
