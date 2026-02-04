import streamlit as st
import requests
import csv
import os
from collections import defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="SkipTheBot Elite", page_icon="🎩")

# --- AUTHENTICATION (The Gatekeeper) ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["ACCESS_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again.
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()  # Do not run the rest of the app if password is wrong

# --- LOAD DATABASE ---
def load_directory():
    directory = defaultdict(dict)
    # 1. Try reading from local file (if testing locally)
    # 2. In production, we assume the file is in the repo
    target_file = "targets.csv"
    
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not row["company"]: continue
                    comp = row["company"].strip()
                    opt = row["option"].strip()
                    directory[comp][opt] = {
                        "phone": row["phone"].strip(),
                        "prompt": row["prompt"].strip()
                    }
        except Exception as e:
            st.error(f"Database Error: {e}")
    
    # Fallback if file is missing/empty
    if not directory:
        directory["Demo: Chase Bank"]["Representative"] = {
            "phone": "+18009359935", "prompt": "Press 0."
        }
    return directory

DIRECTORY = load_directory()

# --- SIDEBAR (Cleaned Up) ---
with st.sidebar:
    st.header("📞 User Info")
    my_phone = st.text_input("Your Cell Phone", value="+14255550199")
    st.info(f"✅ Secure Connection Active\nDatabase: {len(DIRECTORY)} Companies")

# --- MAIN INTERFACE ---
st.title("🎩 Concierge Agent")
st.write("### Select a business, and I'll wait on hold for you.")

# 1. Searchable Dropdown
company_list = sorted(list(DIRECTORY.keys()))
selected_company = st.selectbox("Select Company", company_list)

# 2. Service Options
service_options = list(DIRECTORY[selected_company].keys())
selected_service = st.radio("Select Service", service_options)

# 3. Get Data
data = DIRECTORY[selected_company][selected_service]

# 4. Display
st.divider()
col1, col2 = st.columns(2)
with col1:
    target_phone = st.text_input("Phone Number", value=data["phone"])
with col2:
    target_prompt = st.text_area("Agent Instructions", value=data["prompt"], height=150)

# --- LAUNCH ---
if st.button(f"🚀 Call {selected_company}", type="primary", use_container_width=True):
    # GET KEY FROM SECRETS (Hidden from user)
    api_key_secret = st.secrets["BLAND_API_KEY"]
    
    if len(target_phone) < 10:
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
        headers = {"authorization": api_key_secret}
        
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
