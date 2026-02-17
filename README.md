# 🎬 Visual Media Recognition System

> Identify movies and TV shows from compressed social media clips in under 1 second.
> Built as a pivot from an audio fingerprinting system after discovering visual signals 
> are far more resilient to TikTok/Instagram compression.

## Demo
```bash
curl -X POST -F "file=@tiktok_clip.mp4" http://localhost:8080/api/v1/identify
```
```json
{
  "matched": true,
  "title": "The Dictator",
  "year": 2012,
  "confidence": 1.0,
  "match_type": "strong",
  "processing_time_ms": 593.8
}
```

## How It Works

Two-stage hybrid pipeline combining speed and accuracy:
```
Query Video → Extract Frames → pHash Filter → CNN Verification → Result
                                  (fast)          (accurate)
```

**Stage 1: Perceptual Hashing (pHash)**
- Generates 64-bit hash per frame using DCT (same math as JPEG)
- Searches entire database in milliseconds
- Filters 99%+ of non-matching frames
- Robust to compression and minor modifications

**Stage 2: CNN Feature Verification (EfficientNet-B0)**
- Extracts 1280-dimensional feature vector per frame
- Compares using cosine similarity
- Handles overlays, filters, aspect ratio changes
- Only runs on top candidates from Stage 1

## Performance Benchmarks

| Metric | Result |
|--------|--------|
| Recognition speed | < 1 second per clip |
| Fingerprinting speed | 12 fps |
| Accuracy on clean clips | 100% |
| Accuracy on TikTok clips | 80%+ |
| False positive rate | 0% (tested) |
| Database size (per movie) | ~2MB |

## Quick Start

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install opencv-python imagehash pillow torch torchvision numpy scipy flask flask-cors
```

### 2. Add Media to Database
```bash
python src/add_media.py --video movie.mp4 --title "Movie Name" --year 2024 --sample-rate 2.0
```

### 3. Start the API
```bash
PORT=8080 python api/app.py
```

### 4. Identify a Clip
```bash
curl -X POST -F "file=@clip.mp4" http://localhost:8080/api/v1/identify
```

## API Reference

### `POST /api/v1/identify`
Identify media from uploaded video or image.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "matched": true,
  "title": "Movie Name",
  "year": 2012,
  "timestamp": 43.2,
  "confidence": 0.97,
  "match_type": "strong | probable | weak",
  "processing_time_ms": 593.8
}
```

### `GET /api/v1/media`
List all fingerprinted media in database.

### `GET /api/v1/health`
Health check with database statistics.

## 🔄 The Pivot Story

This project evolved from an audio fingerprinting system (similar to Shazam) that 
I shipped and tested with real users. The audio system achieved 67% accuracy on 
music-heavy content but failed on social media clips because:

1. Video compression prioritizes visual quality over audio
2. Users add voiceovers and background music  
3. Copyright filters intentionally distort audio
4. Many users scroll with sound off

After analyzing these failure modes, I identified visual frame matching as the 
more robust solution. This system achieves:
- **Better compression resilience** (pHash is DCT-based like JPEG/MP4)
- **Semantic robustness** (CNN features survive overlays and filters)
- **Faster identification** (<1 second vs 2-3 seconds for audio)

## Tech Stack

- **Python 3.11** - Core language
- **PyTorch + EfficientNet-B0** - CNN feature extraction
- **OpenCV** - Video processing
- **imagehash** - Perceptual hashing
- **SQLite** - Fingerprint storage
- **Flask** - REST API

## Roadmap

- [ ] iOS Shortcut integration (screen capture → identify)
- [ ] Web interface for browser-based testing
- [ ] Docker deployment
- [ ] Expand database to 50+ titles
- [ ] PostgreSQL for production scale

## Author

Awwal - Computing Student at Queen's University  
Part of a portfolio demonstrating computer vision and systems design.
