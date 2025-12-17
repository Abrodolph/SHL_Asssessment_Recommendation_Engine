import os
import json
import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file.")

DB_PATH = "./chroma_db"
COLLECTION_NAME = "shl_assessments"

# Initialize Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=DB_PATH)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

app = FastAPI(title="SHL Recommendation Engine")

# --- DATA MODELS ---
class RecommendRequest(BaseModel):
    query: str

class AssessmentItem(BaseModel):
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: List[str]

class RecommendResponse(BaseModel):
    recommended_assessments: List[AssessmentItem]

# --- CORE LOGIC: THE AGENT ---

def get_candidates_from_db(query, k=30):
    """Stage 1: Broad Retrieval using Vector Search"""
    results = collection.query(query_texts=[query], n_results=k)
    candidates = []
    
    # Unpack Chroma results
    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        # Parse test_type string back to list
        t_types = [t.strip() for t in meta['test_type'].split(',')] if meta.get('test_type') else []
        
        candidates.append({
            "id": i,
            "name": meta['name'],
            "description": results['documents'][0][i], # Use the rich embedding text
            "test_type": t_types,
            "raw_data": {
                "url": meta['url'],
                "name": meta['name'],
                "adaptive_support": meta['adaptive_support'],
                "description": meta.get('description', results['documents'][0][i]), # Use cleaner desc if available
                "duration": int(meta['duration']),
                "remote_support": meta['remote_support'],
                "test_type": t_types
            }
        })
    return candidates

def rerank_with_gemini(query, candidates):
    """Stage 2: Intelligent Re-ranking using LLM"""
    
    # 1. Prepare a concise list for the LLM to read
    # We send ID, Name, Types, and a short snippet of the description to save tokens
    candidate_str = ""
    for c in candidates:
        desc_preview = c['description'][:200].replace("\n", " ")
        candidate_str += f"ID {c['id']}: {c['name']} | Types: {c['test_type']} | Desc: {desc_preview}...\n"

    # 2. The "Context Engineering" Prompt
    prompt = f"""
    You are an expert HR Assessment Recommender.
    
    USER QUERY: "{query}"
    
    YOUR TASK:
    Select the top 5 to 10 most relevant assessments from the candidates below.
    
    CRITICAL RULES:
    1. **Relevance:** Only choose tests that actually match the user's requirements.
    2. **Balance (Crucial):** - If the query implies BOTH technical skills (coding, finance, tools) AND soft skills (leadership, personality, teamwork), you MUST select a mix of "Knowledge & Skills" AND "Personality & Behavior" tests.
       - If the query is purely technical, focus on "Knowledge & Skills".
       - If the query is purely behavioral, focus on "Personality" or "Situational Judgement".
    
    CANDIDATES:
    {candidate_str}
    
    OUTPUT FORMAT:
    Return ONLY a JSON array of the integer IDs of the selected assessments, in order of relevance.
    Example: [12, 5, 3, 8, 1]
    """

    try:
        # Call Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # Parse IDs
        selected_ids = json.loads(response.text)
        print(f"✅ Gemini successfully reranked {len(selected_ids)} candidates!")
        
        # Map back to full data objects
        final_results = []
        for cid in selected_ids:
            # Find the candidate with this ID
            match = next((c for c in candidates if c['id'] == cid), None)
            if match:
                final_results.append(match['raw_data'])
                
        return final_results

    except Exception as e:
        print(f"⚠️ LLM Reranking failed: {e}")
        # Fallback: Just return the top 10 from vector search
        return [c['raw_data'] for c in candidates[:10]]

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    print(f"🔍 Processing: {request.query}")
    
    # 1. Retrieve broadly (Recall)
    candidates = get_candidates_from_db(request.query, k=25)
    
    # 2. Filter & Rank intelligently (Precision)
    ranked_assessments = rerank_with_gemini(request.query, candidates)
    
    # 3. Return
    return {"recommended_assessments": ranked_assessments}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)