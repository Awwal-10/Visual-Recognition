"""
Visual Media Recognizer - Core SDK
Clean interface wrapping the hybrid pHash + CNN pipeline
"""

import time
import cv2
import numpy as np
from typing import Optional
from collections import Counter

# Import from your existing src/ (we'll refactor later)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fingerprint_extractor import DualFingerprintExtractor
from database_manager import FingerprintDatabase as _DB
from models import RecognitionResult, MatchType


def _get_match_type(similarity: float) -> MatchType:
    """Convert similarity score to match type label"""
    if similarity >= 0.95:
        return MatchType.STRONG
    elif similarity >= 0.80:
        return MatchType.PROBABLE
    elif similarity >= 0.70:
        return MatchType.WEAK
    return MatchType.NONE


class VisualRecognizer:
    """
    Identify movies and TV shows from video clips or screenshots.
    
    Uses a two-stage hybrid pipeline:
    - Stage 1: Perceptual hash (pHash) for fast candidate filtering
    - Stage 2: CNN features (EfficientNet) for accurate verification
    
    Example:
        from visrec import VisualRecognizer, FingerprintDB
        
        db = FingerprintDB("movies.db")
        recognizer = VisualRecognizer(db)
        
        result = recognizer.identify("tiktok_clip.mp4")
        print(result.title)  # "The Dictator"
    """
    
    def __init__(
        self,
        db_path: str = "data/fingerprints.db",
        phash_threshold: int = 15,
        cnn_threshold: float = 0.6
    ):
        """
        Initialize the recognizer.
        
        Args:
            db_path: Path to SQLite fingerprint database
            phash_threshold: Hamming distance threshold for Stage 1 (lower = stricter)
            cnn_threshold: Cosine similarity threshold for Stage 2 (higher = stricter)
        """
        self.db = _DB(db_path)
        self.extractor = DualFingerprintExtractor()
        self.phash_threshold = phash_threshold
        self.cnn_threshold = cnn_threshold
    
    def identify(
        self,
        path: str,
        sample_frames: int = 5
    ) -> RecognitionResult:
        """
        Identify the source media from a video clip or image.
        
        Args:
            path: Path to video file or image
            sample_frames: Number of frames to sample (video only)
        
        Returns:
            RecognitionResult with match details
        """
        start_time = time.time()
        
        # Detect if image or video
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        ext = os.path.splitext(path)[1].lower()
        
        if ext in image_extensions:
            result = self._identify_image(path)
        else:
            result = self._identify_video(path, sample_frames)
        
        # Add processing time
        result.processing_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _identify_image(self, image_path: str) -> RecognitionResult:
        """Identify from a single image/screenshot"""
        frame = cv2.imread(image_path)
        
        if frame is None:
            return RecognitionResult(matched=False)
        
        match = self._match_frame(frame)
        
        if not match:
            return RecognitionResult(matched=False, frames_sampled=1, frames_matched=0)
        
        media_id, title, timestamp, similarity = match
        year = self._get_year(media_id)
        
        return RecognitionResult(
            matched=True,
            title=title,
            year=year,
            timestamp=timestamp,
            confidence=similarity,
            match_type=_get_match_type(similarity),
            frames_sampled=1,
            frames_matched=1
        )
    
    def _identify_video(self, video_path: str, sample_frames: int) -> RecognitionResult:
        """Identify from a video clip by sampling multiple frames"""
        video = cv2.VideoCapture(video_path)
        
        if not video.isOpened():
            return RecognitionResult(matched=False)
        
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        
        # Sample frames evenly
        frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
        
        all_matches = []
        total_stage1 = 0
        total_stage2 = 0
        
        for frame_idx in frame_indices:
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = video.read()
            
            if not ret:
                continue
            
            match = self._match_frame(frame)
            
            if match:
                media_id, title, timestamp, similarity = match
                all_matches.append((media_id, title, timestamp, similarity))
                total_stage2 += 1
        
        video.release()
        
        if not all_matches:
            return RecognitionResult(
                matched=False,
                frames_sampled=sample_frames,
                frames_matched=0
            )
        
        # Vote: most common title wins
        title_votes = Counter(m[1] for m in all_matches)
        winning_title = title_votes.most_common(1)[0][0]
        
        # Best match for winning title
        title_matches = [m for m in all_matches if m[1] == winning_title]
        best = max(title_matches, key=lambda x: x[3])
        media_id, title, timestamp, similarity = best
        
        year = self._get_year(media_id)
        
        return RecognitionResult(
            matched=True,
            title=title,
            year=year,
            timestamp=timestamp,
            confidence=similarity,
            match_type=_get_match_type(similarity),
            frames_sampled=sample_frames,
            frames_matched=len(all_matches),
            stage1_candidates=total_stage1,
            stage2_candidates=total_stage2
        )
    
    def _match_frame(self, frame: np.ndarray):
        """Run two-stage matching on a single frame"""
        # Extract fingerprints
        phash = self.extractor.compute_phash(frame)
        cnn_features = self.extractor.compute_cnn_features(frame)
        
        # Stage 1: pHash filter
        candidates = self.db.search_by_phash(
            phash,
            max_distance=self.phash_threshold,
            limit=50
        )
        
        if not candidates:
            return None
        
        # Stage 2: CNN verification
        matches = self.db.verify_with_cnn(candidates, cnn_features)
        valid = [m for m in matches if m[3] >= self.cnn_threshold]
        
        if not valid:
            return None
        
        return valid[0]  # Best match
    
    def _get_year(self, media_id: int) -> Optional[int]:
        """Get year for a media item"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT year FROM media WHERE id = ?", (media_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def close(self):
        """Release resources"""
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()