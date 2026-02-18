/**
 * Configuration & Constants
 * Single source of truth for app configuration
 */

const CONFIG = {
  // API Configuration
  API: {
    BASE_URL: 'https://visual-recognition-production.up.railway.app',
    ENDPOINTS: {
      HEALTH: '/api/v1/health',
      IDENTIFY: '/api/v1/identify',
      MEDIA: '/api/v1/media'
    },
    TIMEOUT: 30000, // 30 seconds
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
    ALLOWED_TYPES: [
      'video/mp4',
      'video/quicktime',
      'video/x-msvideo',
      'image/jpeg',
      'image/png',
      'image/jpg'
    ]
  },

  // UI Configuration
  UI: {
    MESSAGES: {
      UPLOAD_PROMPT: 'Upload a video clip or screenshot',
      PROCESSING: 'Identifying...',
      SUCCESS: 'Found it!',
      ERROR: 'Could not identify this video',
      NETWORK_ERROR: 'Network error. Please check your connection.',
      FILE_TOO_LARGE: 'File is too large. Max size is 100MB.',
      INVALID_FILE: 'Please upload a video or image file.'
    },
    ANIMATION_DURATION: 300 // milliseconds
  },

  // Feature Flags
  FEATURES: {
    CAMERA_CAPTURE: true,
    FILE_UPLOAD: true,
    HISTORY: true,
    SHARE: true
  }
};

// Freeze config to prevent modifications
Object.freeze(CONFIG);

export default CONFIG;