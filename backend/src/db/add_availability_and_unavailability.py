import sqlite3
from datetime import datetime, timedelta

DB_PATH = "app_data.db"  # Change if your DB name/path is different

def seed_availability_unavailability():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ---------- Fetch expert IDs ----------
    rohan_id = cursor.execute("SELECT id FROM experts WHERE email='rohan@example.com'").fetchone()
    sneha_id = cursor.execute("SELECT id FROM experts WHERE email='sneha@example.com'").fetchone()

    if not rohan_id or not sneha_id:
        print("❌ Experts not found. Make sure they are seeded first.")
        conn.close()
        return

    rohan_id = rohan_id[0]
    sneha_id = sneha_id[0]

    # ---------- AVAILABILITY ----------

    # Rohan: Monday-Friday 10:00-17:00, weekly
    for day in range(0, 5):  # 0=Monday, 4=Friday
        cursor.execute("""
        INSERT OR IGNORE INTO expert_availability (expert_id, start_time, end_time, day_of_week, recurring_type, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (rohan_id, "10:00:00", "17:00:00", day, "weekly"))

    # Sneha: Tuesday-Saturday 09:00-15:00, weekly
    for day in range(1, 6):  # 1=Tuesday, 5=Saturday
        cursor.execute("""
        INSERT OR IGNORE INTO expert_availability (expert_id, start_time, end_time, day_of_week, recurring_type, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (sneha_id, "09:00:00", "15:00:00", day, "weekly"))

    # ---------- UNAVAILABILITY ----------

    # Rohan: Personal leave for 2 days starting 2 days from now
    leave_start = datetime.now() + timedelta(days=2)
    leave_end = leave_start + timedelta(days=2)
    cursor.execute("""
    Delete from expert_availability where expert_id=1
   
    """)

    # Sneha: Weekly off on Sunday
    cursor.execute("""
    Delete from expert_availability where expert_id=2
    """)

    conn.commit()
    conn.close()
    print("✅ Expert availability and unavailability seeded successfully!")

if __name__ == "__main__":
    seed_availability_unavailability()
