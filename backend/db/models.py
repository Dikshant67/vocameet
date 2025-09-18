from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gender = Column(String)
    date_of_birth = Column(DateTime)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    preferred_language = Column(String, default="en")
    other_languages = Column(String)
    city = Column(String)
    zip = Column(String)
    country = Column(String)
    time_zone = Column(String)
    last_login_on = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Expert(Base):
    __tablename__ = "experts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gender = Column(String)
    date_of_birth = Column(DateTime)
    specialty = Column(String)
    status = Column(default="ACTIVE")
    phone = Column(String)
    email = Column(String)
    calendar_link = Column(String)
    other_languages = Column(String)
    city = Column(String)
    zip = Column(String)
    country = Column(String)
    time_zone = Column(String)
    last_login_on = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expert_id = Column(Integer, ForeignKey("experts.id"))
    appointment_time = Column(DateTime, nullable=False)
    status = Column(String, default="Scheduled")
    purpose = Column(String)
    notes = Column(Text)
    type = Column(String)
    location = Column(String)
    next_followup_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ExpertUnavailability(Base):
    __tablename__ = "expert_unavailability"
    id = Column(Integer, primary_key=True, index=True)
    expert_id = Column(Integer, ForeignKey("experts.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reason = Column(String)
    recurring = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_text = Column(Text)
    response_text = Column(Text)
    audio_file_path = Column(String)
    sentiment = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    rating = Column(Integer)
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
