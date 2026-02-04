import streamlit as st
import requests
import csv
import os
from collections import defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="Concierge AI", page_icon="🎩", layout="wide")

# --- SUBSCRIPTION TIERS ---
# Sell these passwords for different prices
SUBSCRIPTIONS = {
    "boujie": ["Personal Use"],           # $29/mo
    "agent425": ["Realtor", "Personal Use"], # $49/mo
    "lawyer123": ["Legal", "Personal Use"],   # $99/mo
    "scrubs206": ["Medical", "Personal Use"], # $199/mo
    "admin99": ["Personal Use", "Realtor", "Medical", "Legal"] # You
}

# --- AUTHENTICATION ---
if "user_role" not in st.session_state:
    st.session_state["user_role"] = []

def check_login():
    if st.session_state["user_role"]:
        return True
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🔒 Member Login")
        pwd = st.text_input("Enter Access Code", type="password", key="auth_input")
        if pwd:
            if pwd in SUBSCRIPTIONS:
                st.session_state["user_role"] = SUBSCRIPTIONS[pwd]
                st.success(f"✅ Access Granted")
                st.rerun()
            else:
                st.error("❌ Invalid Access Code")
    return False

if not check_login():
    st.stop()

# --- LOAD DATABASE (Cached for Speed) ---
@st.cache_data
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
                    comp = row["company"].strip()
                    opt = row["option"].strip()
                    directory[cat][comp][opt] = {
                        "phone": row["phone"].strip(),
                        "prompt": row["prompt"].strip()
                    }
        except: pass
    return directory

FULL_DIRECTORY = load_directory()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📞 User Info")
    my_phone = st.text_input("Your Cell Phone", value="+14255550199")
    st.divider()
    st.caption(f"Logged in as: {st.session_state['user_role'][0]}")
    if st.button("Logout"):
        st.session_state["user_role"] = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🎩 Concierge AI")
st.markdown("### The AI Agent that waits on hold for you.")

# Only show tabs relevant to user
user_cats = [c for c in sorted(list(FULL_DIRECTORY.keys())) if c in st.session_state["user_role"]]

if not user_cats:
    st.error("No categories available for your subscription.")
    st.stop()

# Create Tabs dynamically based on subscription
tabs = st.tabs([f"📖 {c}" for c in user_cats] + ["⚡ Custom"])

# DIRECTORY TABS
for i, cat in enumerate(user_cats):
    with tabs[i]:
        col1, col2 = st.columns([1, 1])
        with col1:
            # Company Select
            companies = sorted(list(FULL_DIRECTORY[cat].keys()))
            selected_company = st.selectbox(f"Select Company ({cat})", companies, key=f"comp_{cat}")
            
            # Service Select
            services = list(FULL_DIRECTORY[cat][selected_company].keys())
            selected_service = st.radio(f"Select Service", services, key=f"serv_{cat}")
        
        with col2:
            # Data Display
            data = FULL_DIRECTORY[cat][selected_company][selected_service]
            phone_input = st.text_input("Phone", value=data["phone"], key=f"ph_{cat}")
            prompt_input = st.text_area("Instructions", value=data["prompt"], height=150, key=f"pr_{cat}")
            
            if st.button(f"🚀 Call {selected_company}", key=f"btn_{cat}", type="primary", use_container_width=True):
                # EXECUTE CALL
                api_key_secret = st.secrets["BLAND_API_KEY"]
                if len(phone_input) < 10:
                    st.error("❌ Invalid Phone")
                else:
                    status = st.empty()
                    status.info("Dialing...")
                    try:
                        res = requests.post("https://api.bland.ai/v1/calls", json={
                            "phone_number": phone_input,
                            "task": prompt_input,
                            "voice": "nat", 
                            "transfer_phone_number": my_phone,
                            "wait_for_greeting": True,
                            "model": "enhanced"
                        }, headers={"authorization": api_key_secret})
                        if res.status_code == 200:
                            st.balloons()
                            st.success(f"✅ Connected! ID: {res.json().get('call_id')}")
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(f"Failed: {e}")

# CUSTOM TAB (Last Tab)
with tabs[-1]:
    st.write("### Custom Dial")
    c_phone = st.text_input("Phone Number", placeholder="+1...", key="custom_phone")
    c_prompt = st.text_area("Instructions", value="Navigate to reception. Wait for human. Transfer.", height=150, key="custom_prompt")
    if st.button("🚀 Start Custom Call", type="primary", use_container_width=True):
        api_key_secret = st.secrets["BLAND_API_KEY"]
        try:
            res = requests.post("https://api.bland.ai/v1/calls", json={
                "phone_number": c_phone,
                "task": c_prompt,
                "voice": "nat", 
                "transfer_phone_number": my_phone,
                "wait_for_greeting": True,
                "model": "enhanced"
            }, headers={"authorization": api_key_secret})
            if res.status_code == 200:
                st.balloons()
                st.success(f"✅ Connected! ID: {res.json().get('call_id')}")
            else:
                st.error(res.text)
        except Exception as e:
            st.error(f"Failed: {e}")
