import json
import os
import chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATION ---
# Point this to your final, clean JSON file
DATA_PATH = "shl_assessments.json" 
DB_PATH = "./chroma_db"
COLLECTION_NAME = "shl_assessments"

def ingest_data():
    # 1. Initialize ChromaDB (Persistent)
    print(f"📂 Initializing ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Use the standard, high-quality Sentence Transformer model
    # This downloads the model locally (~80MB) on first run
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Reset collection to ensure a clean slate
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("   🗑️  Deleted old collection to avoid duplicates.")
    except:
        pass
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"} # Cosine similarity is best for text matching
    )

    # 2. Load Data
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found. Please check the filename.")
        return

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"   📄 Loaded {len(data)} assessments.")

    # 3. Prepare Vectors
    ids = []
    documents = []
    metadatas = []

    print("   ⚙️  Processing and embedding data...")
    
    for idx, item in enumerate(data):
        # A. Create a Rich Document for the AI to "Read"
        # We combine key fields so the semantic search understands the context.
        # Example: "Name: Java Test. Type: Knowledge & Skills. Description: Tests coding ability..."
        
        test_type_str = ", ".join(item.get('test_type', []))
        
        doc_text = (
            f"Assessment Name: {item.get('name', 'Unknown')}. "
            f"Test Type: {test_type_str}. "
            f"Description: {item.get('description', '')}"
        )
        
        # B. Clean Metadata for Filtering
        # ChromaDB requires metadata values to be str, int, float, or bool. Lists aren't directly supported in metadata.
        meta = {
            "name": item.get('name', 'Unknown'),
            "url": item.get('url', ''),
            "duration": item.get('duration', 0),
            "adaptive_support": item.get('adaptive_support', 'No'),
            "remote_support": item.get('remote_support', 'No'),
            # Store test_type as a string in metadata for easy retrieval/filtering
            "test_type": test_type_str 
        }

        ids.append(str(idx))
        documents.append(doc_text)
        metadatas.append(meta)

    # 4. Ingest into DB
    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"✅ Success! Ingested {len(ids)} items into '{COLLECTION_NAME}'.")
        print(f"   Database is ready at: {os.path.abspath(DB_PATH)}")
    else:
        print("⚠️  No items found to ingest.")

if __name__ == "__main__":
    ingest_data()