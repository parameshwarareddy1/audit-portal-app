import streamlit as st
import pandas as pd
from github import Github
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="AuditCore | IT Audit Portal", layout="wide", page_icon="🛡️")

# Styling to make it look like a professional SaaS
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stExpander { background-color: white !important; border-radius: 10px; border: 1px solid #e6e9ef !important; }
    </style>
    """, unsafe_allow_html=True)

# Securely connect to GitHub
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = "parameshwarareddy1/audit-portal-app"
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error("⚠️ Connection Error. Please check your GITHUB_TOKEN in Streamlit Secrets.")
    st.stop()

# --- SIDEBAR & NAVIGATION ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1063/1063302.png", width=100)
st.sidebar.title("Audit Dashboard")
st.sidebar.info(f"**Client:** {REPO_NAME.split('/')[1].upper()}")

# --- TABS ---
tab_portal, tab_admin = st.tabs(["📋 Engagement Portal", "⚙️ Admin & Setup"])

# --- TAB: ADMIN (BULK CREATION) ---
with tab_admin:
    st.header("Upload PBC Request List")
    st.write("Upload an Excel file with 'Title' and 'Description' columns to populate the audit.")
    
    uploaded_excel = st.file_uploader("Choose PBC Excel File", type=["xlsx"])
    
    if uploaded_excel:
        try:
            df = pd.read_excel(uploaded_excel)
            st.dataframe(df, use_container_width=True)
            
            if st.button("🚀 Sync Requests to GitHub"):
                with st.spinner("Generating audit requests..."):
                    for _, row in df.iterrows():
                        repo.create_issue(
                            title=str(row['Title']),
                            body=str(row['Description'])
                        )
                    st.success(f"Successfully created {len(df)} requests!")
                    st.balloons()
        except Exception as e:
            st.error(f"Excel Error: {e}. Ensure you have 'openpyxl' in requirements.txt.")

# --- TAB: PORTAL (CHAT & EVIDENCE) ---
with tab_portal:
    st.header("Request Tracker & Interaction")
    
    # Get all open issues
    issues = repo.get_issues(state='open')
    
    if issues.totalCount == 0:
        st.warning("No active requests found. Upload a PBC list in the 'Admin' tab.")
    else:
        for issue in issues:
            # Check if evidence folder exists to show a "Status" tag
            status_color = "🔴 Pending"
            if any("✅ **New Evidence:**" in c.body for c in issue.get_comments()):
                status_color = "🟢 Evidence Received"

            with st.expander(f"{status_color} | #{issue.number}: {issue.title}", expanded=False):
                st.write(f"**Objective:** {issue.body}")
                st.caption(f"Created on: {issue.created_at.strftime('%Y-%m-%d')}")
                st.divider()
                
                chat_col, upload_col = st.columns([2, 1])
                
                with chat_col:
                    st.markdown("##### 💬 Conversation history")
                    
                    # History
                    for comment in issue.get_comments():
                        is_auditor = "parameshwarareddy1" in comment.user.login
                        with st.chat_message("assistant" if is_auditor else "user"):
                            st.write(f"**{comment.user.login}:** {comment.body}")
                    
                    # New message
                    msg_key = f"input_{issue.id}"
                    new_msg = st.text_input("Reply to this request...", key=msg_key)
                    if st.button("Send Message", key=f"btn_{issue.id}"):
                        if new_msg:
                            issue.create_comment(new_msg)
                            st.rerun()

                with upload_col:
                    st.markdown("##### 📤 Evidence Upload")
                    file_key = f"file_{issue.id}"
                    uploaded_file = st.file_uploader("Drop workpapers here", key=file_key)
                    
                    if uploaded_file:
                        with st.spinner("Uploading..."):
                            path = f"evidence/req_{issue.number}/{uploaded_file.name}"
                            repo.create_file(path, f"Upload for #{issue.number}", uploaded_file.read())
                            issue.create_comment(f"✅ **New Evidence:** `{uploaded_file.name}`")
                            st.success("Uploaded to GitHub!")
                            st.rerun()
