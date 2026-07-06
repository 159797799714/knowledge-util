from config.milvus_config import milvus_config
from utils.milvus_utils import get_milvus_client, escape_milvus_string

milvus_client = get_milvus_client()
collection_name = milvus_config.item_name_collection
item_name = 'BrotherHAK"180烫金机'
# print(item_name)
item_name = escape_milvus_string("Brother\HAK180烫金机")
# print(item_name)
milvus_client.delete(collection_name=collection_name, filter=f'item_name=="{item_name}"')

print("ok")
