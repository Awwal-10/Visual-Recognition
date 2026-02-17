"""
Database Manager - Store and search dual fingerprints
"""

import sqlite3
import numpy as np
from typing import List, Tuple, Optional
from scipy.spatial.distance import cosine
import os


class FingerprintDatabase:
    """Manage fingerprint storage and retrieval"""
    
    def __init__(self, db_path: str = "data/fingerprints.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Media table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER,
                duration REAL,
                filepath TEXT,
                total_frames INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fingerprints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER,
                timestamp REAL,
                frame_index INTEGER,
                phash TEXT NOT NULL,
                cnn_features BLOB,
                FOREIGN KEY (media_id) REFERENCES media(id)
            )
        """)
        
        # Create indexes for fast searching
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phash 
            ON fingerprints(phash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_media_timestamp 
            ON fingerprints(media_id, timestamp)
        """)
        
        self.conn.commit()
        print("✅ Database initialized")
    
    def add_media(
        self, 
        title: str, 
        year: Optional[int] = None,
        filepath: Optional[str] = None,
        duration: Optional[float] = None,
        total_frames: Optional[int] = None
    ) -> int:
        """
        Add a media item to the database
        
        Returns:
            media_id of the inserted item
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO media (title, year, filepath, duration, total_frames)
            VALUES (?, ?, ?, ?, ?)
        """, (title, year, filepath, duration, total_frames))
        
        self.conn.commit()
        media_id = cursor.lastrowid
        
        print(f"✅ Added media: {title} (ID: {media_id})")
        return media_id
    
    def add_fingerprints(
        self, 
        media_id: int, 
        fingerprints: List[Tuple[float, str, np.ndarray]]
    ):
        """
        Add fingerprints for a media item
        
        Args:
            media_id: ID of the media item
            fingerprints: List of (timestamp, phash, cnn_features)
        """
        cursor = self.conn.cursor()
        
        for idx, (timestamp, phash, cnn_features) in enumerate(fingerprints):
            # Convert CNN features to binary blob
            cnn_blob = cnn_features.tobytes()
            
            cursor.execute("""
                INSERT INTO fingerprints 
                (media_id, timestamp, frame_index, phash, cnn_features)
                VALUES (?, ?, ?, ?, ?)
            """, (media_id, timestamp, idx, phash, cnn_blob))
        
        self.conn.commit()
        print(f"✅ Added {len(fingerprints)} fingerprints for media ID {media_id}")
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hex hashes"""
        # Convert hex to binary
        bin1 = bin(int(hash1, 16))[2:].zfill(64)
        bin2 = bin(int(hash2, 16))[2:].zfill(64)
        
        # Count differing bits
        return sum(c1 != c2 for c1, c2 in zip(bin1, bin2))
    
    def search_by_phash(
        self, 
        query_hash: str, 
        max_distance: int = 10,
        limit: int = 50
    ) -> List[Tuple[int, int, float, str, bytes]]:
        """
        Stage 1: Fast pHash search
        
        Args:
            query_hash: Query pHash to search for
            max_distance: Maximum Hamming distance
            limit: Maximum number of results
        
        Returns:
            List of (fingerprint_id, media_id, timestamp, phash, cnn_features_blob)
        """
        cursor = self.conn.cursor()
        
        # Get all fingerprints (we'll filter by Hamming distance in Python)
        # In production, you'd use a more sophisticated index
        cursor.execute("""
            SELECT id, media_id, timestamp, phash, cnn_features
            FROM fingerprints
        """)
        
        results = []
        
        for row in cursor.fetchall():
            fp_id, media_id, timestamp, phash, cnn_blob = row
            distance = self.hamming_distance(query_hash, phash)
            
            if distance <= max_distance:
                results.append((fp_id, media_id, timestamp, phash, cnn_blob))
        
        # Sort by Hamming distance and limit
        results.sort(key=lambda x: self.hamming_distance(query_hash, x[3]))
        return results[:limit]
    
    def verify_with_cnn(
        self,
        candidates: List[Tuple[int, int, float, str, bytes]],
        query_features: np.ndarray
    ) -> List[Tuple[int, str, float, float]]:
        """
        Stage 2: CNN feature verification
        
        Args:
            candidates: Results from Stage 1 pHash search
            query_features: CNN features of query frame
        
        Returns:
            List of (media_id, title, timestamp, similarity_score)
            Sorted by similarity (highest first)
        """
        results = []
        
        cursor = self.conn.cursor()
        
        for fp_id, media_id, timestamp, phash, cnn_blob in candidates:
            # Convert blob back to numpy array
            cnn_features = np.frombuffer(cnn_blob, dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = 1 - cosine(query_features, cnn_features)
            
            # Get media title
            cursor.execute("SELECT title FROM media WHERE id = ?", (media_id,))
            title = cursor.fetchone()[0]
            
            results.append((media_id, title, timestamp, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[3], reverse=True)
        
        return results
    
    def get_stats(self):
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM media")
        media_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fingerprints")
        fingerprint_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Statistics:")
        print(f"   Media items: {media_count}")
        print(f"   Fingerprints: {fingerprint_count}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Test function
if __name__ == "__main__":
    db = FingerprintDatabase()
    db.get_stats()
    db.close()