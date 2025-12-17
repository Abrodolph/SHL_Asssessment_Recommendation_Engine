import json
import re
import os

# Configuration
INPUT_FILE = "shl_assessments.json"
OUTPUT_FILE = "shl_assessments_clean.json"

def clean_duration(duration_str):
    """
    Parses 'Approximate Completion Time in minutes = 49' -> 49
    Returns 0 if not found.
    """
    if not isinstance(duration_str, str):
        return 0
    # Find the first number in the string
    match = re.search(r'(\d+)', duration_str)
    if match:
        return int(match.group(1))
    return 0

def normalize_yes_no(value):
    """
    Converts emojis/text to strict 'Yes' or 'No' as per API spec.
    """
    if not value:
        return "No"
    
    val_str = str(value).lower()
    
    # Check for green indicators (Yes)
    if "🟢" in val_str or "yes" in val_str or "supported" in val_str:
        return "Yes"
    
    # Check for red indicators (No)
    if "🔴" in val_str or "no" in val_str or "not supported" in val_str:
        return "No"
        
    return "No" # Default safe fallback

def clean_json():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file '{INPUT_FILE}' not found.")
        return

    print(f"📂 Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    cleaned_data = []

    for item in raw_data:
        # 1. Create a new dict with ONLY the fields required by the assignment
        # Reference: Appendix 2 API Structure 
        
        # Parse Duration (Required as Integer)
        duration_int = clean_duration(item.get("duration", ""))
        
        # Transform Adaptive Support (Required as "Yes"/"No")
        # We process the raw field before deleting it
        adaptive_val = normalize_yes_no(item.get("adaptive/irt_support", ""))
        
        # Transform Remote Support (Required as "Yes"/"No")
        remote_val = normalize_yes_no(item.get("remote_testing", ""))

        # Ensure test_type is a list of strings 
        raw_test_type = item.get("test_type", "Unknown")
        if isinstance(raw_test_type, str):
            test_type_list = [t.strip() for t in raw_test_type.split(',')]
        else:
            test_type_list = raw_test_type if isinstance(raw_test_type, list) else ["Unknown"]

        new_entry = {
            "name": item.get("name", "Unknown"),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "duration": duration_int,
            "test_type": test_type_list,
            "adaptive_support": adaptive_val, # Renamed and Cleaned
            "remote_support": remote_val      # Renamed and Cleaned
        }
        
        # NOTE: The following fields are explicitly EXCLUDED as per your request:
        # - adaptive/irt_support (Raw)
        # - languages
        # - job_level
        # - source_tab
        
        cleaned_data.append(new_entry)

    # Save to new file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Cleanup Complete!")
    print(f"   Processed {len(cleaned_data)} assessments.")
    print(f"   Removed: 'adaptive/irt_support', 'languages', 'job_level', 'source_tab'")
    print(f"   Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_json()