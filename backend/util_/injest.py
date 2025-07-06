import pandas as pd
from qdrant_client.http.models import PointStruct

class QdrantIngestor:
    def __init__(self, qdrant_client: QdrantClient, collection_name: str, embedder: Embedder, preprocessor: DataPreprocessor):
        self.client = qdrant_client
        self.collection = collection_name
        self.embedder = embedder
        self.pre = preprocessor

    def ingest_csv_folder(self, folder_path: str):
        import os, glob
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        for csv_file in csv_files:
            self.ingest_csv_file(csv_file)

    def ingest_csv_file(self, file_path: str):
        # Read CSV in chunks to handle large size
        for chunk in pd.read_csv(file_path, sep=";", chunksize=100000):
            records = []
            for _, row in chunk.iterrows():
                if pd.isna(row['external code']) or pd.isna(row['description']) or pd.isna(row['internal code']):
                    continue  # drop incomplete rows
                ext = self.pre.clean_text(str(row['external code']))
                desc = self.pre.clean_text(str(row['description']))
                if not ext or not desc:
                    continue
                text = ext + " " + desc
                payload = {
                    "external_code": ext,
                    "description": desc,
                    "internal_code": row['internal code']
                }
                records.append((text, payload))
            if not records:
                continue
            # Batch embed and upsert
            texts, payloads = zip(*records)
            vectors = self.embedder.encode(list(texts))
            points = []
            for i, vec in enumerate(vectors):
                point_id = None  # Let Qdrant assign an ID, or use a custom ID
                points.append(PointStruct(id=point_id, vector=vec.tolist(), payload=payloads[i]))
            # Upsert points into Qdrant
            self.client.upsert(collection_name=self.collection, points=points, wait=True)
