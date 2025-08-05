import faiss
import numpy as np
from typing import List, Dict
import pickle


class VectorSearchAgent:
    def __init__(self, dim: int = 128, index_type: str = "flat"):
        self.dim = dim
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(dim)
        elif index_type == "ivf":
            nlist = 100  # number of clusters
            quantizer = faiss.IndexFlatL2(dim)
            self.index = faiss.IndexIVFFlat(quantizer, dim, nlist)
            self.index.train([])  # Need vectors for training
        self.vectors = []
        self.ids = []

    def add_vectors(self, vectors: List[List[float]], ids: List[int]) -> None:
        try:
            vectors_np = np.array(vectors).astype("float32")
            if vectors_np.shape[1] != self.dim:
                raise ValueError(f"Expected vectors of dimension {self.dim}")
            self.index.add(vectors_np)
            self.vectors.extend(vectors_np)
            self.ids.extend(ids)
        except Exception as e:
            raise Exception(f"Failed to add vectors: {str(e)}")

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict]:
        try:
            qv = np.array(query_vector).astype("float32").reshape(1, -1)
            if qv.shape[1] != self.dim:
                raise ValueError(f"Expected query vector of dimension {self.dim}")
            distances, indices = self.index.search(qv, k)
            return [
                {"id": self.ids[idx], "distance": float(dist)}
                for dist, idx in zip(distances[0], indices[0])
                if idx != -1
            ]
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    def save(self, path: str) -> None:
        try:
            faiss.write_index(self.index, f"{path}.index")
            with open(f"{path}.meta", "wb") as f:
                pickle.dump({"vectors": self.vectors, "ids": self.ids}, f)
        except Exception as e:
            raise Exception(f"Failed to save index: {str(e)}")

    def load(self, path: str) -> None:
        try:
            self.index = faiss.read_index(f"{path}.index")
            with open(f"{path}.meta", "rb") as f:
                meta = pickle.load(f)
                self.vectors = meta["vectors"]
                self.ids = meta["ids"]
        except Exception as e:
            raise Exception(f"Failed to load index: {str(e)}")
