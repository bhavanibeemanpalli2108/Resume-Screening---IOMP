import streamlit as st

def apply_role_theme(role):

    if role == "candidate":
        primary = "#2e7d32"      # Green
        background = "#f0f7f4"
        badge_color = "#2e7d32"
        role_label = "Candidate Portal"

    elif role == "recruiter":
        primary = "#0a66c2"      # LinkedIn Blue
        background = "#eef3f8"
        badge_color = "#0a66c2"
        role_label = "Recruiter Portal"

    else:
        primary = "#333333"
        background = "#ffffff"
        badge_color = "#333333"
        role_label = "Portal"

    st.markdown(f"""
    <style>

    body {{
        background-color: {background};
    }}

    .block-container {{
        padding-top: 1rem;
    }}

    /* Top header strip */
    .role-header {{
        background-color: {primary};
        padding: 15px 25px;
        border-radius: 10px;
        color: white;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    /* Role badge */
    .role-badge {{
        background-color: white;
        color: {badge_color};
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }}

    /* Cards */
    .role-card {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: {primary};
        color: white;
        border-radius: 20px;
        padding: 8px 22px;
        font-weight: 600;
        border: none;
    }}

    section[data-testid="stSidebar"] {{
        background-color: white;
    }}

    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="role-header">
        <div>{role_label}</div>
        <div class="role-badge">{role.upper()}</div>
    </div>
    """, unsafe_allow_html=True)