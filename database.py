"""
database.py — SQLite persistence layer with user management
"""

import sqlite3
import os
import datetime
import hashlib

DB_PATH = "sers.db"


def get_conn():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_conn()
    
    # Incidents table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            reporter TEXT NOT NULL,
            city TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            confidence REAL NOT NULL,
            priority INTEGER NOT NULL,
            level TEXT NOT NULL,
            unit TEXT NOT NULL,
            eta REAL NOT NULL,
            route TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            dispatched_at TEXT,
            resolved_at TEXT,
            phone TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Insert default users if not exists
    default_users = [
        ("reporter", hashlib.sha256("rep123".encode()).hexdigest(), "Reporter", "Civilian Reporter", "+923001234567"),
        ("operator", hashlib.sha256("op123".encode()).hexdigest(), "Operator", "Emergency Operator", "+923001234568"),
        ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Admin", "System Administrator", "+923001234569"),
    ]
    
    for user in default_users:
        conn.execute("""
            INSERT OR IGNORE INTO users (username, password, role, full_name, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user[0], user[1], user[2], user[3], user[4], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def verify_user(username: str, password: str):
    """Verify user credentials"""
    conn = get_conn()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_username(username: str):
    """Get user by username"""
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(user) if user else None


def insert_incident(reporter, city, description, category, confidence,
                    priority, level, unit, eta, route, phone=None, lat=None, lon=None):
    """Insert new incident"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO incidents
        (timestamp, reporter, city, description, category,
         confidence, priority, level, unit, eta, route, status, phone, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?)
    """, (ts, reporter, city, description, category,
          round(confidence, 2), priority, level, unit, eta, route, phone, lat, lon))
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_all_incidents():
    """Get all incidents"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM incidents ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_incidents_by_reporter(reporter):
    """Get incidents by reporter"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE reporter=? ORDER BY id DESC",
        (reporter,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_pending_incidents():
    """Get pending incidents"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE status='Pending' ORDER BY priority DESC, id DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_status(incident_id, new_status):
    """Update incident status"""
    conn = get_conn()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if new_status == "Dispatched":
        conn.execute(
            "UPDATE incidents SET status=?, dispatched_at=? WHERE id=?",
            (new_status, ts, incident_id)
        )
    elif new_status == "Resolved":
        conn.execute(
            "UPDATE incidents SET status=?, resolved_at=? WHERE id=?",
            (new_status, ts, incident_id)
        )
    else:
        conn.execute(
            "UPDATE incidents SET status=? WHERE id=?",
            (new_status, incident_id)
        )
    conn.commit()
    conn.close()


def get_stats():
    """Get incident statistics"""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Pending'").fetchone()[0]
    dispatched = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Dispatched'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Resolved'").fetchone()[0]
    conn.close()
    return {"total": total, "pending": pending, "dispatched": dispatched, "resolved": resolved}


def get_all_users():
    """Get all users"""
    conn = get_conn()
    rows = conn.execute("SELECT id, username, role, full_name, phone, created_at FROM users").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_user(username, password, role, full_name, phone):
    """Create new user"""
    conn = get_conn()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn.execute("""
            INSERT INTO users (username, password, role, full_name, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, hashed, role, full_name, phone, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def delete_user(user_id):
    """Delete user"""
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()