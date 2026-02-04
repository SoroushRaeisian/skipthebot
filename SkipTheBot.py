import streamlit as st
import requests
import csv
import os
from collections import defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="Concierge AI", page_icon="🎩")

# --- SUBSCRIPTION TIERS ---
# This defines which password unlocks which category
SUBSCRIPTIONS = {
    "boujie": ["Personal Use"],
    "agent425": ["Realtor", "Personal Use"],
    "lawyer123": ["Legal", "Personal Use"],
    "scrubs206": ["Medical", "Personal Use"],
    "admin99": ["Personal Use", "Realtor", "Medical", "Legal"]
}

# --- AUTHENTICATION ---
if "user_role" not in st.session_state:
    st.session_state["user_role"] = []

def check_login():
    """Checks the password and sets the allowed categories."""
    if st.session_state["user_role"]:
        return True
    
    st.markdown("## 🔒 Member Login")
    pwd = st.text_input("Enter Access Code", type="password", key="auth_input")
    
    if pwd:
        # Check if the password exists in our subscription list
        if pwd in SUBSCRIPTIONS:
            st.session_state["user_role"] = SUBSCRIPTIONS[pwd]
            st.success(f"✅ Access Granted: {', '.join(st.session_state['user_role'])}")
            st.rerun()
        else:
            st.error("❌ Invalid Access Code")
    return False

if not check_login():
    st.stop()

# --- LOAD DATABASE ---
def load_directory():
    directory = defaultdict(lambda: defaultdict(dict))
    target_file = "targets.csv"
    
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not row["company"]: continue
                    
                    cat = row["category"].strip()
                    # Only load categories the user is allowed to see!
                    if cat in st.session_state["user_role"]:
                        comp = row["company"].strip()
                        opt = row["option"].strip()
                        directory[cat][comp][opt] = {
                            "phone": row["phone"].strip(),
                            "prompt": row["prompt"].strip()
                        }
        except Exception as e:
            st.error(f"Error reading database: {e}")
            
    return directory

FULL_DIRECTORY = load_directory()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📞 User Info")
    my_phone = st.text_input("Your Cell Phone", value="+14255550199")
    
    st.divider()
    st.info(f"Logged in as: {st.session_state['user_role'][0]} Member")
    if st.button("Logout"):
        st.session_state["user_role"] = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🎩 Concierge AI")

# TABS: Directory vs Custom
tab1, tab2 = st.tabs(["📖 Directory", "⚡ Custom Call"])

with tab1:
    # 1. THE MODE SELECTOR
    # Only show modes relevant to this user
    available_modes = sorted(list(FULL_DIRECTORY.keys()))
    
    if available_modes:
        selected_mode = st.selectbox("Category", available_modes, index=0)
        
        # 2. Filter Companies
        company_list = sorted(list(FULL_DIRECTORY[selected_mode].keys()))
        selected_company = st.selectbox("Select Company", company_list)
        
        # 3. Select Service
        service_options = list(FULL_DIRECTORY[selected_mode][selected_company].keys())
        selected_service = st.radio("Select Service", service_options)
        
        # 4. Get Data
        data = FULL_DIRECTORY[selected_mode][selected_company][selected_service]
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            t1_phone = st.text_input("Phone Number", value=data["phone"], key="t1_phone")
        with col2:
            t1_prompt = st.text_area("Agent Instructions", value=data["prompt"], height=100, key="t1_prompt")
        
        if st.button(f"🚀 Call {selected_company}", type="primary", use_container_width=True):
            final_phone = t1_phone
            final_prompt = t1_prompt
            should_call = True
    else:
        st.warning("No contacts found for your subscription level.")
        should_call = False

with tab2:
    st.write("### Custom Dial")
    st.caption("Call any number not in the directory.")
    t2_phone = st.text_input("Phone Number", placeholder="+1...")
    t2_prompt = st.text_area("Instructions", value="Navigate to reception. Wait for human. Transfer.", height=100)
    
    if st.button("🚀 Start Custom Call", type="primary", use_container_width=True):
        final_phone = t2_phone
        final_prompt = t2_prompt
        should_call = True

# --- EXECUTING THE CALL ---
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
                data = response.json()
                st.balloons()
                st.success(f"✅ Agent Deployed! Call ID: {data.get('call_id')}")
                st.markdown("**[Listen Live Here](https://app.bland.ai/dashboard)**")
            else:
                st.error(f"❌ Error: {response.text}")
        except Exception as e:
            st.error(f"Failed: {e}")
