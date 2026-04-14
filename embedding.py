import streamlit as st
from sentence_transformers import SentenceTransformer
import chromadb

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()
client=chromadb.PersistentClient(path="./chroma_db")
collection=client.get_or_create_collection(name="memories")


def add_embedding(memory_id, content, user_id="ayush"):
    embedding = model.encode(content).tolist()
    collection.add(
        ids=[str(memory_id)],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"user_id": user_id}]  # Save user_id in metadata
    )

def search_similar(query, n_results=3, user_id=None):
    query_embedding = model.encode(query).tolist()
    
    # Apply user filter if user_id is provided
    where = {"user_id": user_id} if user_id else None
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where
    )
    return results