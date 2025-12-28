from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
from pymilvus import MilvusClient
from tqdm import tqdm
from pymilvus import db, connections, MilvusException
from sentence_transformers import SentenceTransformer

# Load a pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')
db_name = "test"

embedding_dim=1536
collection_name='test'
source = 'output/BP Ph2 Spruce St Utilidor Lids JIF 082911.md'

converter = DocumentConverter()
chunker = HierarchicalChunker()

def get_db():
    connections.connect(host="du-webui", port=19530)

    db_name = "test"

    try:
        # Check if the database already exists
        if db_name in db.list_database():
            print(f"Database '{db_name}' already exists.")
        else:
            # If it doesn't exist, create it
            db.create_database(db_name)
            print(f"Database '{db_name}' created successfully.")

        # Now you can use the database
        db.using_database(db_name)
        # ... perform operations within the database ...
        return

    except MilvusException as e:
        print(f"An error occurred: {e}")

def get_embeddings(text_list):
    # e.g., using SentenceTransformers or OpenAI
    embeddings = model.encode(text_list)
    #return [[0.1] * 768 for _ in text_list] 
    return embeddings


if __name__ == '__main__':
    get_db()
    doc = converter.convert(source).document

    texts = [chunk.text for chunk in chunker.chunk(doc)]

    for i, text in enumerate(texts[:5]):
        print(f"Chunk {i+1}:\n{text}\n{'-'*50}")


    milvus_client = MilvusClient(uri="http://du-webui:19530",db_name=db_name)
    #collection_name = "my_rag_collection"

    vectors = get_embeddings(texts)
    i = 0
    data = []
    
    for i in range(len(texts)):
        data.append
        [
            {
                "id": i,
                "vector": vectors[i],
                "text": texts[i],
                "metadata": {"source": "docling_conversion"}
            }
        ]

    print(f"Total count: {i}")
    # Format data as a list of dictionaries


    dim = len(data)
    print("**************************************************")
    print(f"Dimmensions found: {dim}")
    print("**************************************************")

    if milvus_client.has_collection(collection_name):
        pass
    else:
        milvus_client.create_collection(
            collection_name=collection_name,
            dimension=embedding_dim,
            metric_type="IP",  # Inner product distance
            consistency_level="Bounded",  # Supported values are (`"Strong"`, `"Session"`, `"Bounded"`, `"Eventually"`). See https://milvus.io/docs/consistency.md#Consistency-Level for more details.
    )

    """
    data = []

    for i, chunk in enumerate(tqdm(texts, desc="Processing chunks")):
        embedding = get_embeddings(vectors)
        data.append({"id": i, "vector": embedding, "text": chunk})
    """
    milvus_client.insert(collection_name=collection_name, data=data)



