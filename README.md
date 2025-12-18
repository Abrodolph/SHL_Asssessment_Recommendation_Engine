# 🎯 SHL Assessment Recommendation Engine

**A Smart Talent Acquisition Tool for HR Professionals**

## 📖 Project Overview

This project is an **AI-powered Recommendation Engine** designed to help HR professionals and Recruiters instantly find the best SHL assessments for a specific job role. By analyzing Job Descriptions (JDs) or natural language queries, the engine intelligently maps requirements to SHL's extensive assessment catalog.

The system uses a **Hybrid AI Architecture**:
1.  **Semantic Search (Vector Embeddings):** Understands the *meaning* behind a query (e.g., "coding test" ≈ "Python/Java assessment").
2.  **Generative AI Reranking (Google Gemini):** Uses an LLM to logically evaluate and rerank the top candidates for maximum relevance.
3.  **Robust Fallback Layer:** Includes an offline TF-IDF engine that guarantees results even if external AI APIs are down.

---

## 🚀 Key Features

* **🔍 Semantic Search:** Doesn't just match keywords; understands context (e.g., linking "finance manager" to "numerical reasoning").
* **🤖 Agentic Reranking:** A "smart agent" step where Google Gemini 1.5 Flash evaluates the shortlist to ensure perfect alignment with user intent.
* **⚡ Ultra-Fast & Lightweight:** Optimized "Lite Architecture" runs entirely in-memory using Cloud-Native embeddings, allowing deployment on free-tier servers (Render).
* **🛡️ Crash-Proof Design:**
    * **Primary Mode:** Live AI (Gemini + Vector DB).
    * **Fallback Mode:** Offline TF-IDF (Term Frequency-Inverse Document Frequency) ensures 100% uptime.
* **📊 Interactive UI:** A clean, responsive dashboard built with Streamlit.

---

## 🛠️ Tech Stack

| Component | Technology Used |
| :--- | :--- |
| **Frontend** | Streamlit (Python) |
| **Backend API** | FastAPI, Uvicorn |
| **AI / LLM** | Google Gemini 1.5 Flash (via `google-generativeai`) |
| **Vector Search** | ChromaDB (In-Memory Mode), Google Embeddings (`embedding-001`) |
| **Offline Fallback** | Scikit-Learn (TF-IDF Vectorizer, Cosine Similarity) |
| **Data Processing** | Pandas, NumPy |
| **Deployment** | Render (Backend), Streamlit Cloud (Frontend) |

---

## ⚙️ Architecture

The system follows a microservices-style architecture:

```
graph LR
    User[User / Recruiter] -->|Enters Query| Frontend[Streamlit UI]
    Frontend -->|POST Request| API[FastAPI Backend]
    API -->|1. Vector Search| Chroma[ChromaDB (In-Memory)]
    Chroma -->|Top 20 Matches| API
    API -->|2. Reranking| Gemini[Google Gemini AI]
    Gemini -->|Top 5 Optimized Results| Frontend
    Frontend -->|Display Results| User
```
## 💻 Local Setup Guide
Follow these steps to run the engine on your own machine.

Prerequisites
```
Python 3.9 or higher
```
A Google Gemini API Key (Get it here)

1. Clone the Repository
```

git clone [https://github.com/YOUR_USERNAME/SHL_Assessment_Recommendation_Engine.git](https://github.com/YOUR_USERNAME/SHL_Assessment_Recommendation_Engine.git)
cd SHL_Assessment_Recommendation_Engine
```
2. Install Dependencies
```

pip install -r requirements.txt
```
3. Configure API Key
Create a .env file in the root directory and add your key:

```
GEMINI_API_KEY=your_actual_api_key_here
```
4. Run the Backend (API)
Open a terminal and run:

```
python api.py
```
You should see: 🚀 Starting API Server on Port 8000...

5. Run the Frontend (UI)
Open a new terminal window and run:

```
streamlit run app.py
```
The app will open automatically in your browser at http://localhost:8501.

🧪 Testing & Evaluation
Generating Batch Predictions
To evaluate the model against a test dataset (CSV/Excel), use the generation script. It will process the file and create a submission.csv.

Method 1: Online (Uses API)

```
python generate_submission.py
```
Method 2: Offline (Zero-Dependency) Useful if API limits are reached. Uses local TF-IDF math.
```
python generate_results.py
```
🔗 API Documentation
The backend exposes a REST API that can be integrated into any ATS (Applicant Tracking System).

Endpoint: POST /recommend

Request:

JSON

{
  "query": "I need a test for a Senior Java Developer with leadership skills"
}
Response:

```JSON

{
  "recommended_assessments": [
    {
      "assessment_name": "Core Java (Advanced)",
      "url": "[https://www.shl.com/](https://www.shl.com/)...",
      "match_reason": "High technical relevance"
    },
    {
      "assessment_name": "Leadership Scenarios",
      "url": "[https://www.shl.com/](https://www.shl.com/)...",
      "match_reason": "Matches leadership requirement"
    }
  ]
}
```
### 📂 Project Structure
```Plaintext

SHL_Recommendation_Engine/
├── api.py                   # FastAPI Backend Server
├── app.py                   # Streamlit Frontend UI
├── shl_assessments.json     # The Database (Assessment Catalog)
├── requirements.txt         # Python Dependencies
├── generate_results.py      # Offline Batch Processing Script
└── README.md                # Documentation
```

Developed for the SHL AI Assessment Challenge.
