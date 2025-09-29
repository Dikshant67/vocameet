from datetime import datetime
import sqlite3
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("app-db")
logger.setLevel(logging.INFO)


class AppDatabase:
    def __init__(self, db_path: str = None):
        """Initialize the application database with all tables."""
        if db_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'app_data.db')

        self.db_path = db_path
        self._initialize_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        """Create all tables if they don't exist."""
        conn = self._connect()
        cursor = conn.cursor()

        # Users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            date_of_birth TIMESTAMP,
            phone TEXT ,
            email TEXT ,
            preferred_language TEXT DEFAULT 'en',
            other_languages TEXT,
            city TEXT,
            zip TEXT,
            country TEXT,
            time_zone TEXT,
            last_login_on TIMESTAMP,
            last_logout_on TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
            
        )
        ''')

        # Experts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS experts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            date_of_birth TIMESTAMP,
            specialty TEXT,
            status TEXT DEFAULT 'ACTIVE',
            phone TEXT,
            email TEXT,
            calendar_link TEXT,
            other_languages TEXT,
            city TEXT,
            zip TEXT,
            country TEXT,
            time_zone TEXT,
            last_login_on TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')

        # Appointments
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            event_id TEXT PRIMARY KEY ,
            user_id INTEGER,
            expert_id INTEGER,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'Scheduled',
            purpose TEXT,
            notes TEXT,
            type TEXT,
            location TEXT,
            next_followup_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(expert_id) REFERENCES experts(id)
        )
        ''')

        # Expert Unavailability
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS expert_unavailability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expert_id INTEGER,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            reason TEXT,
            recurring INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(expert_id) REFERENCES experts(id)
        )
        ''')

        # Conversations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transcription TEXT,
            response_text TEXT,
            audio_file_path TEXT,
            sentiment TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')

        # Feedback
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            appointment_id INTEGER,
            rating INTEGER,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(appointment_id) REFERENCES appointments(id)
        )
        ''')
                # Tokens
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sub TEXT NOT NULL, 
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')



        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    # ---------------- USERS ----------------
    def create_user(self, name: str, email: Optional[str] = None, phone: Optional[str] = None) -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, phone) VALUES (?, ?, ?)",
            (name, email, phone),
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    def get_user_by_email(self, email: str) -> int :
        """Fetch a user by their email address."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = cursor.lastrowid
        conn.close()
        return user_id

    def update_user_on_login(self, user_id: int, name: str):
        """Update user's name and last login time."""
        conn = self._connect()
        cursor = conn.cursor()
        now = datetime.utcnow()
        cursor.execute(
            "UPDATE users SET name = ?, last_login_on = ?, updated_at = ? WHERE id = ?",
            (name, now, now, user_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"Updated login time for user_id={user_id}")

    def record_logout(self, email: str):
        """This method is a placeholder as your schema doesn't have a last_logout_time.
           If you add that column, you can implement the update logic here.
           For now, it just logs the action."""
    
        logger.info(f"Logout recorded for user with email: {email}")
        # Example update query if you add the column:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_logout_on = ? WHERE email = ?", (datetime.utcnow(), email))
        conn.commit()
        conn.close()

    # ---------------- EXPERTS ----------------
    def create_expert(self, name: str, specialty: str, email: str) -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO experts (name, specialty, email) VALUES (?, ?, ?)",
            (name, specialty, email),
        )
        expert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return expert_id

    def get_expert(self, expert_id: int) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experts WHERE id = ?", (expert_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ---------------- APPOINTMENTS ----------------
    def create_appointment(self,event_id: str, user_id: int, expert_id: int,title :str, start_time: str,end_time:str) -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (event_id, user_id, expert_id,purpose, start_time, end_time) VALUES (?,?, ?, ?,?,?)",
            (event_id,user_id, expert_id,title,start_time,end_time),
        )
        appt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return appt_id

    def get_appointment(self, appt_id: int) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appt_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    def get_appointments_by_time_and_title(self,start_time: str, end_time: str, title: str):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM appointments
            WHERE start_time = ? AND end_time = ? AND purpose = ?
            """,
            (start_time, end_time, title)
        )
        row=cursor.fetchone()    
        conn.close()
        return dict(row) if row else None
    def cancel_appointment(self, appt_id: int) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE appointments SET status = 'Cancelled' WHERE id = ?", (appt_id,))
            conn.commit()
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()
    
    #-----------------CONVERSATIONS-----------------
    
    def add_transcription(self ,user_id:int,transcription:str)->int:
        conn=self._connect()
        cursor=conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_id,transcription) VALUES (?,?)",(user_id,transcription),)
        conv_id=cursor.execute("select * from conversations where user_id=? ",(user_id,))
        conn.commit()
        conn.close()
        return True if conv_id else False
    def get_transcription(self, user_id: int) -> str:
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT transcription FROM conversations WHERE user_id=?", (user_id,))
        rows = cursor.fetchall()  # returns a list of tuples, e.g., [('text1',), ('text2',)]

        conn.close()

        # Join all transcriptions into a single string
        transcription_text = " ".join(row[0] for row in rows if row[0])
        return transcription_text

        
        
        
    # ---------------- FEEDBACK ----------------
    def create_feedback(self, user_id: int, appointment_id: int, rating: int, comments: str) -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (user_id, appointment_id, rating, comments) VALUES (?, ?, ?, ?)",
            (user_id, appointment_id, rating, comments),
        )
        fb_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return fb_id

    def get_feedback(self, fb_id: int) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback WHERE id = ?", (fb_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    # ---------------- TOKENS ----------------
   # ---------------- TOKENS ----------------
    def store_token(self, user_id: int, sub: str, access_token: str, 
                    refresh_token: Optional[str] = None, token_expiry: Optional[datetime] = None):
        """Insert a new token row."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO tokens (user_id, sub, access_token, refresh_token, token_expiry, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, sub, access_token, refresh_token, token_expiry, datetime.utcnow())
        )
        conn.commit()
        token_id = cursor.lastrowid
        conn.close()
        logger.info(f"Stored new token for sub={sub}, user_id={user_id}")
        return token_id

    def get_token_by_sub(self, sub: str) -> Optional[Dict[str, Any]]:
        """Fetch the most recent token by sub."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            '''SELECT * FROM tokens WHERE sub = ? ORDER BY created_at DESC LIMIT 1''',
            (sub,)
        )
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_tokens_for_user(self, user_id: int):
        """Get all tokens belonging to a user."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tokens WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_tokens_for_user(self, user_id: int) -> int:
        """Delete all tokens for a user. Returns count deleted."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tokens WHERE user_id = ?", (user_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"Deleted {deleted} tokens for user_id={user_id}")
        return deleted