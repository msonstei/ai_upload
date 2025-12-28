from pymilvus import MilvusClient

# Connect to the Milvus server
# The default database is 'default', but this operation lists all.
client = MilvusClient(
    uri="http://du-webui:19530",
    # Optionally, provide credentials if authentication is enabled
    # token="root:Milvus",
)

# List all databases
databases = client.list_databases()
collections = client.list_collections()
print("List of databases:", databases)
#print(f"Collections: {collections}")
for items in databases:
    database_name = items
    collections = client.list_collections(db_name=database_name)
    print(f"Collections in database '{database_name}': {collections}")
