import streamlit as st
import requests
import csv
import os
from collections import defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="SkipTheBot Elite", page_icon="🎩")

# --- AUTHENTICATION ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]:
        return True
    
    # Show input if not authenticated
    pwd = st.text_input("Enter Access Password", type="password", key="auth_input")
    if pwd:
        if pwd == st.secrets["ACCESS_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()  # Reload to clear the password box
        else:
            st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# --- LOAD DATABASE ---
def load_directory():
    directory = defaultdict(dict)
    target_file = "targets.csv"
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["company"]:
                        directory[row["company"].strip()][row["option"].strip()] = {
                            "phone": row["phone"].strip(),
                            "prompt": row["prompt"].strip()
                        }
        except: pass
    return directory

DIRECTORY = load_directory()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📞 User Info")
    my_phone = st.text_input("Your Cell Phone", value="+14255550199") # Update this default!
    st.success(f"Database: {len(DIRECTORY)} Companies")

# --- MAIN INTERFACE ---
st.title("🎩 Concierge Agent")

# TABS for "Directory" vs "Custom"
tab1, tab2 = st.tabs(["📖 Directory", "⚡ Custom Call"])

with tab1:
    company_list = sorted(list(DIRECTORY.keys()))
    if company_list:
        selected_company = st.selectbox("Select Company", company_list)
        service_options = list(DIRECTORY[selected_company].keys())
        selected_service = st.radio("Select Service", service_options)
        data = DIRECTORY[selected_company][selected_service]
        
        t1_phone = st.text_input("Phone Number", value=data["phone"], key="t1_phone")
        t1_prompt = st.text_area("Agent Instructions", value=data["prompt"], height=150, key="t1_prompt")
        
        if st.button(f"🚀 Call {selected_company}", type="primary"):
            final_phone = t1_phone
            final_prompt = t1_prompt
            should_call = True
    else:
        st.warning("No CSV found. Upload targets.csv to GitHub!")
        should_call = False

with tab2:
    st.write("### Call Anyone")
    t2_name = st.text_input("Who are we calling?", placeholder="e.g. Dr. Smith Dentist")
    t2_phone = st.text_input("Phone Number", placeholder="+1...")
    t2_prompt = st.text_area("Instructions", value="Navigate to reception. Wait for human. Say 'I have a patient on the line'. Transfer.", height=150)
    
    if st.button("🚀 Start Custom Call", type="primary"):
        final_phone = t2_phone
        final_prompt = t2_prompt
        should_call = True

# --- EXECUTING THE CALL (Shared Logic) ---
if 'should_call' in locals() and should_call:
    api_key_secret = st.secrets["BLAND_API_KEY"]
    
    if len(final_phone) < 10:
        st.error("❌ Phone number looks wrong.")
    else:
        status_box = st.empty()
        status_box.info("Connecting...")
        
        try:
            response = requests.post("https://api.bland.ai/v1/calls", json={
                "phone_number": final_phone,
                "task": final_prompt,
                "voice": "nat", 
                "transfer_phone_number": my_phone,
                "wait_for_greeting": True,
                "model": "enhanced"
            }, headers={"authorization": api_key_secret})
            
            if response.status_code == 200:
                st.balloons()
                st.success(f"✅ Agent Deployed! Call ID: {response.json().get('call_id')}")
                st.markdown("**[Listen Live](https://app.bland.ai/dashboard)**")
            else:
                st.error(f"❌ Error: {response.text}")
        except Exception as e:
            st.error(f"Failed: {e}")
