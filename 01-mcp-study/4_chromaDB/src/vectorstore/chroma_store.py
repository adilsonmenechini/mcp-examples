import chromadb
import warnings
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import json

# Importa funções de log
from src.utils.logger import (
    log_info, log_warning, log_error, log_debug,
    log_success
)

# Silenciar warnings do Torch/Transformers
warnings.filterwarnings("ignore", category=FutureWarning)

class ChromaVectorStore:
    def __init__(self, persist_dir="./storage/chroma", collection_name="knowledge"):
        """
        Inicializa o cliente ChromaDB local e a coleção vetorial.
        """
        log_info(f"Inicializando ChromaVectorStore em: {persist_dir}")
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Usando similaridade de cosseno
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        log_success(f"Coleção '{collection_name}' pronta com {self.collection.count()} documentos.")

    def add_document(self, doc_id: str, content: str, metadata: Optional[dict] = None):
        """
        Adiciona um documento à coleção.
        """
        if not content.strip():
            log_warning(f"Conteúdo vazio para doc_id '{doc_id}' — ignorado.")
            return False
            
        try:
            # Gera embedding do conteúdo
            log_debug(f"Gerando embedding para documento: {doc_id}")
            embedding = self.embedder.encode(content).tolist()
            
            # Prepara metadados
            doc_metadata = metadata or {}
            doc_metadata["source"] = doc_metadata.get("source", "user")
            doc_metadata["id"] = doc_id
            
            # Adiciona à coleção
            log_debug(f"Adicionando documento ao ChromaDB - ID: {doc_id}")
            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            log_success(f"Documento '{doc_id}' adicionado com sucesso.")
            return True
            
        except Exception as e:
            log_error(f"Erro ao adicionar documento '{doc_id}': {e}", exc_info=True)
            return False

    def query(self, query: str, k: int = 3, min_similarity: float = 0.3) -> List[str]:
        """
        Realiza uma busca semântica por similaridade.
        
        Args:
            query: Texto da busca
            k: Número de resultados a retornar
            min_similarity: Similaridade mínima para incluir resultados (0-1)
            
        Returns:
            Lista de documentos mais relevantes
        """
        if not query.strip():
            log_warning("Consulta vazia fornecida")
            return []
            
        try:
            log_debug(f"Buscando documentos para: '{query}'")
            
            # Gera embedding da consulta
            query_embedding = self.embedder.encode(query).tolist()
            
            # Realiza a busca
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k * 2, 10),  # Busca mais resultados para filtrar depois
                include=["documents", "distances", "metadatas"]
            )
            
            # Filtra por similaridade mínima e remove duplicatas
            seen = set()
            filtered_docs = []
            
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            ):
                # Converte distância para similaridade (quanto maior, melhor)
                similarity = 1.0 - (dist / 2.0)  # Converte distância para similaridade
                
                if similarity >= min_similarity and doc not in seen:
                    # Adiciona metadados ao documento para referência
                    doc_with_meta = f"[Similaridade: {similarity:.2f}] {doc}"
                    if meta and "source" in meta:
                        doc_with_meta += f"\nFonte: {meta['source']}"
                    
                    filtered_docs.append((similarity, doc_with_meta))
                    seen.add(doc)
            
            # Ordena por similaridade (maior primeiro) e pega os k melhores
            filtered_docs.sort(key=lambda x: x[0], reverse=True)
            result_docs = [doc for _, doc in filtered_docs[:k]]
            
            log_debug(f"Encontrados {len(result_docs)} documentos relevantes")
            return result_docs
            
        except Exception as e:
            log_error(f"Erro na busca: {e}", exc_info=True)
            return []
    
    def list_documents(self, limit: int = 10) -> List[dict]:
        """
        Lista os documentos na coleção.
        """
        try:
            log_debug(f"Listando até {limit} documentos")
            results = self.collection.get(limit=limit)
            documents = [
                {"id": id_, "content": doc[:100] + "...", "metadata": meta}
                for id_, doc, meta in zip(results["ids"], results["documents"], results["metadatas"])
            ]
            log_debug(f"Encontrados {len(documents)} documentos")
            return documents
        except Exception as e:
            log_error(f"Erro ao listar documentos: {e}", exc_info=True)
            return []