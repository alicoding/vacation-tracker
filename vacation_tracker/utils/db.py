import sqlite3
from flask import g, current_app
import os

# Allow the database path to be configured via environment variable
DATABASE = os.environ.get('DATABASE_PATH', 'vacation.db')

def get_db():
    """Get the database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # This enables column access by name
    return db

def close_db(e=None):
    """Close the database connection."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database and perform migrations if needed."""
    db = get_db()
    cursor = db.cursor()
    
    # Check if vacation_days table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vacation_days'")
    if not cursor.fetchone():
        # Create vacation_days table if it doesn't exist
        cursor.execute('''
            CREATE TABLE vacation_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        ''')
    
    # Check if holidays table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='holidays'")
    if not cursor.fetchone():
        # Create holidays table if it doesn't exist
        cursor.execute('''
            CREATE TABLE holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                localName TEXT,
                country_code TEXT DEFAULT 'CA',
                cache_date TEXT NOT NULL,
                is_bank_holiday BOOLEAN DEFAULT 1,
                is_ontario_holiday BOOLEAN DEFAULT 0,
                holiday_source TEXT DEFAULT 'Canadian Bank Holiday'
            )
        ''')
    else:
        # Check for missing columns and add them if needed
        cursor.execute("PRAGMA table_info(holidays)")
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'is_bank_holiday' not in column_names:
            cursor.execute("ALTER TABLE holidays ADD COLUMN is_bank_holiday BOOLEAN DEFAULT 1")
        
        if 'holiday_source' not in column_names:
            cursor.execute("ALTER TABLE holidays ADD COLUMN holiday_source TEXT DEFAULT 'Canadian Bank Holiday'")
            
        if 'is_ontario_holiday' not in column_names:
            cursor.execute("ALTER TABLE holidays ADD COLUMN is_ontario_holiday BOOLEAN DEFAULT 0")
    
    # Future migrations can be added here with additional checks
    
    db.commit()

def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    
    with app.app_context():
        init_db()