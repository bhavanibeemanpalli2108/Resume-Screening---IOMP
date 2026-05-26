import streamlit as st
from auth.authentication import login_user
from utils.theme import apply_role_theme

st.set_page_config(page_title="Login — AI Recruitment", page_icon="💼", layout="centered")

apply_role_theme("candidate")

st.title("Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if not email or not password:
        st.error("Please enter your email and password.")
    else:
        user = login_user(email, password)
        if user:
            st.session_state["user_id"] = user["id"]
            st.session_state["role"] = user["role"]
            st.session_state["logged_in"] = True

            if user["role"] == "candidate":
                st.switch_page("pages/3_Candidate_Dashboard.py")
            elif user["role"] == "recruiter":
                st.switch_page("pages/4_Recruiter_Dashboard.py")
        else:
            st.error("Invalid credentials.")

st.markdown("---")
st.markdown("Don't have an account? [Register here](2_Register)")
