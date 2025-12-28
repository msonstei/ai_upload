import os
import requests
import glob
import logging
from docling.document_converter import DocumentConverter
from pathlib import Path
import json
import time
#from services.docling_service import get_docling_data as ds
from services import docling_service as ds
from services import dir
from services import milvus_loader as ml
# Define the path to your local file
# Example with a PDF file
#file_path = "my-local-document.pdf"
# Or use pathlib for better path management:
# file_path = Path("./my-folder/my-local-document.pdf")

# Instantiate the converter (models will download the first time you run this)
converter = DocumentConverter()

# Replace with your own Docling API endpoint and key
DOCLING_ENDPOINT = 'http://du-webui:5001/'
DOCLING_API_KEY = ''

# Replace with your own Milvus API endpoint, key, and Open-WebUI Knowledge ID
MILVUS_ENDPOINT = 'http://du-webui:19530/'
MILVUS_API_KEY = ''
OPENWEBUI_API_KEY = 'sk-f1287dd823de48719bbd29df55d0c5d3'
OPENWEBUI_KNOWLEDGE_ID = 'b9805f64-1f9a-4146-af55-a488c89563dd' # General Knowledge
OPEN_ENDPOINT= 'http://du-webui/api/v1/files/'
KNOWLEDGE_ENDPOINT = f'http://du-webui/api/v1/knowledge/{OPENWEBUI_KNOWLEDGE_ID}/file/add'

test_file = '/media/projects/C101017_Temp_EDS_Svc_Birch_Hill_Tank_Farm/Planning/Billing/Signed Billing Report.md'

# Set the directory to read
directory_path = '/home/webui/Desktop/Close_out' #'/home/marks/docling/input/transfer/' #'/media/projects'
OUTPUT_DIR = '/home/marks/docling/output'
# Define the allowed file extensions
ALLOWED_FILE_TYPES = ['.docx','.xlsx','.pptx','.xls','.ppt','.md','.html','.xhtml','.csv','.png','.jpeg','.tiff','.bmp','.pdf', '.jpg']

def configure_logging(verbose: bool) -> None:
    """Set up a simple console logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%H:%M:%S",
    )

def upload_to_milvus(file_path, file_name): #markdown):
    logging.info(f"Milvus uploading {full_path}")
    
    # Create the Milvus API request data
    request_data = {
        'file': open(file_path, 'rb').read(),
        #'knowledge_id': OPENWEBUI_KNOWLEDGE_ID
    }

    headers={
            'Authorization': f'Bearer {MILVUS_API_KEY}',
            'Content-Type': 'application/json'
        }

    data=json.dumps({
            'markdown': markdown
        })

    # Send the file and its markdown to Milvus API
    try:
        response = requests.post(f'{MILVUS_ENDPOINT}/api/v2/upload', headers=headers, files=request_data) #data=data , files=request_data)

        # Get the uploaded file ID from Milvus API response
        file_id = response.json()["id"]
        logging.info(f"Milvus returned {file_id}")
        return file_id
    except Exception as e:
        print(f"Error in Milvus {e}")
        #os._exit
    
    # return ml.milvus_loader(OUTPUT_DIR, file_name)

def find_files(directory_path):
    for file in glob.glob(os.path.join(directory_path, '**', '*'), recursive=True):
        if os.path.isfile(file) and os.path.splitext(file)[1].lower() in ALLOWED_FILE_TYPES:
            yield file


def upload_knowledge(file_id,file_name,file_size,url,token):
    headers = {
    'Authorization': f'Bearer {token}',
    'accept': 'application/json',
    'Content-Type': 'application/json',
    }

    json_data = {'file_id': file_id,}
    print(f"Sending to: {url} with {json_data}")
    try:
        response = requests.post(url,headers=headers,json=json_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred uploading knowledge")
        return 'fail'

def upload_file(token, file_path, api_url, file_name):
    headers = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
    }

    params = {
        'process': 'true',
        'process_in_background': 'true',
    }

    files = {
        'file': (file_name, open(file_path, 'rb'), 'text/markdown'),
        'metadata': (None, '{"additionalProp1":{}}'),
    }

    # Open the file in binary read mode
    try:
        response = requests.post('http://du-webui/api/v1/files/', params=params, headers=headers, files=files)

        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.DEBUG(f"Open-WebUI returned uploading file")
        print(f"An error occurred: during upload_file")
        return None

def check_file(file_id,token):
    data = {}
    headers = {
    'Authorization': f'Bearer {token}',
    'accept': 'application/json',
    'Content-Type': 'application/json',
    }
    params = {'stream':'false'}
    url = f"http://du-webui/api/v1/files/{file_id}/process/status"
    #print(f"Sending to: {url} with {params}.")
    try:
        response = requests.get(url,headers=headers,params=params)
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"File check bad response {response.status_code}")
        print(f"Response is: {data['status']}")
        response.raise_for_status() # Raise an exception for bad status codes
        return data
    except requests.exceptions.RequestException as e:
        logging.DEBUG(f"Open-WebUI Knowledge returned {e}")
        print(f"An error occurred uploading knowledge: {e}")
        return response.raise_for_status()

def get_kname(directory_path):
    # Get the directory name and return it to be used as the knowledge name
    return dir.list_directories_os(directory_path)

def create_knowledge(kname, token):
    # Use the directory name {kname} as the knowledge name
    # Create teh new knowledge container
    result = {}
    data = {
    "name": kname,
    "description": kname,
    }

    headers = {
    'Authorization': f'Bearer {token}',
    'accept': 'application/json',
    'Content-Type': 'application/json',
    }
    try:
        url = f"http://du-webui/api/v1/knowledge/list"
        response = requests.get(url, headers=headers)
        # Parse the JSON response into a Python list of dictionaries
        data_list = response.json() 

        # Create a list comprehension to extract all 'name' values
        all_names = [item['name'] for item in data_list]

        print("All names:", all_names)
        if kname in all_names:
            for item in data_list:
                if item.get('name') == kname:
                    target_id = item.get('id')
                    return {'name':kname,'id':target_id}
        else:
            url = f"http://du-webui/api/v1/knowledge/create"
            print(f"{kname} does not exist, Sending to: {url} with {headers},{data}.")
            try:
                response = requests.post(url,headers=headers,json=data)
                if response.status_code == 200:
                    result = response.json()
                else:
                    print(f"Knowledge create bad response {response.status_code}")
                print(f"Response is: {result['id']}")
                response.raise_for_status() # Raise an exception for bad status codes
                return result
            except requests.exceptions.RequestException as e:
                logging.DEBUG(f"Open-WebUI Knowledge returned {e}")
                print(f"An error occurred uploading knowledge: {e}")
                return response.raise_for_status()
    except:
        print("Errot looking up knowledge name")
        return 

def count_files_pathlib(directory_path):
  """Counts all files recursively in a directory using pathlib."""
  # Use rglob('*') to find all files and directories recursively
  # Filter only for files using a list comprehension or generator expression
  count = len([file for file in Path(directory_path).rglob('*') if file.is_file()])
  return count


if __name__ == '__main__':
    # Start logging service
    configure_logging(True)
    response = {'status':'NULL'}

    # Create Knowledge Space
    kname = get_kname(directory_path)
    kname = create_knowledge(kname,OPENWEBUI_API_KEY)
    print(kname)
    k_id = kname['id']
    print(f"Will add files to knowledge container {k_id}")
    # Set ne knowledge collection id, use Temp collection if new collection not created
    if k_id:
       KNOWLEDGE_ENDPOINT = k_id

    # Count the number of files to be processed, and print for user info
    files = find_files(directory_path) 
    count = count_files_pathlib(directory_path)
    print(f"Preparing to upload {count} files.")
    #logging.INFO(f"Preparing to upload {str(count)} files.")

    # Process every file in the repository
    for file in files:
        # Docling process the file into MARKDOWN
        # returns original file path, markdown data, and filename(to be used to name the file in collection)
        full_path, markdown, file_name = ds.get_docling_data(file, OUTPUT_DIR)
        file_id = upload_to_milvus(full_path, file_name) #markdown)
        print(f"Milvus returns {file_id}")
        #file_id = upload_file(OPENWEBUI_API_KEY, full_path, OPEN_ENDPOINT, file_name) #upload_to_milvus(full_path, markdown)
        a_id = file_id['id']
        #while response['status'] !='completed':
        #    response = check_file(a_id,OPENWEBUI_API_KEY)
        #    time.sleep(1.0)
        time.sleep(1.0)
        #print(f"Returned: {file_id['id'],file_id['filename'],file_id['meta']['size']}")
        #final = upload_knowledge(file_id['id'],file_id['filename'],file_id['meta']['size'],KNOWLEDGE_ENDPOINT,OPENWEBUI_API_KEY)
        final = upload_knowledge(a_id,file_name,file_id['meta']['size'],KNOWLEDGE_ENDPOINT,OPENWEBUI_API_KEY)
        print(final)
        if final == 'fail':
            print(f"Error saving file {file_id['filename']} to knowledge base")
        else:
            pass
