import streamlit as st
from datetime import datetime
from database.db import supabase
from utils.theme import apply_role_theme
from services.job_service import create_job, get_recruiter_jobs
from core.email_service import send_shortlist_email, send_rejection_email
from core.feedback_service import generate_feedback

# =========================================================
# Session Validation
# =========================================================
if "logged_in" not in st.session_state:
    st.switch_page("pages/1_Login.py")
if st.session_state.get("role") != "recruiter":
    st.switch_page("pages/1_Login.py")

apply_role_theme("recruiter")
st.title("Recruiter Dashboard")

with st.sidebar:
    st.markdown("## AI Recruitment System")
    st.markdown("---")
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("pages/1_Login.py")

user_id = st.session_state["user_id"]

# =========================================================
# 1️⃣ Post New Job
# =========================================================
st.subheader("Post New Job")
title = st.text_input("Job Title")
description = st.text_area("Job Description")
deadline = st.date_input("Application Deadline")

if st.button("Create Job"):
    if not title or not description:
        st.error("Job title and description are required.")
    elif deadline <= datetime.now().date():
        st.error("Deadline must be a future date.")
    else:
        create_job(user_id, title, description, deadline)
        st.success("Job created successfully.")
        st.rerun()

st.markdown("---")

# =========================================================
# 2️⃣ Your Posted Jobs
# =========================================================
st.subheader("Your Posted Jobs")
jobs = get_recruiter_jobs(user_id)

if not jobs:
    st.info("You have not posted any jobs yet.")

for job in jobs:
    st.markdown(
        f"""<div class="role-card"><h4>{job['title']}</h4><p>{job['description'][:300]}</p></div>""",
        unsafe_allow_html=True,
    )

    if job.get("deadline"):
        try:
            st.write(f"Deadline: {datetime.fromisoformat(job['deadline']).strftime('%d %B %Y')}")
        except Exception:
            pass

    # Fetch applications
    apps_resp = (
        supabase.table("applications")
        .select("*")
        .eq("job_id", job["id"])
        .order("similarity_score", desc=True)
        .execute()
    )
    applications = apps_resp.data or []

    st.write(f"Total Applicants: {len(applications)}")
    if applications:
        avg = sum(a["similarity_score"] for a in applications) / len(applications)
        st.write(f"Average Match Score: {round(avg * 100, 1)}%")

    # =========================================================
    # Threshold Auto-Shortlist
    # =========================================================
    st.markdown("#### Auto-Shortlist by Threshold")
    threshold_key = f"threshold_{job['id']}"
    threshold = st.slider(
        "Shortlist candidates scoring above (%)",
        min_value=0, max_value=100, value=65, step=5,
        key=threshold_key,
    )
    threshold_val = threshold / 100.0

    pending = [a for a in applications if a["status"] == "applied"]
    above = [a for a in pending if a["similarity_score"] >= threshold_val]
    below = [a for a in pending if a["similarity_score"] < threshold_val]

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption(f"✅ Will shortlist: {len(above)} candidates")
    with col_b:
        st.caption(f"❌ Will reject: {len(below)} candidates")

    if st.button(f"Run Auto-Shortlist", key=f"auto_{job['id']}"):
        shortlisted_count = 0
        rejected_count = 0
        failed_emails = []

        for app in above:
            # Update status
            supabase.table("applications").update({"status": "shortlisted"}).eq("id", app["id"]).execute()

            # Fetch candidate info
            user_resp = supabase.table("users").select("email").eq("id", app["candidate_id"]).execute()
            resume_resp = supabase.table("resumes").select("extracted_text, skills").eq("user_id", app["candidate_id"]).execute()

            candidate_email = user_resp.data[0]["email"] if user_resp.data else None
            resume_data = resume_resp.data[0] if resume_resp.data else {}
            resume_text = resume_data.get("extracted_text", "")
            resume_skills = resume_data.get("skills") or []
            job_skills = job.get("skills") or []
            missing_skills = [s for s in job_skills if s not in resume_skills]

            # Generate AI feedback
            feedback = generate_feedback(
                resume_text=resume_text,
                job_title=job["title"],
                job_description=job.get("description", ""),
                score=app["similarity_score"],
                skills_matched=resume_skills,
                skills_missing=missing_skills,
                outcome="shortlisted",
            )

            if candidate_email:
                sent = send_shortlist_email(candidate_email, job["title"], feedback=feedback)
                if not sent:
                    failed_emails.append(candidate_email)
            shortlisted_count += 1

        for app in below:
            supabase.table("applications").update({"status": "rejected"}).eq("id", app["id"]).execute()

            user_resp = supabase.table("users").select("email").eq("id", app["candidate_id"]).execute()
            resume_resp = supabase.table("resumes").select("extracted_text, skills").eq("user_id", app["candidate_id"]).execute()

            candidate_email = user_resp.data[0]["email"] if user_resp.data else None
            resume_data = resume_resp.data[0] if resume_resp.data else {}
            resume_text = resume_data.get("extracted_text", "")
            resume_skills = resume_data.get("skills") or []
            job_skills = job.get("skills") or []
            missing_skills = [s for s in job_skills if s not in resume_skills]

            feedback = generate_feedback(
                resume_text=resume_text,
                job_title=job["title"],
                job_description=job.get("description", ""),
                score=app["similarity_score"],
                skills_matched=resume_skills,
                skills_missing=missing_skills,
                outcome="rejected",
            )

            if candidate_email:
                sent = send_rejection_email(candidate_email, job["title"], feedback=feedback)
                if not sent:
                    failed_emails.append(candidate_email)
            rejected_count += 1

        st.success(f"Done! Shortlisted: {shortlisted_count} | Rejected: {rejected_count}")
        if failed_emails:
            st.warning(f"Email failed for: {', '.join(failed_emails)}")
        st.rerun()

    st.markdown("---")

    # =========================================================
    # Individual Applicants
    # =========================================================
    for app in applications:
        user_resp = supabase.table("users").select("email").eq("id", app["candidate_id"]).execute()
        user_data = user_resp.data[0] if user_resp.data else None

        resume_resp = supabase.table("resumes").select("file_path").eq("user_id", app["candidate_id"]).execute()
        resume_data = resume_resp.data[0] if resume_resp.data else None

        col1, col2 = st.columns([3, 1])
        score_pct = round(app["similarity_score"] * 100, 1)

        with col1:
            st.markdown(
                f"""<div class="role-card">
                    <h4>{user_data['email'] if user_data else 'Unknown'}</h4>
                    <p><b>ATS Score:</b> {score_pct}%</p>
                </div>""",
                unsafe_allow_html=True,
            )
            status = app["status"]
            if status == "shortlisted":
                st.success("✅ Shortlisted")
            elif status == "rejected":
                st.error("❌ Rejected")
            else:
                st.warning("⏳ Applied")

        with col2:
            if resume_data and resume_data.get("file_path"):
                signed = supabase.storage.from_("resumes").create_signed_url(str(resume_data["file_path"]), 120)
                if signed and "signedURL" in signed:
                    st.markdown(f"[View Resume]({signed['signedURL']})")
            else:
                st.caption("No resume file.")

            if app["status"] == "applied":
                if st.button("Shortlist", key=f"shortlist_{app['id']}"):
                    supabase.table("applications").update({"status": "shortlisted"}).eq("id", app["id"]).execute()
                    if user_data:
                        send_shortlist_email(user_data["email"], job["title"])
                    st.success("Shortlisted.")
                    st.rerun()

        st.markdown("---")

    st.markdown("___")
