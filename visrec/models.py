"""
Data models for Visual Recognition SDK
Clean, typed interfaces for all results
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class MatchType(str, Enum):
    """Confidence level of a recognition match"""
    STRONG   = "strong"    # similarity >= 0.95
    PROBABLE = "probable"  # similarity >= 0.80
    WEAK     = "weak"      # similarity >= 0.70
    NONE     = "none"      # no match found


@dataclass
class RecognitionResult:
    """Result from a recognition query"""
    
    matched: bool
    title: Optional[str] = None
    year: Optional[int] = None
    timestamp: Optional[float] = None
    confidence: Optional[float] = None
    match_type: MatchType = MatchType.NONE
    processing_time_ms: Optional[float] = None
    
    # Debug info
    stage1_candidates: int = 0
    stage2_candidates: int = 0
    frames_sampled: int = 0
    frames_matched: int = 0

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "matched": bool(self.matched),
            "title": self.title,
            "year": self.year,
            "timestamp": float(self.timestamp) if self.timestamp is not None else None,
            "confidence": round(float(self.confidence), 4) if self.confidence is not None else None,
            "match_type": self.match_type.value,
            "processing_time_ms": round(float(self.processing_time_ms), 1) if self.processing_time_ms is not None else None,
            "debug": {
                "stage1_candidates": int(self.stage1_candidates),
                "stage2_candidates": int(self.stage2_candidates),
                "frames_sampled": int(self.frames_sampled),
                "frames_matched": int(self.frames_matched)
            }
        }

    def __str__(self):
        if not self.matched:
            return "❌ No match found"
        return (
            f"✅ {self.title} ({self.year})\n"
            f"   Confidence: {self.confidence:.1%} [{self.match_type.value}]\n"
            f"   Timestamp: {self.timestamp:.1f}s\n"
            f"   Votes: {self.frames_matched}/{self.frames_sampled} frames"
        )


@dataclass
class MediaItem:
    """A piece of media in the database"""
    id: int
    title: str
    year: Optional[int]
    duration: Optional[float]
    fingerprint_count: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "duration": self.duration,
            "fingerprint_count": self.fingerprint_count
        }