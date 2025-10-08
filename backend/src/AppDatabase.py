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
        """Establishes the connection with database"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        """Create all database tables if they don't already exist."""
      
        try :
            with self._connect() as conn :
                cursor=conn.cursor()
            # Users
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    gender TEXT,
                    date_of_birth TIMESTAMP,
                    phone TEXT,
                    email TEXT UNIQUE,
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
                            session_guid TEXT UNIQUE,
                            transcription TEXT,
                            response_text TEXT,
                            audio_file_path TEXT,
                            sentiment TEXT,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
              
                logger.info(f"Database initialized at {self.db_path}")
        except :
            logger.critical(f"FATAL: Database initialization failed: ", exc_info=True)

    # ---------------- USERS ----------------
    def create_user(self, name: str, email: Optional[str] = None, phone: Optional[str] = None) -> int:
        """
        Inserts a new user into the database if they do not already exist.

        This function uses 'INSERT OR IGNORE' to prevent duplicates based on unique constraints
        on email or phone number in the table schema.

        Args:
            name: The name of the user.
            email: The user's email address (optional).
            phone: The user's phone number (optional).

        Returns:
            The integer user_id of the newly created user.
            Returns None if the user already exists or if a database error occurs. """
        user_id: Optional[int] = None
        sql = "INSERT OR IGNORE INTO users (name, email, phone) VALUES (?, ?, ?)"
        
        try:
            # The 'with' statement ensures the connection is properly closed
            with self._connect() as conn:
                cursor = conn.cursor()
                logging.info(f"Attempting to create user: {name}")
                
                cursor.execute(sql, (name, email, phone))
                
                # Check if a new row was actually inserted
                if cursor.rowcount > 0:
                    user_id = cursor.lastrowid
                    conn.commit()
                    logging.info(f"Successfully created user '{name}' with ID: {user_id}")
                else:
                    # 'INSERT OR IGNORE' did nothing, meaning the user likely already exists
                    logging.warning(f"User '{name}' with email '{email}' likely already exists. No action taken.")
                    # user_id remains None
                    
        except sqlite3.Error as e:
            # Catch specific database-related errors
            logging.error(f"Database error while creating user '{name}': {e}", exc_info=True)
            # No need to call conn.rollback() as the 'with' statement handles it on error
            return None # Indicate failure
            
        except Exception as e:
            # Catch any other unexpected errors
            logging.error(f"An unexpected error occurred while creating user '{name}': {e}", exc_info=True)
            return None # Indicate failure
            
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
            """
            Fetches a single user by their ID.
    
            Args:
                user_id: The integer ID of the user to fetch.
    
            Returns:
                A dictionary representing the user row if found, otherwise None.
            """
            logger.info(f"Attempting to fetch user with ID: {user_id}")
            try:
                # The 'with' statement handles opening and closing the connection
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                    row = cursor.fetchone()
    
                    if row:
                        logger.info(f"Successfully found user with ID: {user_id}")
                        # 'sqlite3.Row' can be converted to a dict for easy use
                        return dict(row)
                    else:
                        logger.warning(f"User with ID: {user_id} not found.")
                        return None
    
            except sqlite3.Error as e:
                # Log any database-specific errors with a full stack trace
                logger.error(f"Database error while fetching user {user_id}: {e}", exc_info=True)
                return None
            except Exception as e:
                # Catch any other unexpected errors
                logger.error(f"An unexpected error occurred while fetching user {user_id}: {e}", exc_info=True)
                return None
    def get_user_by_email(self, email: str) -> Optional[int]:
            """
            Fetches a user ID by their case-insensitive email address.
    
            Args:
                email: The email address of the user to find.
    
            Returns:
                The integer user_id if found, otherwise None.
            """
            logger.info(f"Attempting to fetch user ID for email: {email}")
            try:
                # The 'with' statement ensures the connection is always closed, even if errors occur.
                with self._connect() as conn:
                    cursor = conn.cursor()
                    # Using LOWER() on both the column and the input is a good way to ensure case-insensitivity.
                    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
                    row = cursor.fetchone()
    
                    if row:
                        user_id = row[0]
                        logger.info(f"Found user with email '{email}'. User ID: {user_id}")
                        return user_id
                    else:
                        logger.warning(f"No user found with email: {email}")
                        return None
    
            except sqlite3.Error as e:
                # Log specific database errors with the full traceback for easier debugging.
                logger.error(f"Database error while fetching user by email '{email}': {e}", exc_info=True)
                return None
            except Exception as e:
                # Catch any other unexpected problems.
                logger.error(f"An unexpected error occurred while fetching user by email '{email}': {e}", exc_info=True)
                return None     
 
    def update_user_on_login(self, user_id: int, name: str) -> None:
            """Update a user's name and last login time in the database.
    
            Args:
                user_id (int): Unique identifier of the user.
                name (str): The user's name.
            """
            query = """
                UPDATE users
                SET name = ?, last_login_on = ?, updated_at = ?
                WHERE id = ?
            """
    
            now = datetime.utcnow()
    
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (name, now, now, user_id))
                    conn.commit()
    
                    if cursor.rowcount == 0:
                        logger.warning(f"No user found with id={user_id} to update.")
                    else:
                        logger.info(f"Updated user (id={user_id}) login time successfully.")
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while updating user (id={user_id}): {e}")
                raise
    
            except Exception as e:
                logger.exception(f"Unexpected error during user update (id={user_id}): {e}")
                raise    


    def record_logout(self, email: str) -> None:
            """Record the user's logout time in the database.
    
            Args:
                email (str): The email address of the user.
            """
            query = """
                UPDATE users
                SET last_logout_on = ?, updated_at = ?
                WHERE email = ?
            """
    
            now = datetime.utcnow()
    
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (now, now, email))
                    conn.commit()
    
                    if cursor.rowcount == 0:
                        logger.warning(f"No user found with email='{email}' to record logout.")
                    else:
                        logger.info(f"Recorded logout for user with email='{email}' successfully.")
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while recording logout for email='{email}': {e}")
                raise
    
            except Exception as e:
                logger.exception(f"Unexpected error during logout record for email='{email}': {e}")
                raise    
    def add_user_gender_and_dob(
            self,
            user_id: int,
            gender: Optional[str] = None,
            age: Optional[int] = None
        ) -> bool:
            """Add or update a user's gender and date of birth.
    
            Args:
                user_id (int): The ID of the user to update or insert.
                gender (Optional[str]): The gender of the user.
                age (Optional[int]): The age of the user, used to calculate date of birth.
    
            Returns:
                bool: True if the operation succeeded, False otherwise.
            """
            now = datetime.utcnow()
            date_of_birth = None
    
            # Derive date of birth if age is provided
            if age is not None:
                current_year = datetime.now().year
                birth_year = current_year - age
                # Approximate DOB as June 1 of the birth year
                date_of_birth = datetime(birth_year, 6, 1)
    
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
    
                    # Check if the user already exists
                    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                    existing_user = cursor.fetchone()
    
                    if not existing_user:
                        # Insert new record
                        cursor.execute(
                            """
                            INSERT INTO users (id, gender, date_of_birth, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (user_id, gender, date_of_birth, now, now),
                        )
                        logger.info(f"Inserted new user record with id={user_id}.")
                    else:
                        # Build dynamic update fields
                        fields, params = [], []
    
                        if gender is not None:
                            fields.append("gender = ?")
                            params.append(gender)
                        if date_of_birth is not None:
                            fields.append("date_of_birth = ?")
                            params.append(date_of_birth)
    
                        if fields:
                            # Add updated_at field
                            fields.append("updated_at = ?")
                            params.append(now)
                            params.append(user_id)
                            query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
                            cursor.execute(query, tuple(params))
                            logger.info(f"Updated user (id={user_id}) gender/DOB successfully.")
                        else:
                            logger.info(f"No updates provided for user id={user_id}.")
    
                    conn.commit()
                    return True
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while adding/updating user (id={user_id}): {e}")
                return False
    
            except Exception as e:
                logger.exception(f"Unexpected error while updating user (id={user_id}): {e}")
                return False
    
    # ---------------- EXPERTS ----------------
    def create_expert(self, name: str, specialty: str, email: str) -> Optional[int]:
            """Create a new expert record in the database.
    
            Args:
                name (str): Expert's full name.
                specialty (str): Expert's area of specialization.
                email (str): Expert's email address.
    
            Returns:
                Optional[int]: The ID of the newly created expert, or None if creation failed.
            """
            query = """
                INSERT INTO experts (name, specialty, email, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """
    
            now = datetime.utcnow()
    
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (name, specialty, email, now, now))
                    expert_id = cursor.lastrowid
                    conn.commit()
    
                    logger.info(f"Expert created successfully (id={expert_id}, email='{email}').")
                    return expert_id
    
            except sqlite3.IntegrityError as e:
                logger.warning(f"Failed to create expert (email='{email}'): duplicate or constraint error. {e}")
                return None
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while creating expert (email='{email}'): {e}")
                return None
    
            except Exception as e:
                logger.exception(f"Unexpected error while creating expert (email='{email}'): {e}")
                return None
    
    
    def get_expert(self, expert_id: int) -> Optional[Dict[str, Any]]:
            """Retrieve an expert's details by their ID.
    
            Args:
                expert_id (int): Unique ID of the expert.
    
            Returns:
                Optional[Dict[str, Any]]: Expert details as a dictionary, or None if not found.
            """
            query = "SELECT * FROM experts WHERE id = ?"
    
            try:
                with self._connect() as conn:
                    # Optional: set row factory to return dict-like rows
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, (expert_id,))
                    row = cursor.fetchone()
    
                    if row:
                        logger.info(f"Expert retrieved successfully (id={expert_id}).")
                        return dict(row)
                    else:
                        logger.warning(f"No expert found with id={expert_id}.")
                        return None
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while retrieving expert (id={expert_id}): {e}")
                return None
    
            except Exception as e:
                logger.exception(f"Unexpected error while retrieving expert (id={expert_id}): {e}")
                return None   
    # ---------------- APPOINTMENTS ----------------
    def create_appointment(
            self,
            event_id: str,
            user_id: int,
            expert_id: int,
            title: str,
            start_time: str,
            end_time: str
        ) -> Optional[int]:
            """Create a new appointment record in the database.
    
            Args:
                event_id (str): External calendar or event identifier.
                user_id (int): ID of the user booking the appointment.
                expert_id (int): ID of the expert the appointment is with.
                title (str): Purpose or title of the appointment.
                start_time (str): Appointment start time (ISO 8601 string recommended).
                end_time (str): Appointment end time (ISO 8601 string recommended).
    
            Returns:
                Optional[int]: The ID of the newly created appointment, or None if creation failed.
            """
            query = """
                INSERT INTO appointments (
                    event_id, user_id, expert_id, purpose, start_time, end_time, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
    
            now = datetime.utcnow()
    
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (event_id, user_id, expert_id, title, start_time, end_time, now, now))
                    appt_id = cursor.lastrowid
                    conn.commit()
    
                    logger.info(
                        f"Appointment created successfully (id={appt_id}, event_id='{event_id}', user_id={user_id}, expert_id={expert_id})."
                    )
                    return appt_id
    
            except sqlite3.IntegrityError as e:
                logger.warning(
                    f"Failed to create appointment (event_id='{event_id}') due to constraint violation: {e}"
                )
                return None
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while creating appointment (event_id='{event_id}'): {e}")
                return None
    
            except Exception as e:
                logger.exception(f"Unexpected error while creating appointment (event_id='{event_id}'): {e}")
                return None

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
    

    def add_transcription_with_guid(self, user_id: int, new_transcription: str, session_guid: str) -> None:
        """
        Add a new transcription to an existing session row or create a new session.
        Appends transcription to existing ones to keep all in a single row.
        """
        try:
            conn = sqlite3.connect(self.db_path)  # Use your DB path
            cursor = conn.cursor()

            # Check if session row exists
            cursor.execute("SELECT transcription FROM conversations WHERE session_guid = ?", (session_guid,))
            row = cursor.fetchone()

            if row:
                # Append to existing transcription, avoid duplicates
                existing_transcription = row[0] or ""
                # Optional: skip if exact transcription already exists
                if new_transcription.strip() not in existing_transcription:
                    updated_transcription = (existing_transcription + " " + new_transcription).strip()
                    cursor.execute("""
                        UPDATE conversations
                        SET transcription = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE session_guid = ?
                    """, (updated_transcription, session_guid))
            else:
                # Insert new row for session
                cursor.execute("""
                    INSERT INTO conversations (user_id, session_guid, transcription)
                    VALUES (?, ?, ?)
                """, (user_id, session_guid, new_transcription))

            conn.commit()
            logger.info(f"Saved transcription to DB (user_id={user_id}, session_guid={session_guid}).")

        except sqlite3.Error as e:
            logger.error(f"SQLite error while adding transcription: {e}")

        finally:
            cursor.close()
            conn.close()


    def get_transcription(self, user_id: int) -> Optional[str]:
            """Retrieve and combine all transcription text for a given user.
    
            Args:
                user_id (int): ID of the user whose transcriptions are being retrieved.
    
            Returns:
                Optional[str]: Combined transcription text, or None if no records exist.
            """
            query = "SELECT transcription FROM conversations WHERE user_id = ? ORDER BY last_updated DESC LIMIT 2"
    
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (user_id,))
                    rows = cursor.fetchall()  # returns a list of tuples, e.g., [('text1',), ('text2',)]
    
                    if not rows:
                        logger.info(f"No transcriptions found for user_id={user_id}.")
                        return None
    
                    # Safely join all non-empty transcription strings
                    transcription_text = " ".join(row[0] for row in rows if row[0])
    
                    logger.info(f"Retrieved and combined transcription for user_id={user_id}.")
                    return transcription_text.strip() if transcription_text else None
    
            except sqlite3.Error as e:
                logger.exception(f"Database error while fetching transcription for user_id={user_id}: {e}")
                return None
    
            except Exception as e:
                logger.exception(f"Unexpected error while retrieving transcription for user_id={user_id}: {e}")
                return None
       

        
        
        
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
    