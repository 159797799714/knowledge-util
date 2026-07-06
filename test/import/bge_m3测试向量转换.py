from utils.embedding_utils import get_bge_m3_ef

docs = [
    "hello.",
    "再见",
    "苹果",
]

model = get_bge_m3_ef()

docs_embeddings = model.encode_documents(docs)

print(docs_embeddings)