import streamlit as st

def require_login():
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.error("Please login first.")
        st.stop()

def require_role(role):
    if st.session_state.get("role") != role:
        st.error("Unauthorized access.")
        st.stop()