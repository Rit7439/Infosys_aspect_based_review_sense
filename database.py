import sqlite3
import bcrypt

def get_db_connection():
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            product_name TEXT,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Aspect sentiments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aspects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            aspect TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL NOT NULL,
            keywords TEXT,
            corrected_sentiment TEXT,
            is_corrected INTEGER DEFAULT 0,
            correction_notes TEXT,
            corrected_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews (id)
        )
    ''')
    
    # Active learning corrections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_learning_corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aspect_id INTEGER NOT NULL,
            original_sentiment TEXT NOT NULL,
            corrected_sentiment TEXT NOT NULL,
            confidence REAL NOT NULL,
            review_text TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            corrected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_for_training INTEGER DEFAULT 0,
            FOREIGN KEY (aspect_id) REFERENCES aspects (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            feedback_text TEXT,
            feedback_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Initialize database when imported
init_database()