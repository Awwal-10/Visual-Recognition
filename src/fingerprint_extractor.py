"""
Fingerprint Extractor - Dual Hash System
Extracts both pHash (fast) and CNN features (accurate) from video frames
"""

import cv2
import numpy as np
import imagehash
from PIL import Image
import torch
from torchvision import models, transforms
from typing import List, Tuple
import time


class DualFingerprintExtractor:
    """Extract both perceptual hash and CNN features from video frames"""
    
    def __init__(self):
        """Initialize the CNN model and preprocessing"""
        print("🔄 Loading EfficientNet model...")
        
        # Load pre-trained EfficientNet
        self.model = models.efficientnet_b0(pretrained=True)
        self.model.eval()  # Set to inference mode
        
        # Use EfficientNet's features directly (1280 dimensions)
        # No random linear layer - keeps features consistent!
        self.feature_extractor = torch.nn.Sequential(
            self.model.features,
            self.model.avgpool,
            torch.nn.Flatten()
        )
        
        
        # Image preprocessing (required for EfficientNet)
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        print("✅ Model loaded and ready!")
    
    def compute_phash(self, frame: np.ndarray) -> str:
        """
        Compute perceptual hash for a frame
        
        Args:
            frame: OpenCV frame (BGR format)
        
        Returns:
            Hexadecimal hash string (16 characters)
        """
        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Compute perceptual hash
        phash = imagehash.phash(pil_image, hash_size=8)  # 8x8 = 64 bits
        
        return str(phash)
    
    def compute_cnn_features(self, frame: np.ndarray) -> np.ndarray:
        """
        Compute CNN feature vector for a frame
        
        Args:
            frame: OpenCV frame (BGR format)
        
        Returns:
            512-dimensional feature vector
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Preprocess for CNN
        input_tensor = self.preprocess(pil_image)
        input_batch = input_tensor.unsqueeze(0)  # Add batch dimension
        
        # Extract features (no gradient needed)
        with torch.no_grad():
            features = self.feature_extractor(input_batch)
        
        # Convert to numpy array and flatten
        feature_vector = features.squeeze().numpy()
        
        return feature_vector
    
    def extract_from_video(
        self, 
        video_path: str, 
        sample_rate: float = 1.0
    ) -> List[Tuple[float, str, np.ndarray]]:
        """
        Extract fingerprints from video at specified sample rate
        
        Args:
            video_path: Path to video file
            sample_rate: Frames per second to sample (1.0 = 1 fps)
        
        Returns:
            List of (timestamp, phash, cnn_features) tuples
        """
        print(f"\n📹 Processing video: {video_path}")
        print(f"📊 Sample rate: {sample_rate} fps")
        
        # Open video
        video = cv2.VideoCapture(video_path)
        
        if not video.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"⏱️  Duration: {duration:.1f} seconds ({total_frames} frames at {fps:.1f} fps)")
        
        # Calculate frame interval
        frame_interval = int(fps / sample_rate)
        expected_fingerprints = int(duration * sample_rate)
        
        print(f"🎯 Extracting ~{expected_fingerprints} fingerprints (every {frame_interval} frames)")
        
        fingerprints = []
        frame_count = 0
        
        start_time = time.time()
        
        while True:
            ret, frame = video.read()
            
            if not ret:
                break  # End of video
            
            # Check if we should process this frame
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                
                # Extract both fingerprints
                phash = self.compute_phash(frame)
                cnn_features = self.compute_cnn_features(frame)
                
                fingerprints.append((timestamp, phash, cnn_features))
                
                # Progress indicator
                if len(fingerprints) % 10 == 0:
                    print(f"  ⏳ Processed {len(fingerprints)} frames (timestamp: {timestamp:.1f}s)")
            
            frame_count += 1
        
        video.release()
        
        elapsed = time.time() - start_time
        print(f"\n✅ Extracted {len(fingerprints)} fingerprints in {elapsed:.1f} seconds")
        print(f"⚡ Speed: {len(fingerprints)/elapsed:.1f} fingerprints/second")
        
        return fingerprints


# Test function
def test_extractor():
    """Test the extractor on a sample video"""
    extractor = DualFingerprintExtractor()
    
    # You'll replace this with your actual video path
    test_video = "videos/test.mp4"
    
    try:
        fingerprints = extractor.extract_from_video(test_video, sample_rate=1.0)
        
        # Show first fingerprint as example
        if fingerprints:
            timestamp, phash, cnn_features = fingerprints[0]
            print(f"\n📸 First fingerprint:")
            print(f"   Timestamp: {timestamp:.2f}s")
            print(f"   pHash: {phash}")
            print(f"   CNN features shape: {cnn_features.shape}")
            print(f"   CNN features (first 5): {cnn_features[:5]}")
    
    except FileNotFoundError:
        print(f"\n⚠️  Test video not found at: {test_video}")
        print("   Place a video file in the videos/ folder and update the path")


if __name__ == "__main__":
    test_extractor()