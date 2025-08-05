import sys
import os
from pathlib import Path
import chromadb
from pprint import pprint

# Adiciona o diretório raiz ao path do Python
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.vectorstore.chroma_store import ChromaVectorStore

def check_stored_data():
    """Verifica os dados armazenados diretamente no ChromaDB"""
    print("\n🔍 Verificando dados armazenados...")
    
    # Conecta diretamente ao ChromaDB
    client = chromadb.PersistentClient(path="./storage/chroma")
    
    try:
        # Lista todas as coleções
        collections = client.list_collections()
        print(f"\n📚 Coleções encontradas: {len(collections)}")
        
        for collection in collections:
            print(f"\n📂 Coleção: {collection.name}")
            print(f"📊 Total de itens: {collection.count()}")
            
            # Pega os primeiros 5 itens
            items = collection.get(limit=5)
            if items and 'ids' in items and len(items['ids']) > 0:
                print("\n📝 Documentos armazenados:")
                for i, (doc_id, doc) in enumerate(zip(items['ids'], items['documents']), 1):
                    print(f"   {i}. ID: {doc_id}")
                    print(f"      Conteúdo: {doc[:100]}...")
            else:
                print("ℹ️  Nenhum documento encontrado nesta coleção.")
                
    except Exception as e:
        print(f"❌ Erro ao verificar dados armazenados: {e}")

def test_chroma():
    # Inicializa o ChromaVectorStore
    print("🔍 Inicializando ChromaVectorStore...")
    vector_store = ChromaVectorStore(persist_dir="./storage/chroma")
    
    # Verifica documentos existentes
    print("\n📋 Verificando documentos existentes...")
    test_query = "verificação de documentos"
    existing_docs = vector_store.query(test_query, k=5)
    
    if existing_docs and len(existing_docs) > 0:
        print(f"✅ Encontrados {len(existing_docs)} documentos existentes.")
        print("📝 Documentos de exemplo:")
        for i, doc in enumerate(existing_docs[:3], 1):
            print(f"   {i}. {doc[:100]}...")
    else:
        print("ℹ️  Nenhum documento encontrado. Adicionando documentos de exemplo...")
        
        documents = {
            "doc1": "Python é uma linguagem de programação de alto nível",
            "doc2": "ChromaDB é um banco de dados vetorial open-source",
            "doc3": "Inteligência Artificial está transformando a tecnologia",
            "doc4": "Machine Learning é um subcampo da IA",
            "doc5": "Python é amplamente usado em ciência de dados"
        }
        
        print("\n📝 Adicionando documentos...")
        for doc_id, content in documents.items():
            print(f"- {doc_id}: {content[:30]}...")
            vector_store.add_document(doc_id, content)
    
    # Verifica os dados armazenados
    check_stored_data()
    
    # Realiza algumas consultas
    print("\n🔎 Realizando consultas de teste...")
    queries = ["O que é Python?", "Fale sobre bancos de dados vetoriais"]
    
    for query in queries:
        print(f"\n❓ Consulta: '{query}'")
        results = vector_store.query(query, k=2)
        print(f"   Resultados encontrados ({len(results)}):")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result[:80]}...")
    
    print("\n✅ Teste concluído!")
    print("💾 Dados armazenados em: ./storage/chroma")

if __name__ == "__main__":
    test_chroma()
