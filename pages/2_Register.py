import streamlit as st
from auth.authentication import register_user
from utils.theme import apply_role_theme

st.set_page_config(page_title="Register — AI Recruitment", page_icon="💼", layout="centered")

apply_role_theme("candidate")

st.title("Register")

email = st.text_input("Email")
password = st.text_input("Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")
role = st.radio("Select Role", ["candidate", "recruiter"])

if st.button("Register"):
    if not email or not password:
        st.error("Email and password are required.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif len(password) < 6:
        st.error("Password must be at least 6 characters.")
    else:
        try:
            response = register_user(email, password, role)
            if response.data:
                st.success("Registration successful. Please login.")
                st.page_link("pages/1_Login.py", label="Go to Login")
            else:
                st.error("Registration failed. Email may already be in use.")
        except Exception as e:
            st.error(f"Registration failed: {e}")

st.markdown("---")
st.markdown("Already have an account? [Login here](1_Login)")
