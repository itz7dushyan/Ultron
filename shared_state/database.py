import sqlite3
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from config import config

logger = logging.getLogger("Ultron.Database")

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured for concurrent WAL access."""
    conn = sqlite3.connect(str(config.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_connection()
    try:
        with conn:
            # 1. Audit / Event Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT,
                    details TEXT,
                    status TEXT NOT NULL
                );
            """)

            # 2. Task Board
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    assigned_agent TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    result TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 3. Key-Value Shared Memory
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at TEXT NOT NULL
                );
            """)
        logger.info("Ultron Database initialized successfully.")
    finally:
        conn.close()

def log_event(agent_name: str, action: str, target: Optional[str] = None, details: Optional[Any] = None, status: str = "success") -> int:
    """Inserts an immutable audit event."""
    conn = get_connection()
    timestamp = datetime.now().isoformat()
    details_str = json.dumps(details) if details is not None and not isinstance(details, str) else str(details or "")
    
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO event_log (timestamp, agent_name, action, target, details, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, agent_name, action, target, details_str, status)
            )
            return cursor.lastrowid
    finally:
        conn.close()

def get_recent_events(limit: int = 25) -> List[Dict[str, Any]]:
    """Retrieves the most recent audit events."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT id, timestamp, agent_name, action, target, details, status
            FROM event_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def create_task(title: str, description: str = "", assigned_agent: str = "Manager") -> int:
    """Creates a new task in the task board."""
    conn = get_connection()
    now = datetime.now().isoformat()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, assigned_agent, status, created_at, updated_at)
                VALUES (?, ?, ?, 'pending', ?, ?)
                """,
                (title, description, assigned_agent, now, now)
            )
            return cursor.lastrowid
    finally:
        conn.close()

def update_task_status(task_id: int, status: str, result: Optional[str] = None):
    """Updates a task's status and outcome."""
    conn = get_connection()
    now = datetime.now().isoformat()
    try:
        with conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, result = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, result, now, task_id)
            )
    finally:
        conn.close()

def get_active_tasks() -> List[Dict[str, Any]]:
    """Returns all currently pending or in-progress tasks."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT id, title, description, assigned_agent, status, result, created_at, updated_at
            FROM tasks
            WHERE status IN ('pending', 'in_progress')
            ORDER BY id ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def set_memory(key: str, value: Any, category: str = "general"):
    """Stores or updates a key-value pair in shared memory."""
    conn = get_connection()
    now = datetime.now().isoformat()
    val_str = json.dumps(value) if not isinstance(value, str) else value
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO memory (key, value, category, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = excluded.updated_at
                """,
                (key, val_str, category, now)
            )
    finally:
        conn.close()

def get_memory(key: str) -> Optional[Any]:
    """Fetches a value from shared memory."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT value FROM memory WHERE key = ?", (key,))
        row = cursor.fetchone()
        if not row:
            return None
        val_str = row["value"]
        try:
            return json.loads(val_str)
        except Exception:
            return val_str
    finally:
        conn.close()

def get_all_memory() -> Dict[str, Any]:
    """Returns a dictionary of all stored memory keys and values."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT key, value FROM memory")
        result = {}
        for row in cursor.fetchall():
            try:
                result[row["key"]] = json.loads(row["value"])
            except Exception:
                result[row["key"]] = row["value"]
        return result
    finally:
        conn.close()

def get_db():
    """Helper returning connection module."""
    return get_connection()
