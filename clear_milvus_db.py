from pymilvus import connections, db
from pymilvus import MilvusClient

client = MilvusClient(
    uri="http://du-webui:19530",
    token="root:Milvus"
)

# List all existing databases
list = client.list_databases()

print(list)


for item in list:
    print(item)
    # 1. Connect to Milvus
    #connections.connect(host="du-webui", port="19530")

    # 2. Use the target database (assuming it's not 'default')
    database_name = item
    client.using_database(database_name)

    # 3. List and drop all collections
    collections = client.list_collections(db_name=database_name)
    #collections = db.list_collections()
    for collection_name in collections:
        print(f"Dropping collection: {collection_name}")
        client.drop_collection(collection_name) # This permanently deletes the data

    # 4. Drop the database
    if database_name != 'default':
        client.drop_database(database_name)
        print(f"Database '{database_name}' dropped.")
