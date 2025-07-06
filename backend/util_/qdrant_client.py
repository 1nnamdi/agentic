from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, OptimizersConfigDiff

client = QdrantClient(url="http://localhost:6333")
dim = 384
collection_name = "my_collection"

if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE, on_disk=True),
        shard_number=2  # parallelize ingestion
    )
