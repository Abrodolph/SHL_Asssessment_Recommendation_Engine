import streamlit as st
import requests
import pandas as pd
import json

# --- CONFIGURATION ---
# This points to your running FastAPI backend
API_URL = "http://localhost:8000/recommend"
HEALTH_URL = "http://localhost:8000/health"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="SHL Intelligent Recommender",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for a professional look
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    .main-header { font-size: 2.5rem; color: #4B4B4B; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.shl.com/assets/images/shl-logo.svg", width=150)
    st.title("System Status")
    
    # Check if backend is alive
    try:
        health = requests.get(HEALTH_URL, timeout=2)
        if health.status_code == 200:
            st.success("🟢 API Online")
        else:
            st.error(f"🔴 API Error: {health.status_code}")
    except:
        st.error("🔴 API Offline")
        st.warning("⚠️ Make sure `python api.py` is running in another terminal!")

    st.markdown("---")
    st.markdown("### 📝 Instructions")
    st.markdown("1. Enter a **Job Description** or **Query**.")
    st.markdown("2. Click **Get Recommendations**.")
    st.markdown("3. View balanced assessment options.")

# --- MAIN CONTENT ---
st.title("🧠 SHL Assessment Recommender")
st.markdown("#### AI-Powered Search for Hard & Soft Skills")

# Input Form
with st.form("search_form"):
    col1, col2 = st.columns([4, 1])
    with col1:
        query_input = st.text_input(
            "Search Query:",
            placeholder="e.g., 'Java developer who can also lead a team' or paste a JD URL"
        )
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        submitted = st.form_submit_button("Search 🚀")

if submitted and query_input:
    with st.spinner("🤖 Analyzing intent & retrieving assessments..."):
        try:
            # SEND REQUEST TO BACKEND
            payload = {"query": query_input}
            response = requests.post(API_URL, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("recommended_assessments", [])
                
                if not results:
                    st.warning("No assessments found. Try a different query.")
                else:
                    st.success(f"Found {len(results)} relevant assessments!")
                    
                    # Display Results
                    for i, item in enumerate(results):
                        with st.expander(f"{i+1}. {item['name']} ({item['duration']} mins)", expanded=True):
                            # Layout: Description on left, Meta tags on right
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.markdown(f"**Description:** {item['description']}")
                                st.markdown(f"[🔗 View on SHL Catalog]({item['url']})")
                            with c2:
                                st.caption("Test Types:")
                                st.info(", ".join(item['test_type']))
                                st.caption("Features:")
                                if item['adaptive_support'] == "Yes": st.write("✅ Adaptive")
                                if item['remote_support'] == "Yes": st.write("✅ Remote")
            else:
                st.error(f"Server Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to Backend. Is it running?")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

elif submitted and not query_input:
    st.warning("Please enter a query first.")