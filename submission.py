import pandas as pd
import requests
import time
import os

# --- CONFIGURATION ---
# Point to your LOCAL running API
API_URL = "http://127.0.0.1:8000/recommend"

# The file you just uploaded (Test Set)
INPUT_FILE = "Gen_AI Dataset (1).xlsx - Test-Set.csv"
OUTPUT_CSV = "submission.csv"

def generate_predictions():
    print("🚀 Starting Final Submission Generator...")

    # 1. Check input file
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: '{INPUT_FILE}' not found!")
        return

    # 2. Load the CSV
    try:
        df = pd.read_csv(INPUT_FILE)
        
        # Smart column detection
        possible_cols = ["Query", "Job Description", "JD"]
        query_col = next((c for c in df.columns if c in possible_cols), df.columns[0])
        
        queries = df[query_col].dropna().tolist()
        print(f"📄 Loaded {len(queries)} queries from '{INPUT_FILE}'")
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    submission_rows = []

    # 3. Process Queries
    print("-" * 60)
    for i, q in enumerate(queries):
        # Clean query
        q_text = str(q).strip()
        print(f"Processing [{i+1}/{len(queries)}]: {q_text[:40]}...")
        
        try:
            # Send to Local API (Timeout increased to 60s for safety)
            response = requests.post(API_URL, json={"query": q_text}, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("recommended_assessments", [])
                
                if not results:
                    submission_rows.append({"Query": q_text, "Assessment_url": "No result"})
                
                # Add each recommendation (Row expansion)
                for item in results:
                    submission_rows.append({
                        "Query": q_text,
                        "Assessment_url": item.get("assessment_url", item.get("url", ""))
                    })
            else:
                print(f"   ⚠️ API Error {response.status_code}. Is api.py running?")

        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
        
        # Small delay to keep your CPU happy
        time.sleep(0.5)

    print("-" * 60)

    # 4. Save
    if submission_rows:
        sub_df = pd.DataFrame(submission_rows)
        # Final Format Check
        sub_df = sub_df[["Query", "Assessment_url"]]
        sub_df.to_csv(OUTPUT_CSV, index=False)
        print(f"✅ DONE! 'submission.csv' created with {len(sub_df)} rows.")
    else:
        print("❌ Failed to generate results.")

if __name__ == "__main__":
    generate_predictions()