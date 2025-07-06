import re
import unicodedata

class DataPreprocessor:
    def __init__(self):
        # Map German-specific chars to ASCII
        self.trans = str.maketrans("äöüÄÖÜß", "aeoeueAeOeUess")

    def clean_text(self, text: str) -> str:
        if pd.isna(text):
            return ""
        text = text.translate(self.trans)                       # replace umlauts etc.
        text = unicodedata.normalize("NFKD", text)             # normalize accents
        text = re.sub(r"[^A-Za-z0-9 ]+", " ", text)           # remove punctuation
        text = re.sub(r"\s+", " ", text).strip().lower()      # collapse whitespace
        return text