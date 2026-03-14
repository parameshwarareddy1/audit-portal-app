import streamlit as st
import pandas as pd
from github import Github
import time

# --- MINIMALIST UI CONFIG ---
st.set_page_config(page_title="AuditCore | Minimal", layout="wide")

# CSS for a clean Black & White "Fieldguide" look
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    h1, h2, h3 { border-bottom: 1px solid #000000; padding-bottom: 10px; }
    .stExpander { border: 1px solid #000000 !important; border-radius: 0px !important; }
    .stButton>button { border-radius: 0px; border: 1px solid #000000; background-color: white; color: black; }
    .stButton>button:hover { background-color: #000000; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- GITHUB CONNECTION ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = "parameshwarareddy1/audit-portal-app"
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error("Connect Token to Streamlit Secrets.")
    st.stop()

# --- MAIN APP ---
st.title("AUDIT ENGAGEMENT PORTAL")
st.caption(f"REPOSITORY: {REPO_NAME.upper()}")

tab_portal, tab_admin = st.tabs(["PORTAL", "SETTINGS"])

# --- TAB: ADMIN (UPLOAD) ---
with tab_admin:
    st.subheader("BATCH REQUEST UPLOAD")
    uploaded_excel = st.file_uploader("Upload PBC Excel (Columns: Title, Description)", type=["xlsx"])
    
    if uploaded_excel:
        df = pd.read_excel(uploaded_excel)
        if st.button("SYNC TO GITHUB"):
            with st.spinner("Processing..."):
                for _, row in df.iterrows():
                    repo.create_issue(title=str(row['Title']), body=str(row['Description']))
                st.success("SYNC COMPLETE")
                time.sleep(1) # Wait for GitHub indexing
                st.rerun()

# --- TAB: PORTAL (SEARCH & INTERACTION) ---
with tab_portal:
    # --- SEARCH BAR ---
    search_query = st.text_input("🔍 SEARCH REQUESTS", "").lower()
    
    # Fetch issues
    issues = list(repo.get_issues(state='open'))
    
    # Filter based on search
    filtered_issues = [i for i in issues if search_query in i.title.lower() or search_query in i.body.lower()]

    if not filtered_issues:
        st.info("No matching requests found.")
    else:
        for issue in filtered_issues:
            # Check for evidence markers
            has_evidence = any("✅" in c.body for c in issue.get_comments())
            status_text = "[COMPLETED]" if has_evidence else "[PENDING]"

            with st.expander(f"{status_text} #{issue.number}: {issue.title}"):
                st.text(f"DESCRIPTION: {issue.body}")
                
                c1, c2 = st.columns([2, 1])
                
                with c1:
                    st.markdown("**COMMUNICATION LOG**")
                    for comment in issue.get_comments():
                        st.markdown(f"**{comment.user.login}**: {comment.body}")
                        st.markdown("---")
                    
                    new_msg = st.text_input("Add comment...", key=f"in_{issue.id}")
                    if st.button("SEND", key=f"btn_{issue.id}"):
                        if new_msg:
                            issue.create_comment(new_msg)
                            st.rerun()

                with c2:
                    st.markdown("**EVIDENCE FILING**")
                    file = st.file_uploader("Upload File", key=f"f_{issue.id}")
                    if file:
                        path = f"evidence/req_{issue.number}/{file.name}"
                        repo.create_file(path, f"Audit Evidence", file.read())
                        issue.create_comment(f"✅ Evidence Uploaded: `{file.name}`")
                        st.success("FILE SAVED")
                        st.rerun()
