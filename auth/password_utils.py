import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()  # generate a random salt
    hashed = bcrypt.hashpw(password.encode(), salt)  # hash password with salt
    return hashed.decode()  # return hashed password as string


def verify_password(password: str, hashed_password: str) -> bool:
    # compare input password with stored hashed password
    return bcrypt.checkpw(password.encode(), hashed_password.encode())