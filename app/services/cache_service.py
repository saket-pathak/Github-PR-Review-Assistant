import sqlite3
import json
from typing import List, Dict, Any, Optional

class ReviewCache:
    def __init__(self, db_path: str = ".review_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_reviews (
                        diff_hash TEXT PRIMARY KEY,
                        comments TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS reviews_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        repo TEXT NOT NULL,
                        pr_number INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        summary TEXT,
                        comments_posted INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception:
            # Failsafe if unable to initialize database in read-only or restricted environments
            pass

    def get_comments(self, diff_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves cached comments for a given diff hash.
        Returns None if not cached.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT comments FROM file_reviews WHERE diff_hash = ?",
                    (diff_hash,)
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception:
            # Fallback/ignore if database is locked or corrupted
            pass
        return None

    def set_comments(self, diff_hash: str, comments: List[Dict[str, Any]]):
        """
        Caches comments for a given diff hash.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO file_reviews (diff_hash, comments) VALUES (?, ?)",
                    (diff_hash, json.dumps(comments))
                )
                conn.commit()
        except Exception:
            # Ignore caching errors (failsafe design)
            pass

    def add_review_to_history(
        self,
        platform: str,
        repo: str,
        pr_number: int,
        status: str,
        summary: str,
        comments_posted: int
    ):
        """
        Logs a pull request review execution run.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO reviews_history (platform, repo, pr_number, status, summary, comments_posted)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (platform, repo, pr_number, status, summary, comments_posted)
                )
                conn.commit()
        except Exception:
            pass

    def get_reviews_history(self) -> List[Dict[str, Any]]:
        """
        Retrieves all pull request reviews logged in history, ordered newest first.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT id, platform, repo, pr_number, status, summary, comments_posted, created_at FROM reviews_history ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_review_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single review history record by ID.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, platform, repo, pr_number, status, summary, comments_posted, created_at FROM reviews_history WHERE id = ?",
                    (review_id,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception:
            pass
        return None
