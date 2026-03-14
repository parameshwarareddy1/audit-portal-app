import streamlit as st
import pandas as pd
from github import Github
import io

# --- SETUP ---
st.set_page_config(page_title="AuditCore Pro", layout="wide")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
g = Github(GITHUB_TOKEN)

# --- 1. DASHBOARD: CLIENT SELECTION ---
st.sidebar.title("🏢 Audit Dashboard")
# In a real app, you'd fetch all repos with a specific prefix like 'audit-'
client_repos = ["parameshwarareddy1/client-alpha-2026", "parameshwarareddy1/client-beta-2026"]
selected_client = st.sidebar.selectbox("Select Audit Engagement", client_repos)

repo = g.get_repo(selected_client)

# --- 2. THE "FIELDGUIDE" TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Engagement Overview", "💬 Request Portal", "⚙️ Admin Setup"])

with tab3:
    st.header("Bulk Request Creator")
    st.write("Upload your PBC (Provided by Client) Excel list here.")
    uploaded_excel = st.file_uploader("Upload Excel Request List", type=['xlsx'])
    
    if uploaded_excel:
        df = pd.read_excel(uploaded_excel)
        st.write("Preview of Requests:", df.head())
        if st.button("🚀 Generate All Requests in GitHub"):
            for index, row in df.iterrows():
                # Creates an Issue for every row in your Excel
                repo.create_issue(
                    title=f"{row['ID']}: {row['Request_Name']}",
                    body=f"**Category:** {row['Category']}\n**Description:** {row['Description']}"
                )
            st.success(f"Created {len(df)} requests in the client portal!")

with tab1:
    st.header(f"Status for {selected_client}")
    # Visual metrics like Fieldguide
    open_reqs = repo.get_issues(state='open').totalCount
    st.metric("Pending Client Action", open_reqs)
    # You could add a progress bar here: (Completed / Total)

with tab2:
    st.header("Client Interaction Portal")
    issues = repo.get_issues(state='open')
    
    # List all requests in a table-like view
    for issue in issues:
        with st.expander(f"📌 {issue.title}"):
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.subheader("Discussion")
                for c in issue.get_comments():
                    st.markdown(f"**{c.user.login}**: {c.body}")
                
                chat_msg = st.text_input("Message Client", key=f"msg_{issue.id}")
                if st.button("Send", key=f"btn_{issue.id}"):
                    issue.create_comment(chat_msg)
                    st.rerun()
            
            with c2:
                st.subheader("Evidence")
                file = st.file_uploader("Drop Evidence Here", key=f"file_{issue.id}")
                if file:
                    repo.create_file(f"evidence/{issue.number}/{file.name}", "Upload", file.read())
                    issue.create_comment(f"✅ Uploaded: {file.name}")
                    st.success("Uploaded!")
