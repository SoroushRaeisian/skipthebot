import streamlit as st
import requests
import csv
import os
from collections import defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="Concierge AI", page_icon="🎩")

# --- AUTHENTICATION ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    """Returns `True` if the user had the correct password."""
    if st.session_state["password_correct"]:
        return True
    
    # Show input if not authenticated
    pwd = st.text_input("Enter Access Password", type="password", key="auth_input")
    if pwd:
        # Check against the secret in Streamlit Cloud
        if pwd == st.secrets["ACCESS_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()  # Reload to clear the password box
        else:
            st.error("😕 Password incorrect")
    return False

# Stop the app if password is wrong
if not check_password():
    st.stop()

# --- LOAD DATABASE ---
def load_directory():
    # Structure: directory["Category"]["Company"]["Option"] = {phone, prompt}
    directory = defaultdict(lambda: defaultdict(dict))
    
    # 1. Try reading from local file
    target_file = "targets.csv"
    
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Skip empty lines
                    if not row["company"]: continue
                    
                    # Read the columns
                    cat = row["category"].strip()
                    comp = row["company"].strip()
                    opt = row["option"].strip()
                    
                    # Store in the dictionary
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
    # This is where the AI will transfer the call when a human answers
    my_phone = st.text_input("Your Cell Phone", value="+14255550199")
    st.success("✅ Secure Line Active")
    st.info(f"Loaded {len(FULL_DIRECTORY)} Categories")

# --- MAIN INTERFACE ---
st.title("🎩 Concierge AI")

# TABS for Standard vs Custom
tab1, tab2 = st.tabs(["📖 Directory", "⚡ Custom Call"])

with tab1:
    # 1. THE MODE SELECTOR (The Magic Switch)
    # This reads 'Personal Use', 'Realtor', 'Medical', 'Legal' from your CSV
    available_modes = sorted(list(FULL_DIRECTORY.keys()))
    
    if available_modes:
        selected_mode = st.selectbox("I am a...", available_modes, index=0)
        
        # 2. Filter Companies based on Mode
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
        
        # The Launch Button
        if st.button(f"🚀 Call {selected_company}", type="primary", use_container_width=True):
            final_phone = t1_phone
            final_prompt = t1_prompt
            should_call = True
    else:
        st.warning("Database empty. Please check targets.csv format.")
        should_call = False

with tab2:
    st.write("### Call Anyone")
    st.caption("Use this for numbers not in the database (e.g., your Dentist).")
    
    t2_name = st.text_input("Who are we calling?", placeholder="e.g. Dr. Smith Dentist")
    t2_phone = st.text_input("Phone Number", placeholder="+1...")
    t2_prompt = st.text_area("Instructions", value="Navigate to reception. Wait for human. Transfer.", height=100)
    
    if st.button("🚀 Start Custom Call", type="primary", use_container_width=True):
        final_phone = t2_phone
        final_prompt = t2_prompt
        should_call = True

# --- EXECUTING THE CALL ---
if 'should_call' in locals() and should_call:
    # Get the Hidden Key from the Cloud Vault
    api_key_secret = st.secrets["BLAND_API_KEY"]
    
    if len(final_phone) < 10:
        st.error("❌ Phone number looks wrong.")
    else:
        status_box = st.empty()
        status_box.info("Connecting...")
        
        try:
            # Send to Bland AI
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
