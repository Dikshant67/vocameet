from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Expert, Appointment, ExpertUnavailability

DATABASE_URL = "sqlite:///./voice_ai.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user1 = User(
        name="Ravi Kumar", gender="Male",
        date_of_birth=datetime(1990, 5, 20),
        phone="9999999999", email="ravi@example.com",
        preferred_language="hi", city="Delhi", zip="110001",
        country="India", time_zone="Asia/Kolkata"
    )
    user2 = User(
        name="Anita Sharma", gender="Female",
        date_of_birth=datetime(1985, 8, 12),
        phone="8888888888", email="anita@example.com",
        preferred_language="en", city="Mumbai", zip="400001",
        country="India", time_zone="Asia/Kolkata"
    )

    expert1 = Expert(
        name="Dr. Meera Joshi", gender="Female",
        date_of_birth=datetime(1975, 4, 15),
        specialty="Psychologist", phone="7777777777",
        email="meera@example.com", calendar_link="https://calendly.com/dr-meera",
        city="Pune", zip="411001", country="India", time_zone="Asia/Kolkata"
    )
    expert2 = Expert(
        name="Dr. Rajeev Singh", gender="Male",
        date_of_birth=datetime(1980, 9, 10),
        specialty="Nutritionist", phone="6666666666",
        email="rajeev@example.com", calendar_link="https://calendly.com/dr-rajeev",
        city="Bangalore", zip="560001", country="India", time_zone="Asia/Kolkata"
    )

    db.add_all([user1, user2, expert1, expert2])
    db.commit()
    db.refresh(user1); db.refresh(user2)
    db.refresh(expert1); db.refresh(expert2)

    appointment1 = Appointment(
        user_id=user1.id, expert_id=expert1.id,
        appointment_time=datetime.now() + timedelta(days=2, hours=10),
        status="Scheduled", purpose="Counseling Session",
        notes="First-time consultation", type="First-time",
        location="https://meet.jit.si/session1",
        next_followup_date=datetime.now() + timedelta(days=30)
    )
    appointment2 = Appointment(
        user_id=user2.id, expert_id=expert2.id,
        appointment_time=datetime.now() + timedelta(days=3, hours=11),
        status="Scheduled", purpose="Diet Consultation",
        notes="Follow-up for weight management", type="Follow-up",
        location="https://meet.jit.si/session2",
        next_followup_date=datetime.now() + timedelta(days=60)
    )

    unavailability1 = ExpertUnavailability(
        expert_id=expert1.id,
        start_time=datetime(2025, 10, 1, 9, 30),
        end_time=datetime(2025, 10, 7, 18, 30),
        reason="Vacation", recurring=0
    )
    unavailability2 = ExpertUnavailability(
        expert_id=expert2.id,
        start_time=datetime(2025, 9, 13, 9, 30),
        end_time=datetime(2025, 9, 13, 18, 30),
        reason="Weekend Block", recurring=1
    )

    db.add_all([appointment1, appointment2, unavailability1, unavailability2])
    db.commit()

    print("✅ Database initialized and sample data inserted successfully!")

if __name__ == "__main__":
    init_db()
