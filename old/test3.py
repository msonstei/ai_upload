import requests
import json
import os
import io
key=os.getenv('OPEN_API')
knowledge_id='092f9730-5aa0-48d1-90eb-8b85fc81537a'
address = 'http://du-webui/api/v1'
knowledge = 'Stainless Steel'

def get_knowledge(token, knowledge):
    id = 0
    knowledge_id = 0
    knowledge_bases = {}
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': f'application/json',
        }
    url = f"{address}/knowledge/list"
    print(f"Trying {url} {headers}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        knowledge_bases = response.json()

        print("Knowledge Bases and their IDs:")
        for kb in knowledge_bases:
            print(f"* Name: {kb.get('name')}, ID: {kb.get('id')}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from the response.")

    for item in knowledge_bases:
        if item.get("name") == knowledge:
            knowledge_id = item.get("id")
            break # Exit the loop once the ID is found

    if knowledge_id is not None:
            print(f"The ID for '{knowledge}' is: {knowledge_id}")
            return knowledge_id
    else:
        print(f"No ID found for '{knowledge}'.")


def upload(token, id, file_name,knowledge):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type':'application/json'
    }

    print(f"Loading using: id: {id} for filename: {file_name} to: {knowledge}")
    add_to_kb_url = f'{address}/knowledge/{knowledge}/file/add'
#    headers = {
#        'Authorization': f'Bearer {token}',
#        'Content-Type': f'application/json',
#    }
    data = {'file_id': f'{id}',}
    kb_response = requests.post(add_to_kb_url, headers=headers, data=data)
    kb_response.raise_for_status()

    print((url, headers, data))
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    return response

def upload_file(token, file_path,knowledge_id):
    id = 0
    file_name=''
    files={}
    url = f'{address}/files/'
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    """
    try:
        with open(file_path, 'rb') as f:
            files = f.read()
        #return files
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    """

    with open(file_path, 'rb') as pdf_file:
        # 2. Create the 'files' dictionary in the correct format
        # The key 'file' is the name of the form field expected by the server
        files = {'file': (file_path, pdf_file, 'application/pdf')}
    print(type(files))
    print(files)
    #files = {'file': open(file_path, file_handle)}
    response = requests.post(url, headers=headers, data=files)
    if response.status_code == 200:
        print('\n')
        print('File embedding complete')
        # Step 3: Load the JSON response into a Python object (e.g., a dictionary)
        data = response.json()

        # You can now work with the data as a standard Python dictionary/list
        print(f'\n')
        print(type(data))
        # Example access:
        # get document id (data['id'])
        id = data['id']
        file_name = data['filename']
        response = upload(token, id, file_name, knowledge_id)
        if response.status_code == 200:
            return response.json()
        else:
            return(f'upload_file File Error: {response.status_code}')

    else:
        return(f'upload_file2 Error: {response.status_code}')

def main():
   token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjMxMzlhMjVhLWIwMzYtNDk0ZS1iYmQzLTlhN2Q1MDRhYmRjNiIsImV4cCI6MTc2NzkxMTkwNiwianRpIjoiNTNhYWZiOWUtZGI5NC00NjI0LTgxMzQtYWMxMTY5Yzg0YTk2In0.MSeYb4hbO8VA4_o_VGH6jHWrA-gQgcFl3kFShTk1FRQ' #key
   file='pdf/Contract.pdf'
   knowledge_id = get_knowledge(token,knowledge)
   response = upload_file(token, file,knowledge_id)
   #response = chat_with_model(token)
   print(response)

if __name__=='__main__':
   main()
