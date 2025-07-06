from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

# Connect to local Qdrant
qdrant = QdrantClient(host="localhost", port=6333)

# (Re)create a collection named "product_data"
collection_name = "product_data"
qdrant.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)