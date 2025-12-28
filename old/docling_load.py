import os
import requests
import glob
import logging
from docling.document_converter import DocumentConverter
from pathlib import Path
import json
import time

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
OPENWEBUI_API_KEY = 'sk-f1287dd823de48719bbd29df55d0c5d3'
OPENWEBUI_KNOWLEDGE_ID = '092f9730-5aa0-48d1-90eb-8b85fc81537a'
OPEN_ENDPOINT= 'http://du-webui/api/v1/files/'
KNOWLEDGE_ENDPOINT = f'http://du-webui/api/v1/knowledge/{OPENWEBUI_KNOWLEDGE_ID}/file/add'

test_file = '/media/projects/C101017_Temp_EDS_Svc_Birch_Hill_Tank_Farm/Planning/Billing/Signed Billing Report.md'

# Set the directory to read
directory_path = '/media/projects'

# Define the allowed file extensions
ALLOWED_FILE_TYPES = ['.doc','.docx','.xlsx','.pptx','.xls','.ppt','.md','.html','.xhtml','.csv','.png','.jpeg','.tiff','.bmp',
                      '.webp','.wav','.mp3','.pdf', '.jpg']

def configure_logging(verbose: bool) -> None:
    """Set up a simple console logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%H:%M:%S",
    )

def get_docling_data(file_path):

    # Convert the document
    try:
        result = converter.convert(file_path)
        print(f"Document processed successfully from: {file_path}")
        output_path = os.path.dirname(file_path)
        markdown_output = Path(file_path).stem
        file_name = Path(file_path).name
        logging.info(f"Output Path: {output_path}")
        markdown_output = f"{markdown_output}.md"
        logging.info(f"Output file: {output_path}")
        full_path = f'{output_path}/{markdown_output}'
        logging.info(f"Save file: {full_path}")
        markdown_content = result.document.export_to_markdown()
        # Export the result to a structured format, e.g., JSON or Markdown
        # result_dict = result.document.export_to_dict()
        # print(json.dumps(result_dict, indent=2))
        # 5. Save the output to a local file
        try:
            logging.info(f"Saving file to {markdown_output}")
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                logging.info(f"Uploading {full_path}")
            logging.info(f"Conversion successful")
            return full_path, markdown_content, file_name
        except Exception as e:
            print (f"Error saving file: {e}")




    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")


def upload_to_milvus(file_path, markdown):
    logging.info(f"Milvus uploading {full_path}")
    # Create the Milvus API request data
    request_data = {
        'file': open(file_path, 'rb').read(),
        'knowledge_id': OPENWEBUI_KNOWLEDGE_ID
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
        response = requests.post(f'{MILVUS_ENDPOINT}/api/v2/upload', headers=headers,data=data , files=request_data)

        # Get the uploaded file ID from Milvus API response
        file_id = response.json()["id"]
        logging.info(f"Milvus returned {file_id}")
        return file_id
    except Exception as e:
        print(f"Error in Milvus {e}")
        #os._exit

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
    #print(f"Sending to: {url} with {json_data}")
    try:
        response = requests.post(url,headers=headers,json=json_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred uploading knowledge")
        return 'fail'

def upload_file(token, file_path, api_url, file_name):
    """
    Uploads a file to the Open WebUI instance via API.

    Args:
        token (str): Your Open WebUI API key.
        file_path (str): The local path to the file you want to upload.
        api_url (str): The URL of the file upload API endpoint.

    Returns:
        dict: The JSON response from the API.
    """
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
        logging.DEBUG(f"Open-WebUI returned {e}")
        print(f"An error occurred: {e}")
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

if __name__ == '__main__':
    configure_logging(True)
    response = {'status':'NULL'}
    #for file in find_files(directory_path):
        #full_path,markdown, file_name = get_docling_data(file)
        #file_id = upload_file(OPENWEBUI_API_KEY, full_path, OPEN_ENDPOINT, file_name) #upload_to_milvus(full_path, markdown)
    file_id = upload_file(OPENWEBUI_API_KEY, test_file, OPEN_ENDPOINT, 'Signed Billing Report.pdf')
    a_id = file_id['id']
    while response['status'] !='completed':
        response = check_file(a_id,OPENWEBUI_API_KEY)
        time.sleep(1.0)
    time.sleep(1.0) 
    #print(f"Returned: {file_id['id'],file_id['filename'],file_id['meta']['size']}")
    final = upload_knowledge(file_id['id'],file_id['filename'],file_id['meta']['size'],KNOWLEDGE_ENDPOINT,OPENWEBUI_API_KEY)
    #print(final)
    if final == 'fail':
        print(f"Error saving file {file_id['filename']} to knowledge base")
    else:
       pass
