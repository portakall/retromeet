from pymilvus import connections, Collection, utility

# Assuming you have already established a connection to your Milvus server
connections.connect(host="localhost", port="19530")

try:
    collection_names = utility.list_collections()
    if collection_names:
        for collection_name in collection_names:
            utility.drop_collection(collection_name)
            print(f"Successfully dropped the collection: {collection_name}")
    else:
        print("No collections found to drop.")
except Exception as e:
    print(f"An error occurred while trying to drop collections: {e}")