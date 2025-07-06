from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import openai
import math

app = FastAPI()

# Initialize components
preprocessor = DataPreprocessor()
embedder = Embedder()
qdrant_client = QdrantClient(url="http://localhost:6333")
collection_name = "my_collection"
ingestor = QdrantIngestor(qdrant_client, collection_name, embedder, preprocessor)

# Pydantic models
class IngestRequest(BaseModel):
    folder_path: str

class QueryRequest(BaseModel):
    external_code: str
    description: str

@app.post("/ingest")
def ingest_data(req: IngestRequest):
    try:
        ingestor.ingest_csv_folder(req.folder_path)
        return {"status": "ingestion completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query_code(req: QueryRequest):
    # Clean input
    ext = preprocessor.clean_text(req.external_code)
    desc = preprocessor.clean_text(req.description)
    query_text = ext + " " + desc

    # Embed and search Qdrant
    query_vec = embedder.encode([query_text])[0]
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vec.tolist(),
        limit=5
    )
    if not results:
        return {"internal_code": None, "confidence": 0.0}

    # Build context from top results
    context = ""
    for res in results:
        payload = res.payload
        context += f"External: {payload.get('external_code','')}, Description: {payload.get('description','')}\n"
    context = context.strip()

    # Prepare LLM prompt (classification of internal code)
    prompt = (
        f"Context of similar entries:\n{context}\n\n"
        f"Given the external code '{req.external_code}' and description '{req.description}', "
        "predict the *internal code*. Answer with the code only."
    )

    # Call OpenAI (using chat completion with logprobs for confidence)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=10,
        logprobs=5  # retrieve logprobs for confidence
    )
    choice = response.choices[0]
    code_prediction = choice.message['content'].strip()

    # Compute confidence from token logprobs (as exp(logprob))
    # Assume the code is a single token or first token
    logprob = choice.logprobs.token_logprobs[0] if choice.logprobs.token_logprobs else None
    confidence = math.exp(logprob) if logprob is not None else None

    return {"internal_code": code_prediction, "confidence": confidence}
