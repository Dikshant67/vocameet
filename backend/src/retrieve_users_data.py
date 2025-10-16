# check_db.py
from main import SessionLocal, User

def query_users():
    db = SessionLocal()
    print("--- Querying all users in the database ---")
    try:
        all_users = db.query(User).all()
        if not all_users:
            print("No users found in the database.")
            return

        for user in all_users:
            print(f"\nUser ID: {user.id}, Email: {user.email}, Name: {user.name}")
            print(f"  -> Last Login: {user.last_login_time}")
            print(f"  -> Last Logout: {user.last_logout_time}")
            print(f"  -> Created At: {user.created_at}")
            print(f"  -> Picture URL: {user.picture}\n")
            print("-"*40)
    finally:
        db.close()
        print("\n--- Query finished ---")

if __name__ == "__main__":
    query_users()