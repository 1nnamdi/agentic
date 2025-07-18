from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()  # 384 for this model
    def encode(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, convert_to_numpy=True)