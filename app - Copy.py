import streamlit as st

st.set_page_config(
    page_title="AI Recruitment System",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
<style>
body { background-color: #f0f7f4; }
.block-container { padding-top: 2rem; }
.card {
    background: white;
    padding: 30px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    text-align: center;
}
.stButton>button {
    background-color: #2e7d32;
    color: white;
    border-radius: 25px;
    padding: 10px 28px;
    font-weight: 600;
    font-size: 16px;
    width: 100%;
}
section[data-testid="stSidebar"] { background-color: white; }
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 💼 AI Recruitment")
    st.markdown("---")
    st.page_link("pages/1_Login.py", label="🔐 Login")
    st.page_link("pages/2_Register.py", label="📝 Register")

# Hero section
st.markdown("""
<div class="card">
    <h1>💼 AI-Powered Resume Screening</h1>
    <p style="font-size:18px; color:#555;">
        Intelligent resume screening using semantic matching, skill extraction,
        and automated candidate ranking.
    </p>
</div>
""", unsafe_allow_html=True)

# Dual-role entry buttons
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <h3>🎓 Candidate</h3>
        <p>Upload your resume, apply to jobs, and track your application status.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Candidate Login", key="candidate_btn"):
        st.switch_page("pages/1_Login.py")

with col2:
    st.markdown("""
    <div class="card">
        <h3>🏢 Recruiter</h3>
        <p>Post jobs, rank candidates by AI score, and shortlist with one click.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Recruiter Login", key="recruiter_btn"):
        st.switch_page("pages/1_Login.py")

# Features section
st.markdown("---")
st.markdown("### How it works")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("**📄 Parse**\nPDF & DOCX resume parsing with layout preservation")
with c2:
    st.markdown("**🧠 Embed**\nSemantic embeddings via sentence-transformers")
with c3:
    st.markdown("**📊 Score**\n40% semantic + 30% skills + 20% projects + 10% experience")
with c4:
    st.markdown("**📧 Notify**\nAutomatic shortlist emails to selected candidates")
