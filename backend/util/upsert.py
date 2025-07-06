import glob
import pandas as pd
from qdrant_client.models import PointStruct

preprocessor = DataPreprocessor()
embedder = Embedder()
qdrant_client = qdrant  # from above setup
current_id = 0

# Ingest all CSVs in the data folder
for file_path in glob.glob("/path/to/data/*.csv"):
    for chunk in pd.read_csv(file_path, sep=';', chunksize=100000):
        # Drop rows with any NaNs in relevant columns
        chunk = chunk.dropna(subset=["external code", "description", "internal code"])
        texts = []
        payloads = []
        for _, row in chunk.iterrows():
            clean_text, payload = preprocessor.preprocess_row(
                row["external code"], row["description"], row["internal code"]
            )
            texts.append(clean_text)
            payloads.append(payload)

        # Generate embeddings in one batch
        embeddings = embedder.encode(texts)  # returns NumPy array shape (N,384)

        # Prepare Qdrant PointStructs for upsert
        points = []
        for i, vector in enumerate(embeddings):
            points.append(PointStruct(
                id=current_id + i,
                vector=vector.tolist(),
                payload=payloads[i]
            ))
        # Upsert batch into Qdrant
        qdrant_client.upsert(collection_name=collection_name, points=points)

        current_id += len(points)