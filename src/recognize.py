"""
Recognize - Identify media from video clips or images using hybrid matching
"""

import argparse
import os
import sys
import cv2
import numpy as np
from fingerprint_extractor import DualFingerprintExtractor
from database_manager import FingerprintDatabase
from typing import Optional, Dict


class MediaRecognizer:
    """Recognize media using two-stage hybrid matching"""
    
    def __init__(self):
        """Initialize recognizer"""
        self.extractor = DualFingerprintExtractor()
        self.db = FingerprintDatabase()
    
    def recognize_frame(
        self,
        frame: np.ndarray,
        phash_threshold: int = 10,
        cnn_threshold: float = 0.7
    ) -> Optional[Dict]:
        """
        Recognize a single frame using two-stage matching
        
        Args:
            frame: OpenCV frame (BGR format)
            phash_threshold: Maximum Hamming distance for Stage 1
            cnn_threshold: Minimum similarity for Stage 2
        
        Returns:
            Dictionary with match info or None if no match
        """
        print("\n🔍 Analyzing frame...")
        
        # Extract fingerprints from query frame
        print("  📊 Computing pHash...")
        query_phash = self.extractor.compute_phash(frame)
        
        print("  🧠 Computing CNN features...")
        query_cnn = self.extractor.compute_cnn_features(frame)
        
        # STAGE 1: Fast pHash filtering
        print(f"\n⚡ STAGE 1: pHash search (threshold: {phash_threshold})...")
        candidates = self.db.search_by_phash(
            query_phash,
            max_distance=phash_threshold,
            limit=50
        )
        
        print(f"  ✅ Found {len(candidates)} candidates")
        
        if not candidates:
            print("  ❌ No matches found in Stage 1")
            return None
        
        # STAGE 2: CNN verification
        print(f"\n🎯 STAGE 2: CNN verification (threshold: {cnn_threshold})...")
        matches = self.db.verify_with_cnn(candidates, query_cnn)
        
        # Filter by CNN threshold
        valid_matches = [m for m in matches if m[3] >= cnn_threshold]
        
        print(f"  ✅ {len(valid_matches)} matches above threshold")
        
        if not valid_matches:
            print("  ❌ No matches passed CNN verification")
            return None
        
        # Get best match
        best_match = valid_matches[0]
        media_id, title, timestamp, similarity = best_match
        
        return {
            'media_id': media_id,
            'title': title,
            'timestamp': timestamp,
            'similarity': similarity,
            'confidence': similarity * 100,
            'candidates_stage1': len(candidates),
            'candidates_stage2': len(valid_matches)
        }
    
    def recognize_image(
        self,
        image_path: str,
        phash_threshold: int = 10,
        cnn_threshold: float = 0.7
    ) -> Optional[Dict]:
        """
        Recognize media from a screenshot/image
        
        Args:
            image_path: Path to image file
            phash_threshold: Maximum Hamming distance for Stage 1
            cnn_threshold: Minimum similarity for Stage 2
        
        Returns:
            Dictionary with match info or None
        """
        print(f"\n📸 Loading image: {image_path}")
        
        # Load image
        frame = cv2.imread(image_path)
        
        if frame is None:
            print(f"❌ Error: Could not load image: {image_path}")
            return None
        
        print(f"  ✅ Image size: {frame.shape[1]}x{frame.shape[0]}")
        
        # Recognize the frame
        return self.recognize_frame(frame, phash_threshold, cnn_threshold)
    
    def recognize_video(
        self,
        video_path: str,
        sample_frames: int = 5,
        phash_threshold: int = 10,
        cnn_threshold: float = 0.7
    ) -> Optional[Dict]:
        """
        Recognize media from a video clip
        
        Args:
            video_path: Path to video file
            sample_frames: Number of frames to sample and test
            phash_threshold: Maximum Hamming distance for Stage 1
            cnn_threshold: Minimum similarity for Stage 2
        
        Returns:
            Dictionary with match info or None
        """
        print(f"\n🎬 Loading video: {video_path}")
        
        video = cv2.VideoCapture(video_path)
        
        if not video.isOpened():
            print(f"❌ Error: Could not open video: {video_path}")
            return None
        
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps
        
        print(f"  ✅ Video duration: {duration:.1f} seconds")
        print(f"  🎯 Sampling {sample_frames} frames for recognition")
        
        # Sample frames evenly throughout the video
        frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
        
        all_matches = []
        
        for idx, frame_idx in enumerate(frame_indices):
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = video.read()
            
            if not ret:
                continue
            
            timestamp = frame_idx / fps
            print(f"\n--- Frame {idx + 1}/{sample_frames} (at {timestamp:.1f}s) ---")
            
            match = self.recognize_frame(frame, phash_threshold, cnn_threshold)
            
            if match:
                all_matches.append(match)
        
        video.release()
        
        # Aggregate results
        if not all_matches:
            print("\n❌ No matches found in any frame")
            return None
        
        # Vote: most common title wins
        from collections import Counter
        title_votes = Counter(m['title'] for m in all_matches)
        most_common_title = title_votes.most_common(1)[0][0]
        
        # Get best match for that title
        best_match = max(
            [m for m in all_matches if m['title'] == most_common_title],
            key=lambda x: x['similarity']
        )
        
        best_match['votes'] = f"{title_votes[most_common_title]}/{sample_frames}"
        
        return best_match
    
    def print_result(self, result: Optional[Dict]):
        """Print recognition result in a nice format"""
        print("\n" + "="*60)
        
        if result is None:
            print("❌ NO MATCH FOUND")
            print("="*60)
            return
        
        print("✅ MATCH FOUND!")
        print("="*60)
        print(f"🎬 Title: {result['title']}")
        print(f"⏱️  Timestamp: {result['timestamp']:.1f} seconds")
        print(f"🎯 Confidence: {result['confidence']:.1f}%")
        print(f"📊 Similarity Score: {result['similarity']:.3f}")
        
        if 'votes' in result:
            print(f"🗳️  Votes: {result['votes']} frames agreed")
        
        print(f"\n🔍 Stage 1 (pHash): {result['candidates_stage1']} candidates")
        print(f"🎯 Stage 2 (CNN): {result['candidates_stage2']} passed verification")
        print("="*60 + "\n")
    
    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Recognize media from images or video clips"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Path to image file")
    group.add_argument("--video", help="Path to video clip")
    
    parser.add_argument(
        "--phash-threshold",
        type=int,
        default=10,
        help="Maximum Hamming distance for pHash matching (default: 10)"
    )
    
    parser.add_argument(
        "--cnn-threshold",
        type=float,
        default=0.7,
        help="Minimum CNN similarity score (default: 0.7)"
    )
    
    parser.add_argument(
        "--sample-frames",
        type=int,
        default=5,
        help="Number of frames to sample from video (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Initialize recognizer
    recognizer = MediaRecognizer()
    
    # Recognize
    if args.image:
        result = recognizer.recognize_image(
            args.image,
            args.phash_threshold,
            args.cnn_threshold
        )
    else:
        result = recognizer.recognize_video(
            args.video,
            args.sample_frames,
            args.phash_threshold,
            args.cnn_threshold
        )
    
    # Print result
    recognizer.print_result(result)
    recognizer.close()


if __name__ == "__main__":
    main()