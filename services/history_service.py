import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

DB_DIR = Path(__file__).resolve().parent.parent / "database"
DB_PATH = DB_DIR / "history.db"


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection, ensuring the database directory exists."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes tables for QR code history and overall app analytics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qr_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                qr_type TEXT NOT NULL,
                content TEXT NOT NULL,
                format TEXT DEFAULT 'PNG',
                size INTEGER DEFAULT 256,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_stats (
                stat_key TEXT PRIMARY KEY,
                stat_value INTEGER DEFAULT 0
            )
            """
        )
        cursor.execute(
            "INSERT OR IGNORE INTO app_stats (stat_key, stat_value) VALUES ('total_generated', 0)"
        )
        cursor.execute(
            "INSERT OR IGNORE INTO app_stats (stat_key, stat_value) VALUES ('total_downloads', 0)"
        )
        conn.commit()


def log_qr_creation(name: str, qr_type: str, content: str, format_name: str = "PNG", size: int = 256) -> int:
    """Records a generated QR code in history and increments generation count."""
    init_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO qr_history (name, qr_type, content, format, size, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, qr_type, content, format_name, size, now_str),
        )
        new_id = cursor.lastrowid
        cursor.execute(
            "UPDATE app_stats SET stat_value = stat_value + 1 WHERE stat_key = 'total_generated'"
        )
        conn.commit()
        return new_id if new_id is not None else 0


def log_download() -> None:
    """Increments the total download counter."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE app_stats SET stat_value = stat_value + 1 WHERE stat_key = 'total_downloads'"
        )
        conn.commit()


def get_history(search_query: str = "", type_filter: str = "All") -> List[Dict[str, Any]]:
    """Retrieves history records with optional search and type filtering."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM qr_history WHERE 1=1"
        params = []

        if type_filter and type_filter != "All":
            query += " AND qr_type = ?"
            params.append(type_filter)

        if search_query:
            query += " AND (name LIKE ? OR content LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_history_item(record_id: int) -> None:
    """Deletes a specific history record."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qr_history WHERE id = ?", (record_id,))
        conn.commit()


def clear_all_history() -> None:
    """Wipes all historical QR code logs."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qr_history")
        conn.commit()


def get_stats() -> Dict[str, Any]:
    """Returns analytics stats for the dashboard."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stat_key, stat_value FROM app_stats")
        stats_map = {row["stat_key"]: row["stat_value"] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) as total FROM qr_history")
        row = cursor.fetchone()
        history_count = row["total"] if row else 0

        cursor.execute("SELECT qr_type, COUNT(*) as count FROM qr_history GROUP BY qr_type")
        type_breakdown = {row["qr_type"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_generated": stats_map.get("total_generated", history_count),
            "total_downloads": stats_map.get("total_downloads", 0),
            "history_count": history_count,
            "type_breakdown": type_breakdown,
        }

