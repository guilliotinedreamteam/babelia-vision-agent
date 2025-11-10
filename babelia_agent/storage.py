"""
Storage Manager

Manages saved images and discovery database.
"""

import os
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from PIL import Image

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages storage of discovered images and metadata"""
    
    def __init__(self, save_dir: str = './discoveries', db_path: str = './babelia_discoveries.db'):
        """
        Initialize storage manager
        
        Args:
            save_dir: Directory to save images
            db_path: Path to SQLite database
        """
        self.save_dir = Path(save_dir)
        self.db_path = db_path
        
        # Create directories
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Storage initialized (dir: {save_dir}, db: {db_path})")
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    score REAL NOT NULL,
                    hex_name TEXT NOT NULL,
                    wall TEXT,
                    shelf TEXT,
                    volume TEXT,
                    page TEXT,
                    reason TEXT,
                    image_path TEXT NOT NULL,
                    analysis_json TEXT,
                    UNIQUE(hex_name, wall, shelf, volume, page)
                )
            """)
            conn.commit()
    
    def save_discovery(self, image: Image.Image, score: float,
                      analysis: Dict[str, Any], coordinates: Dict[str, str]) -> str:
        """
        Save discovered image and metadata
        
        Args:
            image: PIL Image
            score: Significance score
            analysis: Analysis results
            coordinates: Babelia coordinates
        
        Returns:
            Path to saved image
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_score{score:.3f}.jpg"
        image_path = self.save_dir / filename
        
        # Save image
        image.save(image_path, 'JPEG', quality=95)
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO discoveries 
                    (timestamp, score, hex_name, wall, shelf, volume, page, 
                     reason, image_path, analysis_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    score,
                    coordinates['hex_name'],
                    coordinates['wall'],
                    coordinates['shelf'],
                    coordinates['volume'],
                    coordinates['page'],
                    analysis.get('reason', 'unknown'),
                    str(image_path),
                    json.dumps(analysis)
                ))
                conn.commit()
            except sqlite3.IntegrityError:
                logger.warning("Duplicate discovery, skipping database insert")
        
        return str(image_path)
    
    def get_discovery_count(self) -> int:
        """Get total number of discoveries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM discoveries")
            return cursor.fetchone()[0]
    
    def get_top_discoveries(self, limit: int = 10) -> list:
        """Get top discoveries by score"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, score, hex_name, reason, image_path
                FROM discoveries
                ORDER BY score DESC
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()
    
    def close(self):
        """Cleanup resources"""
        # SQLite connections are closed automatically
        pass