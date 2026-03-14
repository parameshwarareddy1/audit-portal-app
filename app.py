import streamlit as st
import pandas as pd
from github import Github
import io

# --- SETUP ---
st.set_page_config(page_title="AuditCore | parameshwarareddy1", layout="wide")

# Securely get your token from Streamlit Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = "parameshwarareddy1/audit-portal-app"
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# --- HEADER ---
st.title("🛡️ IT Audit Engagement Portal")
st.caption(f"Active Repository: {REPO_NAME}")

# --- TABS FOR WORKFLOW ---
tab1, tab2, tab3 = st.tabs(["📋 Request List (PBC)", "💬 Communication Center", "🚀 Admin Setup"])

# --- TAB 3: ADMIN (CREATE REQUESTS FROM EXCEL) ---
with tab3:
    st.header("Bulk Request Generator")
    st.info("Upload an Excel file with columns: 'Title' and 'Description' to create audit requests.")
    
    uploaded_file = st.file_uploader("Upload PBC List (Excel)", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Preview:", df.head())
        
        if st.button("Generate Requests in GitHub"):
            with st.spinner("Creating requests..."):
                for _, row in df.iterrows():
                    # Create each row as a GitHub Issue
                    repo.create_issue(
                        title=str(row['Title']),
                        body=str(row['Description']),
                        labels=["Request"] # Tagging them as 'Request'
                    )
                st.success(f"Successfully created {len(df)} requests!")

# --- TAB 1: PBC TRACKER (OVERVIEW) ---
with tab1:
    st.header("Request Status Tracker")
    issues = repo.get_issues(state='open', labels=["Request"])
    
    if issues.totalCount == 0:
        st.warning("No active requests found. Go to 'Admin Setup' to upload some.")
    else:
        # Create a clean table view like Fieldguide
        data = []
        for i in issues:
            data.append({
                "ID": i.number,
                "Title": i.title,
                "Created": i.created_at.strftime("%Y-%m-%d"),
                "Comments": i.comments
            })
        st.table(pd.DataFrame(data))

# --- TAB 2: COMMUNICATION (THE CHAT) ---
with tab2:
    st.header("Client Chat & Evidence Upload")
    
    # Selection for which request to discuss
    issue_list = {f"#{i.number}: {i.title}": i for i in repo.get_issues(state='open')}
    
    if not issue_list:
        st.info("No open requests to discuss.")
    else:
        selected_req_title = st.selectbox("Select a Request to Open Discussion", list(issue_list.keys()))
        selected_issue = issue_list[selected_req_title]
        
        col_chat, col_files = st.columns([2, 1])
        
        with col_chat:
            st.subheader("Discussion Thread")
            # Show history
            for comment in selected_issue.get_comments():
                with st.chat_message("user" if "parameshwarareddy1" not in comment.user.login else "assistant"):
                    st.write(f"**{comment.user.login}**: {comment.body}")
            
            # New message
            chat_input = st.chat_input("Reply to client...")
            if chat_input:
                selected_issue.create_comment(chat_input)
                st.rerun()
        
        with col_files:
            st.subheader("Evidence Upload")
            file_to_upload = st.file_uploader("Upload evidence for this request", key=f"file_{selected_issue.id}")
            if file_to_upload:
                path = f"evidence/req_{selected_issue.number}/{file_to_upload.name}"
                repo.create_file(path, f"Audit Evidence: {file_to_upload.name}", file_to_upload.read())
                selected_issue.create_comment(f"✅ **Evidence Uploaded:** `{file_to_upload.name}`")
                st.success("File stored in GitHub!")
