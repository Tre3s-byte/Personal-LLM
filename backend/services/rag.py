from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from .chunker import chunk_code
from pathlib import Path
from pathlib import Path
from PyPDF2 import PdfReader


def build_index(self, texts):
    if not texts:
        raise ValueError("No documents to index. Check your load_documents function.")
    embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dimension = embeddings.shape[1]  # now safe
    self.index = faiss.IndexFlatL2(dimension)
    self.index.add(np.array(embeddings))
    self.documents = texts


class LocalRAG:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.documents = []

    def build_index(self, texts):
        embeddings = self.model.encode(texts)
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings))
        self.documents = texts

    def search(self, query, top_k=4):
        query_vec = self.model.encode([query])
        distances, indices = self.index.search(query_vec, top_k)

        return [self.documents[i] for i in indices[0]]


def load_documents(paths=None):
    if paths is None:
        paths = [Path.home() / "Documents", Path.home() / "Downloads"]

    all_texts = []
    for folder in paths:
        for file in folder.rglob("*"):
            if file.suffix.lower() == ".txt":
                all_texts.append(file.read_text(encoding="utf-8"))
            elif file.suffix.lower() == ".pdf":
                try:
                    reader = PdfReader(file)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    if text.strip():
                        all_texts.append(text)
                except Exception as e:
                    print(f"Failed to read {file}: {e}")

    return all_texts


def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # overlap
    return chunks
