# state = {
#     "embedding_chunks":  [
#             {"entity": {"chunk_id": "chunk_1", "content": "向量搜索结果#1"}},
#             {"entity": {"chunk_id": "chunk_2", "content": "向量搜索结果#2"}},
#             {"entity": {"chunk_id": "chunk_3", "content": "向量搜索结果#3"}},
#         ]
# }

state = {}
#弱类型："" None =》  False
# list = state.get("embedding_chunks", [])
list = state.get("embedding_chunks") or []
print(list)