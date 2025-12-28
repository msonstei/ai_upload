import os
import requests
import glob
import logging
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
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
#OPENWEBUI_API_KEY = 'sk-1057d0440957486787b65ce7d72bd612'
OPENWEBUI_KNOWLEDGE_ID = 'b9805f64-1f9a-4146-af55-a488c89563dd' # General Knowledge
OPEN_ENDPOINT= 'http://du-webui/api/v1/files/'
KNOWLEDGE_ENDPOINT = f'http://du-webui/api/v1/knowledge/{OPENWEBUI_KNOWLEDGE_ID}/file/add'

test_file = '/media/projects/C101017_Temp_EDS_Svc_Birch_Hill_Tank_Farm/Planning/Billing/Signed Billing Report.md'

# Set the directory to read
#directory_path = '/home/marks/docling/input/transfer/' #'/media/projects'
directory_path = '/home/webui/Desktop/Close_out/'
OUTPUT_DIR = '/home/marks/docling/output'
LOG_FILE = '/home/marks/docling/logs/upload.log'
# Define the allowed file extensions
ALLOWED_FILE_TYPES = ['.docx','.xlsx','.pptx','.md','.csv','.pdf']

def configure_logging(verbose: bool) -> None:
    """Set up a simple console logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        filename= LOG_FILE,
        filemadoe='a',
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%H:%M:%S",
    )

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

def get_embeddings(text_list):
    # e.g., using SentenceTransformers or OpenAI
    return [[0.1] * 768 for _ in text_list] 

def doc_converter(source):
    # Function to split data into chunks
    converter = DocumentConverter()
    chunker = HierarchicalChunker()

    source = "https://milvus.io/docs/overview.md"
    doc = converter.convert(source).document

    texts = [chunk.text for chunk in chunker.chunk(doc)]

    for i, text in enumerate(texts[:5]):
        print(f"Chunk {i+1}:\n{text}\n{'-'*50}")

def upload_to_milvus(file_path, file_name, json_markdown):
    logging.info(f"Milvus uploading {full_path},{file_name}")
    
    # Create the Milvus API request data
    #texts = open(file_path, 'rb').read()

    headers={
            'Authorization': f'Bearer {MILVUS_API_KEY}',
            'Content-Type': 'application/json'
        }
    """
    data=json.dumps({
            'markdown': markdown
        })
   
    #vectors = get_embeddings(texts)

    # Format data as a list of dictionaries
    data = [
        {
            "id": i,
            "vector": vectors[i],
            "text": texts[i],
            "metadata": {"source": "docling_conversion"}
        }
        for i in range(len(texts))
    ]

    # Insert into Milvus
    client.insert(collection_name=collection_name, data=data)
    """
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
    
    #return ml.milvus_loader(OUTPUT_DIR, file_name)

def find_files(directory_path):
    # Returns the files that will be processed.
    # Excludes files not listed in  ALLOWED_FILE_TYPES
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
        print(f"An error occurred uploading knowledge {e}")
        return 'fail'

def upload_file(token, file_path, api_url, file_name):
    headers = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
        'Content-Type': 'multipart/form-data',
    }

    params = {
        'process': 'true',
        'process_in_background': 'true',
    }
    """
    files = {
        'file': f'@{file_path}{file_name}'
        'file': open(f'{file_path}/{file_name}', 'rb'),
        #'file': (file_path, open(file_name, 'rb'), 'text/markdown'),
        'metadata': (None, '{"additionalProp1":{}}'),
    }
    """

    # Open the file in binary read mode
    print(f"Uploading {file_path}")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(api_url, headers=headers, files=files)
 
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except Exception as e:
        #logging.DEBUG(f"Open-WebUI returned uploading file")
        print(f"An error occurred: during upload_file {e}")
        return None

def check_file(file_id,token):
    # function to check the status of file being processed.
    # repeated call until it returns 'complete' status
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

def check_file_exists(token, api_url, file_name):
    # Function to check if a file already exists
    # called before uploading file
    headers = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
    }
        
    params = {
        'filename': file_name,
        'content': 'true',
    }
    # Get list of uploaded files
    try:
        response = requests.post(f'{api_url}/search', headers=headers, params=params)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except Exception as e:
        #logging.DEBUG(f"Open-WebUI returned uploading file")
        print(f"An error occurred: during upload_file {e}")
        return None

def get_kname(directory_path):
    # Get the directory name and return it to be used as the knowledge name
    dirs = dir.list_directories_os(directory_path)
    print(dirs)
    return dirs

def create_knowledge(kname, token):
    # Use the directory name {kname} as the knowledge name
    # Create teh new knowledge container
    result = {}
    data = {
    "name": kname,
    "description": kname,
    "access_control": {
    "additionalProp1": {}
     }
    }

    headers = {
    'Authorization': f'Bearer {token}',
    'accept': 'application/json',
    'Content-Type': 'application/json',
    }
    data_list = []
    try:
        url = f"http://du-webui/api/v1/knowledge/"
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f"Exception connecting to knowledge lookup: {e}")

        # Parse the JSON response into a Python list of dictionaries
        if response.status_code == 200:
            json_data = response.json()
            data_list = [
                {"id": item["id"], "name": item["name"]} 
                for item in json_data["items"]
            ]
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
        # Create a list comprehension to extract all 'name' values
        all_names = [item['name'] for item in data_list]
        if kname in all_names:
            for item in data_list:
                if item.get('name') == kname:
                    target_id = item.get('id')
                    return {'name':kname,'id':target_id}
        # If collection name doesn't exist create it
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
                #logging.DEBUG(f"Open-WebUI Knowledge returned {e}")
                print(f"An error occurred uploading knowledge: {e}")
                return response.raise_for_status()
    except Exception as e:
        print(f"Error looking up knowledge name: {e}")
        return 1

def count_files_pathlib(directory_path):
  """Count all files recursively in a directory using pathlib."""
  # Use rglob('*') to find all files and directories recursively
  # Filter only for files using a list comprehension or generator expression
  count = len([file for file in Path(directory_path).rglob('*') if file.is_file()])
  return count

def upload_files(token, file_path, url, file_name):
    headers = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
        #'Content-Type': 'multipart/form-data',
    }

    params = {
        'process': 'true',
        'process_in_background': 'true',
    }    
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, 'application/octet-stream')}
        response = requests.post(url,params=params, headers=headers, files=files)
        
    return response.json()


if __name__ == '__main__':
    # Start logging service
    configure_logging(True)
    # initialize the variables
    file_id = ''
    response = {'status':'NULL'}
    # Create Knowledge Space
    kname = get_kname(directory_path)
    kname = create_knowledge(kname,OPENWEBUI_API_KEY)
    if kname == 1:
        logging.fatal("Irrecoverable error creating knowledge")
        print(f"Irrecoverable error in creating knowledge. Check log file {LOG_FILE} for details. Exiting application")
        os._exit
    # Assign the returned knowledge id to k_id variable
    k_id = kname['id']
    logging.info(f"Will add files to knowledge container {k_id}")
    print(f"Will add files to knowledge container {k_id}")
    # Set ne knowledge collection id, use Temp collection if new collection not created
    if k_id:
        KNOWLEDGE_ENDPOINT = f'http://du-webui/api/v1/knowledge/{k_id}/file/add'

    # Count the number of files to be processed, and print for user info
    files = find_files(directory_path)
    count = count_files_pathlib(directory_path)
    print(f"Preparing to upload {count} files.")
    #logging.INFO(f"Preparing to upload {str(count)} files.")

    # Process every file in the repository
    full_path = f"{directory_path}{kname['name']}/"
    for file in files:
        file_name=Path(file).name
        new_path = Path(file).parent
        full_path = f"{new_path}{kname['name']}/"
        good_path = f"{new_path}/{file_name}"
        logging.info(f"Processing: {full_path} \n {file_name}")
        # Docling process the file into MARKDOWN
        # returns original file path, markdown data, and filename(to be used to name the file in collection)
        #full_path, markdown, file_name = ds.get_docling_data(file, OUTPUT_DIR)
        #file_id = upload_to_milvus(full_path, file_name, json_markdown)
        #print(f"Milvus returns {file_id}")
        exists = check_file_exists(OPENWEBUI_API_KEY, OPEN_ENDPOINT, file_name)
        if exists['detail'] == 'No files found matching the patern':
            file_id = upload_files(OPENWEBUI_API_KEY, f'{new_path}/{file_name}', OPEN_ENDPOINT, file_name)
            print(file_id)
        else:
            print(f"File {file_name} already exists, skipping upload")
            continue
        #file_id = upload_file(OPENWEBUI_API_KEY, good_path, OPEN_ENDPOINT, file_name) #upload_to_milvus(full_path, markdown)
        a_id = file_id['id']
        response['status'] = 'incomplete'
        while response['status'] !='completed' or response['status'] !='failed':
            response = check_file(a_id,OPENWEBUI_API_KEY)
            time.sleep(5.0)
        time.sleep(1.0)
        if response['status'] =='completed':
            print("****************************File Uploaded with ID*******************************************")
            print(f"Returned: {file_id['id'],file_id['filename'],file_id['meta']['size']}")
            logging.info(f"Returned: {file_id['id'],file_id['filename'],file_id['meta']['size']}")
            #final = upload_knowledge(file_id['id'],file_id['filename'],file_id['meta']['size'],KNOWLEDGE_ENDPOINT,OPENWEBUI_API_KEY)
            print("*****************************Send to Knowledge******************************************")
            final = upload_knowledge(a_id,file_name,file_id['meta']['size'],KNOWLEDGE_ENDPOINT,OPENWEBUI_API_KEY)
            print("*****************************Returned from Knowledge******************************************")
            print(final)
            if final == 'fail':
                print(f"Error saving file {file_id['filename']} to knowledge base")
            else:
                pass
            
