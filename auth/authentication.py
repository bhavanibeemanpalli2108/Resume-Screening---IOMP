from database.db import supabase
from auth.password_utils import hash_password, verify_password

def register_user(email, password, role):
    hashed = hash_password(password)

    response = supabase.table("users").insert({
        "email": email,
        "password": hashed,
        "role": role
    }).execute()

    return response

def login_user(email, password):
    response = supabase.table("users").select("*").eq("email", email).execute()

    if not response.data:
        return None

    user = response.data[0]

    if verify_password(password, user["password"]):
        return user

    return None