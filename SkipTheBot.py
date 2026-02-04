import streamlit as st
import requests
import csv
import os
from collections import defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="SkipTheBot 500", page_icon="🎩")

# --- LOAD DATABASE ---
def load_directory():
    directory = defaultdict(dict)
    
    # Check if the file exists
    if os.path.exists("targets.csv"):
        try:
            with open("targets.csv", "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Robustness: Skip empty lines
                    if not row["company"]: continue
                    
                    comp = row["company"].strip()
                    opt = row["option"].strip()
                    
                    directory[comp][opt] = {
                        "phone": row["phone"].strip(),
                        "prompt": row["prompt"].strip()
                    }
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    else:
        # Fallback if file is missing
        directory["Demo: Chase Bank"]["Representative"] = {
            "phone": "+18009359935", "prompt": "Press 0."
        }
    return directory

DIRECTORY = load_directory()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Authentication")
    api_key_input = st.text_input("Paste your API Key", type="password").strip()
    
    st.header("📞 Your Info")
    my_phone = st.text_input("Your Cell Phone", value="+14255550199")
    
    # Show stats
    count = len(DIRECTORY)
    st.success(f"Loaded {count} Companies")
    st.info("💡 Tip: Add more to targets.csv to grow this list.")

# --- MAIN INTERFACE ---
st.title("🎩 SkipTheBot Elite")
st.write("### The Directory")

# 1. Searchable Dropdown
company_list = sorted(list(DIRECTORY.keys()))
selected_company = st.selectbox("Select Company", company_list)

# 2. Service Options
service_options = list(DIRECTORY[selected_company].keys())
selected_service = st.radio("Select Service", service_options)

# 3. Get Data
data = DIRECTORY[selected_company][selected_service]

# 4. Display & Edit
st.divider()
col1, col2 = st.columns(2)
with col1:
    target_phone = st.text_input("Phone Number", value=data["phone"])
with col2:
    target_prompt = st.text_area("Agent Instructions", value=data["prompt"], height=150)

# --- LAUNCH ---
if st.button(f"🚀 Call {selected_company}", type="primary", use_container_width=True):
    if len(api_key_input) < 5:
        st.error("❌ Key missing! Check sidebar.")
    elif len(target_phone) < 10:
        st.error("❌ Phone number looks wrong.")
    else:
        status_box = st.empty()
        status_box.info(f"Connecting to {selected_company}...")
        
        url = "https://api.bland.ai/v1/calls"
        payload = {
            "phone_number": target_phone,
            "task": target_prompt,
            "voice": "nat", 
            "transfer_phone_number": my_phone,
            "wait_for_greeting": True,
            "model": "enhanced"
        }
        headers = {"authorization": api_key_input}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                st.balloons()
                st.success(f"✅ Agent Deployed! Call ID: {data.get('call_id')}")
                st.markdown("**[Listen Live Here](https://app.bland.ai/dashboard)**")
            else:
                st.error("❌ Server Error.")
                st.json(response.json())
        except Exception as e:
            st.error(f"Failed: {e}")