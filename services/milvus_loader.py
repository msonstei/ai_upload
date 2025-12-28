from os import environ
from llama_index.readers.file import MarkdownReader
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import MilvusClient
MILVUS_URI = "http://du-webui:19530"
# Set your OpenAI API key as an environment variable
# environ["OPENAI_API_KEY"] = "sk-******" 
def milvus_loader(file_directory,db_name):
    # 1. Load the markdown files from a directory
    loader = SimpleDirectoryReader(input_dir=file_directory, file_extractor={".md": MarkdownReader()})
    documents = loader.load_data()

    # 2. Connect to Milvus (e.g., Milvus Lite or a Milvus server)
    # For Milvus Lite (local file storage):
    #client = MilvusClient(uri="./milvus_demo.db") 
    # For a Milvus server:
    """
    client = MilvusClient(
    uri="http://du-webui:19530",
    token="root:Milvus",
    db_name="default",
    ) 
    """
    try:
        client = MilvusClient(uri=MILVUS_URI)
        print("Successfully connected to Milvus standalone server.")
        
        # You can now use the client to perform operations
        # Example: print all existing collections
        print(client.list_databases()) 
        # 3. Use LlamaIndex to create an index and store embeddings in Milvus
        vector_store = MilvusVectorStore(milvus_client=client, collection_name="default") #MilvusClient(uri=MILVUS_URI), collection_name="default")
        index = VectorStoreIndex.from_documents(
            documents,
            vector_store=vector_store,
        )

        print(f"Successfully loaded {len(documents)} documents into Milvus collection '{db_name}.")
        print(index)


    except Exception as e:
        print(f"Failed to connect to Milvus: {e}")



