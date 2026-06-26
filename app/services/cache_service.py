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
