"""
Add Media - Process videos and add to fingerprint database
"""

import argparse
import os
import sys
from fingerprint_extractor import DualFingerprintExtractor
from database_manager import FingerprintDatabase


def add_video_to_database(
    video_path: str,
    title: str,
    year: int = None,
    sample_rate: float = 1.0
):
    """
    Process a video and add its fingerprints to the database
    
    Args:
        video_path: Path to video file
        title: Title of the media
        year: Release year (optional)
        sample_rate: Frames per second to sample
    """
    
    # Validate video exists
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found: {video_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🎬 Adding Media to Database")
    print(f"{'='*60}")
    print(f"Title: {title}")
    if year:
        print(f"Year: {year}")
    print(f"Video: {video_path}")
    print(f"Sample Rate: {sample_rate} fps")
    print(f"{'='*60}\n")
    
    # Initialize extractor and database
    print("🔧 Initializing systems...")
    extractor = DualFingerprintExtractor()
    db = FingerprintDatabase()
    
    # Extract fingerprints
    print("\n📹 Extracting fingerprints from video...")
    try:
        fingerprints = extractor.extract_from_video(video_path, sample_rate)
    except Exception as e:
        print(f"❌ Error extracting fingerprints: {e}")
        db.close()
        sys.exit(1)
    
    if not fingerprints:
        print("❌ No fingerprints extracted!")
        db.close()
        sys.exit(1)
    
    # Calculate duration
    duration = fingerprints[-1][0] if fingerprints else 0
    
    # Add media to database
    print("\n💾 Adding to database...")
    media_id = db.add_media(
        title=title,
        year=year,
        filepath=video_path,
        duration=duration,
        total_frames=len(fingerprints)
    )
    
    # Add fingerprints
    db.add_fingerprints(media_id, fingerprints)
    
    # Show statistics
    print("\n" + "="*60)
    print("✅ SUCCESS!")
    print("="*60)
    db.get_stats()
    print("="*60 + "\n")
    
    db.close()


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Add a video to the fingerprint database"
    )
    
    parser.add_argument(
        "--video",
        required=True,
        help="Path to video file"
    )
    
    parser.add_argument(
        "--title",
        required=True,
        help="Title of the media"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        help="Release year (optional)"
    )
    
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=1.0,
        help="Frames per second to sample (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    add_video_to_database(
        video_path=args.video,
        title=args.title,
        year=args.year,
        sample_rate=args.sample_rate
    )


if __name__ == "__main__":
    main()