import re

class DataPreprocessor:
    def __init__(self):
        # Map German umlauts to ASCII
        self.umlaut_map = str.maketrans({
            "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
            "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"
        })
    def clean_text(self, text: str) -> str:
        text = text.translate(self.umlaut_map)      # Replace umlauts
        text = re.sub(r'[^0-9A-Za-z\s]', '', text) # Remove symbols except spaces
        text = re.sub(r'\s+', ' ', text).strip()   # Collapse whitespace
        return text.lower()
    def preprocess_row(self, external: str, description: str, internal: str):
        """Combine and clean fields, return text and payload metadata."""
        combined = f"{external} {description}"
        clean = self.clean_text(combined)
        # Payload can include original fields for reference
        payload = {"external_code": external, "internal_code": internal}
        return clean, payload
