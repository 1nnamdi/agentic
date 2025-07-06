from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self):
        # Load a multilingual MiniLM model (free, Apache-2.0 license)
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of preprocessed texts into vectors."""
        return self.model.encode(texts, show_progress_bar=False, batch_size=64)
