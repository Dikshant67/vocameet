# src/seed_db.py

from datetime import datetime
import logging

# We import the database session factory and the User model from your main application file
from main import SessionLocal, User

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- DEFINE YOUR DUMMY DATA HERE ---
# You can add as many users as you want to this list.
DUMMY_USERS = [
    {
        "name": "Alice Wonderland",
        "email": "alice.w@example.com",
        "picture": "https://i.pravatar.cc/150?u=alice.w@example.com",
    },
    {
        "name": "Bob Builder",
        "email": "bob.b@example.com",
        "picture": "https://i.pravatar.cc/150?u=bob.b@example.com",
    },
    {
        "name": "Charlie Chocolate",
        "email": "charlie.c@example.com",
        "picture": "https://i.pravatar.cc/150?u=charlie.c@example.com",
    },
    {
        # This user will have a logout time for demonstration
        "name": "Diana Prince",
        "email": "diana.p@example.com",
        "picture": "https://i.pravatar.cc/150?u=diana.p@example.com",
        "logout_time": datetime(2025, 9, 12, 10, 30, 0) # Example logout time
    }
]

def seed_database():
    """
    Populates the database with dummy user data.
    Checks if a user already exists before adding to prevent duplicates.
    """
    logger.info("--- Starting database seeding ---")
    db = SessionLocal()

    try:
        for user_data in DUMMY_USERS:
            # Check if a user with this email already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()

            if existing_user:
                logger.info(f"User with email '{user_data['email']}' already exists. Skipping.")
                continue

            # Create a new User object from the dummy data
            new_user = User(
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data["picture"],
                last_login_time=datetime.utcnow(),
                last_logout_time=user_data.get("logout_time") # Will be None if not provided
            )

            # Add the new user to the session
            db.add(new_user)
            logger.info(f"Staged new user for creation: {user_data['name']}")

        # Commit all the staged users to the database
        db.commit()
        logger.info("\n--- Database seeding complete! ---")

    except Exception as e:
        logger.error(f"An error occurred during seeding: {e}")
        db.rollback()  # Roll back the changes if an error occurs
    finally:
        db.close()  # Always close the session

if __name__ == "__main__":
    seed_database()