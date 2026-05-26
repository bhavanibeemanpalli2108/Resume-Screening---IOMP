import streamlit as st
from datetime import datetime
from database.db import supabase
from database.queries import get_user_resume
from services.resume_service import process_resume
from services.matching_service import compute_match
from core.email_service import send_ats_feedback_email
from core.feedback_service import generate_feedback
from utils.theme import apply_role_theme

# =========================================================
# Session Validation
# =========================================================
if "logged_in" not in st.session_state:
    st.switch_page("pages/1_Login.py")
if st.session_state.get("role") != "candidate":
    st.switch_page("pages/1_Login.py")

apply_role_theme("candidate")
st.title("Candidate Dashboard")

with st.sidebar:
    st.markdown("## AI Recruitment System")
    st.markdown("---")
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("pages/1_Login.py")

user_id = st.session_state["user_id"]

# =========================================================
# 1️⃣ Resume Upload + ATS Score
# =========================================================
st.subheader("Upload / Update Resume")

uploaded_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Processing your resume..."):
        resume_record = process_resume(uploaded_file, user_id)

    if resume_record:
        st.success("Resume uploaded successfully.")

        # Show extracted info
        skills = resume_record.get("skills", [])
        exp = resume_record.get("experience_years")
        projects = resume_record.get("projects", [])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Skills Detected", len(skills))
        with col2:
            st.metric("Experience (years)", exp if exp else "N/A")
        with col3:
            st.metric("Projects Found", len(projects))

        if skills:
            st.markdown("**Detected Skills:** " + " · ".join(
                [f"`{s}`" for s in skills]
            ))
    else:
        st.error("Could not process resume. Please try a different file.")

st.markdown("---")

# =========================================================
# 2️⃣ Available Jobs
# =========================================================
st.subheader("Available Jobs")

jobs_resp = supabase.table("jobs").select("*").execute()
jobs = jobs_resp.data or []
resume = get_user_resume(user_id)

if not jobs:
    st.info("No job postings available yet.")

for job in jobs:
    deadline = None
    if job.get("deadline"):
        try:
            deadline = datetime.fromisoformat(job["deadline"])
        except Exception:
            pass

    if not deadline or deadline <= datetime.now():
        continue

    st.markdown(
        f"""<div class="role-card">
            <h4>{job['title']}</h4>
            <p>{job['description'][:250]}...</p>
            <p><b>Deadline:</b> {deadline.strftime('%d %B %Y')}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    existing = supabase.table("applications") \
        .select("id") \
        .eq("candidate_id", user_id) \
        .eq("job_id", job["id"]) \
        .execute()

    if existing.data:
        st.info("✅ Already applied.")
    else:
        if st.button("Apply", key=f"apply_{job['id']}"):
            if not resume:
                st.error("Please upload your resume first.")
            else:
                with st.spinner("Calculating your ATS score..."):
                    match_result = compute_match(resume, job)
                    score = match_result["composite_score"]

                    # Generate AI feedback for the candidate
                    resume_skills = resume.get("skills") or []
                    job_skills = job.get("skills") or []
                    missing_skills = [s for s in job_skills if s not in resume_skills]
                    outcome = "shortlisted" if score >= 0.65 else "rejected"

                    feedback = generate_feedback(
                        resume_text=resume.get("extracted_text", ""),
                        job_title=job["title"],
                        job_description=job.get("description", ""),
                        score=score,
                        skills_matched=resume_skills,
                        skills_missing=missing_skills,
                        outcome=outcome,
                    )

                # Insert application
                supabase.table("applications").insert({
                    "candidate_id": user_id,
                    "job_id": job["id"],
                    "similarity_score": score,
                    "semantic_score": match_result["semantic_score"],
                    "skill_score": match_result["skill_score"],
                    "project_score": match_result["project_score"],
                    "experience_score": match_result["experience_score"],
                    "status": "applied",
                }).execute()

                # Show ATS score to candidate
                score_pct = round(score * 100, 1)
                if score >= 0.65:
                    st.success(f"Application submitted! Your ATS Score: **{score_pct}%** 🎯")
                else:
                    st.warning(f"Application submitted. Your ATS Score: **{score_pct}%**")

                # Show AI feedback inline
                st.info(f"💡 **AI Feedback:** {feedback}")

                # Send ATS feedback email
                user_resp = supabase.table("users").select("email").eq("id", user_id).execute()
                if user_resp.data:
                    send_ats_feedback_email(
                        to_email=user_resp.data[0]["email"],
                        job_title=job["title"],
                        ats_score=score,
                        feedback=feedback,
                    )

                st.rerun()

    st.markdown("---")

# =========================================================
# 3️⃣ My Applications
# =========================================================
st.subheader("My Applications")

apps_resp = supabase.table("applications").select("*").eq("candidate_id", user_id).execute()
applications = apps_resp.data or []

if not applications:
    st.info("You haven't applied to any jobs yet.")

for app in applications:
    job_resp = supabase.table("jobs").select("title").eq("id", app["job_id"]).execute()
    job_title = job_resp.data[0]["title"] if job_resp.data else "Unknown Job"

    score_pct = round(app["similarity_score"] * 100, 1)
    st.markdown(f"### {job_title}")

    # Score breakdown
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ATS Score", f"{score_pct}%")
    with col2:
        sem = app.get("semantic_score")
        st.metric("Semantic", f"{round((sem or 0)*100,1)}%")
    with col3:
        skl = app.get("skill_score")
        st.metric("Skills", f"{round((skl or 0)*100,1)}%")
    with col4:
        proj = app.get("project_score")
        st.metric("Projects", f"{round((proj or 0)*100,1)}%")

    status = app["status"]
    if status == "shortlisted":
        st.success("✅ Shortlisted")
    elif status == "rejected":
        st.error("❌ Not selected this time")
    else:
        st.warning("⏳ Under Review")

    st.markdown("---")
