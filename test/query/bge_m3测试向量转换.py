from utils.embedding_utils import get_bge_m3_ef

docs = ["hello."]
model = get_bge_m3_ef()
docs_embeddings = model.encode_documents(docs)