"""Database module for tracking uploaded videos."""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class VideoDatabase:
    """SQLite database for tracking uploaded videos."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                topic TEXT,
                tags TEXT,
                file_path TEXT,
                content_hash TEXT UNIQUE,
                bottube_id TEXT,
                upload_status TEXT DEFAULT 'pending',
                uploaded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_content_hash ON videos(content_hash)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_upload_status ON videos(upload_status)
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_content_hash(self, title: str, topic: str, caption: str) -> str:
        """Generate a hash for content deduplication."""
        content = f"{title}|{topic}|{caption}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def video_exists(self, content_hash: str) -> bool:
        """Check if a video with this content hash already exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM videos WHERE content_hash = ?',
            (content_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def add_video(
        self,
        title: str,
        topic: str,
        content_hash: str,
        description: str = '',
        tags: str = '',
        file_path: str = ''
    ) -> int:
        """Add a new video record."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO videos (title, description, topic, tags, file_path, content_hash, upload_status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (title, description, topic, tags, file_path, content_hash))
        
        video_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return video_id
    
    def mark_uploaded(
        self,
        video_id: int,
        bottube_id: str,
        file_path: str = ''
    ) -> None:
        """Mark a video as successfully uploaded."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE videos 
            SET upload_status = 'uploaded',
                bottube_id = ?,
                file_path = COALESCE(NULLIF(?, ''), file_path),
                uploaded_at = ?
            WHERE id = ?
        ''', (bottube_id, file_path, datetime.now().isoformat(), video_id))
        
        conn.commit()
        conn.close()
    
    def mark_failed(self, video_id: int, error_message: str) -> None:
        """Mark a video upload as failed."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE videos 
            SET upload_status = 'failed',
                error_message = ?
            WHERE id = ?
        ''', (error_message, video_id))
        
        conn.commit()
        conn.close()
    
    def get_pending_videos(self) -> List[Dict[str, Any]]:
        """Get all videos pending upload."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM videos 
            WHERE upload_status = 'pending'
            ORDER BY created_at ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_uploads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent successfully uploaded videos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM videos 
            WHERE upload_status = 'uploaded'
            ORDER BY uploaded_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict[str, int]:
        """Get upload statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN upload_status = 'uploaded' THEN 1 ELSE 0 END) as uploaded,
                SUM(CASE WHEN upload_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN upload_status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM videos
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else {'total': 0, 'uploaded': 0, 'pending': 0, 'failed': 0}
