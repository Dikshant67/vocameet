import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "app_data.db"   # change if you have a different DB name

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ---------- USERS ----------
    users = [
        ("Aarav Sharma", "Male", "1995-06-15", "9999988888", "aarav@example.com", "en", "hi,en", "Mumbai", "400001", "India", "Asia/Kolkata"),
        ("Priya Mehta", "Female", "1993-08-12", "9998877777", "priya@example.com", "en", "en,hi", "Pune", "411001", "India", "Asia/Kolkata"),
    ]
    for u in users:
        cursor.execute("""
        INSERT OR IGNORE INTO users (name, gender, date_of_birth, phone, email, preferred_language, other_languages, city, zip, country, time_zone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, u)

    # ---------- EXPERTS ----------
    experts = [
        ("Dr. Kundan Gaykwad", "Male", "1985-03-10", "Surgeon", "ACTIVE", "9876543210", "kundan@example.com", "https://cal.kundandhayale.com", "en,hi", "Mumbai", "400002", "India", "Asia/Kolkata", 10, 30),
        ("Dr. Rushikesh Lawande", "Male", "1990-11-25", "Dental Care Expert", "ACTIVE", "9876500011", "rushi@example.com", "https://cal.rushi.com", "en", "Bangalore", "560001", "India", "Asia/Kolkata", 5, 45),
    ]
    for e in experts:
        cursor.execute("""
        INSERT OR IGNORE INTO experts (name, gender, date_of_birth, specialty, status, phone, email, calendar_link, other_languages, city, zip, country, time_zone, meeting_buffer_minutes, default_meeting_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, e)

    # ---------- AVAILABILITY ----------
    # Example: Rohan is available Mon-Fri 10 AM - 5 PM, recurring weekly
    rohan_id = cursor.execute("SELECT id FROM experts WHERE email='kundan@example.com'").fetchone()[0]
    sneha_id = cursor.execute("SELECT id FROM experts WHERE email='rushi@example.com'").fetchone()[0]

    for day in range(0, 5):  # Monday to Friday
        cursor.execute("""
        INSERT OR IGNORE INTO expert_availability (expert_id, start_time, end_time, day_of_week, recurring_type, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (
            rohan_id,
            "10:00:00", "17:00:00", day, "weekly"
        ))

    # Sneha available Tue–Sat 09 AM – 3 PM
    for day in range(1, 6):
        cursor.execute("""
        INSERT OR IGNORE INTO expert_availability (expert_id, start_time, end_time, day_of_week, recurring_type, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (
            sneha_id,
            "09:00:00", "15:00:00", day, "weekly"
        ))

    # ---------- UNAVAILABILITY ----------
    # Rohan on leave for 2 days
    leave_start = datetime.now() + timedelta(days=2)
    leave_end = leave_start + timedelta(days=2)
    cursor.execute("""
    INSERT INTO expert_unavailability (expert_id, start_time, end_time, reason, recurring_type)
    VALUES (?, ?, ?, ?, ?)
    """, (rohan_id, leave_start, leave_end, "Personal leave", "none"))

    # Sneha has a weekly break on Sunday
    cursor.execute("""
    INSERT OR IGNORE INTO expert_unavailability (expert_id, start_time, end_time, reason, recurring_type)
    VALUES (?, ?, ?, ?, ?)
    """, (sneha_id, "00:00:00", "23:59:59", "Weekly off", "weekly"))

    # ---------- SAMPLE APPOINTMENTS ----------
    #start = datetime.now() + timedelta(days=1, hours=11)
    #end = start + timedelta(minutes=30)
   # cursor.execute("""
  #  INSERT OR IGNORE INTO appointments (event_id, user_id, expert_id, start_time, end_time, status, purpose, type, location)
    #VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
   # """, (
   #     "EVT001", 1, rohan_id, start, end, "Scheduled", "Career guidance session", "Online", "Google Meet"
  #  ))

    # ---------- COMMIT ----------
    conn.commit()
    conn.close()
    print("✅ Dummy data inserted successfully!")

if __name__ == "__main__":
    seed_data()
