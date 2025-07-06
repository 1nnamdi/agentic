from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
# Assume preprocessor, embedder, qdrant_client, collection_name are already defined (from above)

class QueryRequest(BaseModel):
    external_code: str
    description: str

@app.post("/query/")
async def query_internal_code(request: QueryRequest):
    text = f"{request.external_code} {request.description}"
    clean = preprocessor.clean_text(text)
    query_vec = embedder.encode([clean])[0]  # get first (and only) embedding

    # Search Qdrant for nearest neighbors
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vec.tolist(),
        limit=5
    )

    # Collect predicted internal codes from top hits
    internal_codes = [hit.payload["internal_code"] for hit in results]
    # (Optionally pick a majority or the first one as final prediction)
    return {"predicted_internal_codes": internal_codes}