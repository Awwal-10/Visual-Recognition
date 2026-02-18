"""
Visual Recognition API
RESTful service for media identification
"""

import os
import sys
import tempfile
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'visrec'))

from recognizer import VisualRecognizer
from database_manager import FingerprintDatabase
from fingerprint_extractor import DualFingerprintExtractor

app = Flask(__name__)
CORS(app)

# Config
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'jpg', 'jpeg', 'png'}
DB_PATH = os.environ.get('DB_PATH', 'data/fingerprints.db')

# Initialize (loaded once, reused)
print("🔄 Loading recognition system...")
recognizer = VisualRecognizer(db_path=DB_PATH)
print("✅ API ready!")


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── ROUTES ─────────────────────────────────────────────────────────────────

@app.route('/api/v1/health', methods=['GET'])
def health():
    """Health check + database stats"""
    cursor = recognizer.db.conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM media")
    media_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fingerprints")
    fp_count = cursor.fetchone()[0]
    
    return jsonify({
        "status": "ok",
        "media_items": media_count,
        "fingerprints": fp_count,
        "version": "1.0.0"
    })
@app.route('/', methods=['GET'])
def home():
    """API documentation homepage"""
    return jsonify({
        "name": "Visual Recognition API",
        "version": "1.0.0",
        "description": "Identify movies and TV shows from video clips",
        "endpoints": {
            "health": "GET /api/v1/health",
            "list_media": "GET /api/v1/media",
            "identify": "POST /api/v1/identify (multipart/form-data with 'file' field)",
            "identify_url": "POST /api/v1/identify/url (JSON with 'url' field)"
        },
        "live_demo": "curl -X POST -F 'file=@video.mp4' https://visual-recognition-production.up.railway.app/api/v1/identify",
        "github": "https://github.com/Awwal-10/Visual-Recognition",
        "status": "operational"
    })

@app.route('/api/v1/media', methods=['GET'])
def list_media():
    """List all fingerprinted media"""
    cursor = recognizer.db.conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.title, m.year, m.duration,
               COUNT(f.id) as fingerprint_count
        FROM media m
        LEFT JOIN fingerprints f ON f.media_id = m.id
        GROUP BY m.id
        ORDER BY m.title
    """)
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "id": row[0],
            "title": row[1],
            "year": row[2],
            "duration": row[3],
            "fingerprints": row[4]
        })
    
    return jsonify({"media": items, "total": len(items)})


@app.route('/api/v1/identify', methods=['POST'])
def identify():
    """
    Identify media from uploaded video or image
    
    Request: multipart/form-data with 'file' field
    Response: RecognitionResult as JSON
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided. Send file as 'file' field"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not supported",
            "supported": list(ALLOWED_EXTENSIONS)
        }), 400
    
    # Save to temp file
    suffix = '.' + file.filename.rsplit('.', 1)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        sample_frames = int(request.form.get('sample_frames', 5))
        result = recognizer.identify(tmp_path, sample_frames=sample_frames)
        return jsonify(result.to_dict())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        os.unlink(tmp_path)


@app.route('/api/v1/identify/url', methods=['POST'])
def identify_from_url():
    """
    Identify media from a URL (TikTok, YouTube, etc.)
    
    Request: JSON { "url": "https://..." }
    Response: RecognitionResult as JSON
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "Provide JSON body with 'url' field"}), 400
    
    url = data['url']
    
    # Download with yt-dlp
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp_path = tmp.name
    
    try:
        import subprocess
        result = subprocess.run([
            'yt-dlp', '-f', 'best[ext=mp4]',
            url, '-o', tmp_path, '--quiet'
        ], capture_output=True, timeout=60)
        
        if result.returncode != 0:
            return jsonify({"error": "Failed to download video from URL"}), 400
        
        sample_frames = data.get('sample_frames', 5)
        result = recognizer.identify(tmp_path, sample_frames=sample_frames)
        return jsonify(result.to_dict())
    
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Download timed out"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ─── ERROR HANDLERS ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large"}), 413


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    print(f"\n🚀 Visual Recognition API")
    print(f"   Running on: http://localhost:{port}")
    print(f"   Database: {DB_PATH}")
    print(f"\n📡 Endpoints:")
    print(f"   GET  /api/v1/health")
    print(f"   GET  /api/v1/media")
    print(f"   POST /api/v1/identify      (upload file)")
    print(f"   POST /api/v1/identify/url  (from URL)\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)