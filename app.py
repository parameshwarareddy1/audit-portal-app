import streamlit as st
from github import Github
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="AuditPortal Pro", layout="wide")

# --- AUTHENTICATION (For Resume: Use Secrets) ---
# On Streamlit Cloud, you'll put these in "Advanced Settings > Secrets"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 
REPO_NAME = "your-github-username/client-audit-repo" # Example

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- APP INTERFACE ---
st.title("🛡️ IT Audit Evidence Portal")
st.caption(f"Connected to Repository: {REPO_NAME}")

# Create two columns: Left for Request List, Right for Chat/Upload
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Request List")
    # Fetch all 'Issues' from GitHub - each Issue is an Audit Request
    issues = repo.get_issues(state='open')
    issue_titles = [f"#{i.number}: {i.title}" for i in issues]
    
    if not issue_titles:
        st.info("No open requests found.")
        selected_issue_text = None
    else:
        selected_issue_text = st.radio("Select a request to discuss/upload:", issue_titles)

with col2:
    if selected_issue_text:
        # Extract issue number
        issue_num = int(selected_issue_text.split(":")[0].replace("#", ""))
        current_issue = repo.get_issue(number=issue_num)
        
        st.header(f"Request: {current_issue.title}")
        
        # --- CHAT PART ---
        st.subheader("💬 Discussion")
        # Display existing comments as chat bubbles
        comments = current_issue.get_comments()
        for c in comments:
            with st.chat_message("user" if "client" in c.user.login else "assistant"):
                st.write(f"**{c.user.login}:** {c.body}")

        # Chat Input
        new_msg = st.chat_input("Type your message here (use @client_user to tag)...")
        if new_msg:
            current_issue.create_comment(new_msg)
            st.rerun()

        st.divider()

        # --- UPLOAD PART ---
        st.subheader("📤 Evidence Upload")
        uploaded_file = st.file_uploader("Upload file for this request", type=['pdf', 'xlsx', 'png', 'jpg'])
        
        if uploaded_file:
            file_content = uploaded_file.read()
            file_path = f"evidence/req_{issue_num}/{uploaded_file.name}"
            
            try:
                # Check if file exists to update or create
                repo.create_file(file_path, f"Evidence for #{issue_num}", file_content)
                st.success("File uploaded and committed to GitHub!")
                # Add a comment to the chat automatically
                current_issue.create_comment(f"✅ Evidence uploaded: `{uploaded_file.name}`")
            except Exception as e:
                st.error(f"Error: {e}")
