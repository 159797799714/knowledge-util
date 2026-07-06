from utils.embedding_utils import generate_embeddings

text = "BrotherHAK180烫金机"

result = generate_embeddings([text])
print(result["dense"])
print(result["sparse"])