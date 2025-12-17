import os
import json
import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
import uvicorn

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env. AI features will fail.")

DB_PATH = "./chroma_db"
COLLECTION_NAME = "shl_assessments"

# --- INIT GEMINI ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # KEEPING YOUR REQUESTED MODEL
    model = genai.GenerativeModel('gemini-2.5-flash') 
else:
    model = None

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=DB_PATH)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

app = FastAPI(title="SHL Recommendation Engine")

# --- DATA MODELS ---
class RecommendRequest(BaseModel):
    query: str

class AssessmentItem(BaseModel):
    assessment_url: str
    assessment_name: str
    adaptive_support: Optional[str] = "No" # Default to avoid validation error
    description: str
    duration: Optional[int] = 0           # Default to avoid validation error
    remote_support: Optional[str] = "No"  # Default to avoid validation error
    test_type: List[str]

class RecommendResponse(BaseModel):
    recommended_assessments: List[AssessmentItem]

# --- CORE LOGIC ---

def get_candidates_from_db(query, k=30):
    """Stage 1: Broad Retrieval using Vector Search"""
    try:
        results = collection.query(query_texts=[query], n_results=k)
        candidates = []
        
        if not results['ids']: return []

        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            
            # Robust splitting for test_type
            t_type_raw = meta.get('test_type', "")
            if isinstance(t_type_raw, str):
                t_types = [t.strip() for t in t_type_raw.split(',')] if t_type_raw else []
            else:
                t_types = []

            # Robust integer casting for duration
            try:
                dur = int(float(meta.get('duration', 0)))
            except:
                dur = 0

            candidates.append({
                "id": i,
                "name": meta.get('name', 'Unknown'),
                "description": results['documents'][0][i],
                "test_type": t_types,
                "raw_data": {
                    "assessment_url": meta.get('url', '#'),
                    "assessment_name": meta.get('name', 'Unknown Test'),
                    "adaptive_support": str(meta.get('adaptive_support', 'No')),
                    "description": meta.get('description', results['documents'][0][i])[:500],
                    "duration": dur,
                    "remote_support": str(meta.get('remote_support', 'No')),
                    "test_type": t_types
                }
            })
        return candidates
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return []

def rerank_with_gemini(query, candidates):
    """Stage 2: Intelligent Re-ranking using LLM"""
    if not candidates: return []
    if not model: return [c['raw_data'] for c in candidates[:10]] # Safety fallback

    # 1. Prepare context
    candidate_str = ""
    for c in candidates:
        desc_preview = c['description'][:200].replace("\n", " ")
        candidate_str += f"ID {c['id']}: {c['name']} | Types: {c['test_type']} | Desc: {desc_preview}...\n"

    prompt = f"""
    You are an expert HR Assessment Recommender.
    USER QUERY: "{query}"
    
    YOUR TASK:
    Select the top 5 to 10 most relevant assessments.
    
    CRITICAL RULES:
    1. Relevance matches the user's needs.
    2. Balance Hard & Soft skills if implied.
    
    CANDIDATES:
    {candidate_str}
    
    OUTPUT: JSON array of IDs. Example: [12, 5, 3]
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        selected_ids = json.loads(response.text)
        print(f"✅ Gemini successfully reranked {len(selected_ids)} candidates!")
        
        final_results = []
        for cid in selected_ids:
            match = next((c for c in candidates if c['id'] == cid), None)
            if match:
                final_results.append(match['raw_data'])
                
        # If model returns empty list (it happens), fallback to top 5 DB results
        if not final_results:
             return [c['raw_data'] for c in candidates[:5]]

        return final_results

    except Exception as e:
        print(f"⚠️ LLM Reranking failed (using DB fallback): {e}")
        return [c['raw_data'] for c in candidates[:10]]

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    print(f"🔍 Processing: {request.query}")
    
    # 1. Retrieve
    candidates = get_candidates_from_db(request.query, k=25)
    
    # 2. Rerank
    ranked_assessments = rerank_with_gemini(request.query, candidates)
    
    return {"recommended_assessments": ranked_assessments}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
