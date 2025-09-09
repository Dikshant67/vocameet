from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Expert, Appointment, ExpertUnavailability

DATABASE_URL = "sqlite:///./voice_ai.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_queries():
    db = SessionLocal()

    print("\n=== Users ===")
    for user in db.query(User).all():
        print(f"{user.id}: {user.name}, {user.city}, {user.preferred_language}")

    print("\n=== Experts ===")
    for expert in db.query(Expert).all():
        print(f"{expert.id}: {expert.name}, {expert.specialty}, {expert.city}")

    print("\n=== Appointments ===")
    appointments = db.query(Appointment).all()
    for appt in appointments:
        user = db.query(User).filter(User.id == appt.user_id).first()
        expert = db.query(Expert).filter(Expert.id == appt.expert_id).first()
        print(f"Appt {appt.id}: {user.name} with {expert.name} "
              f"at {appt.appointment_time} | Purpose: {appt.purpose}")

    print("\n=== Expert Unavailability ===")
    for u in db.query(ExpertUnavailability).all():
        expert = db.query(Expert).filter(Expert.id == u.expert_id).first()
        print(f"{expert.name} unavailable from {u.start_time} to {u.end_time} "
              f"Reason: {u.reason}, Recurring: {u.recurring}")

if __name__ == "__main__":
    run_queries()
