"""Reset user password with new hashing method."""
from app.database.session import engine, SessionLocal
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import text
import getpass

email = input("Enter your email: ")
new_password = getpass.getpass("Enter new password: ")

with SessionLocal() as db:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("User not found!")
    else:
        user.hashed_password = hash_password(new_password)
        db.commit()
        print(f"Password updated for {email}. You can now sign in.")
