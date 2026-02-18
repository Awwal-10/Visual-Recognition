/**
 * Main Application Logic
 * Orchestrates API calls, UI updates, and user interactions
 */

import CONFIG from './config.js';
import apiClient from './api.js';
import uiManager from './ui.js';

class VisualRecognitionApp {
  constructor() {
    this.fileInput = null;
    this.uploadZone = null;
  }

  /**
   * Initialize application
   */
  async init() {
    console.log('🚀 Initializing Visual Recognition App...');

    // Initialize UI manager
    uiManager.init();

    // Cache DOM elements
    this.cacheElements();

    // Set up event listeners
    this.setupEventListeners();

    // Check API health
    await this.checkAPIHealth();

    console.log('✅ App initialized successfully');
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.fileInput = document.getElementById('file-input');
    this.uploadZone = document.getElementById('upload-zone');
    this.captureBtn = document.getElementById('capture-btn');
    this.uploadBtn = document.getElementById('upload-btn');
  }

  /**
   * Set up all event listeners
   */
  setupEventListeners() {
    // File input change
    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    // Upload button click
    if (this.uploadBtn) {
      this.uploadBtn.addEventListener('click', () => this.fileInput?.click());
    }

    // Capture button (mobile camera)
    if (this.captureBtn) {
      this.captureBtn.addEventListener('click', () => this.handleCapture());
    }

    // Drag and drop on upload zone
    if (this.uploadZone) {
      this.uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
      this.uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
      this.uploadZone.addEventListener('drop', (e) => this.handleDrop(e));
      this.uploadZone.addEventListener('click', () => this.fileInput?.click());
    }

    // Network status monitoring
    window.addEventListener('online', () => {
      uiManager.updateStatus(true);
      uiManager.showToast('Connection restored', 'success');
    });

    window.addEventListener('offline', () => {
      uiManager.updateStatus(false);
      uiManager.showToast('No internet connection', 'error');
    });
  }

  /**
   * Check API health on startup
   */
  async checkAPIHealth() {
    try {
      const health = await apiClient.checkHealth();
      console.log('✅ API Health:', health);
      uiManager.updateStatus(true);
    } catch (error) {
      console.error('❌ API Health Check Failed:', error);
      uiManager.updateStatus(false);
      uiManager.showToast('API unavailable - check connection', 'error');
    }
  }

  /**
   * Handle file selection from input
   */
  async handleFileSelect(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    await this.processFile(file);

    // Reset input so same file can be selected again
    event.target.value = '';
  }

  /**
   * Handle drag over event
   */
  handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    this.uploadZone?.classList.add('dragover');
  }

  /**
   * Handle drag leave event
   */
  handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    this.uploadZone?.classList.remove('dragover');
  }

  /**
   * Handle file drop
   */
  async handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    this.uploadZone?.classList.remove('dragover');

    const file = event.dataTransfer?.files?.[0];
    if (!file) return;

    await this.processFile(file);
  }

  /**
   * Handle camera capture (mobile)
   */
  handleCapture() {
    if (!this.fileInput) return;

    // Set accept to capture video from camera
    this.fileInput.setAttribute('accept', 'video/*');
    this.fileInput.setAttribute('capture', 'environment');
    this.fileInput.click();

    // Reset after click
    setTimeout(() => {
      this.fileInput.removeAttribute('capture');
      this.fileInput.setAttribute('accept', CONFIG.API.ALLOWED_TYPES.join(','));
    }, 100);
  }

  /**
   * Process and identify file
   */
  async processFile(file) {
    try {
      // Validate file type
      if (!CONFIG.API.ALLOWED_TYPES.includes(file.type)) {
        throw new Error(CONFIG.UI.MESSAGES.INVALID_FILE);
      }

      // Validate file size
      if (file.size > CONFIG.API.MAX_FILE_SIZE) {
        throw new Error(CONFIG.UI.MESSAGES.FILE_TOO_LARGE);
      }

      console.log('📤 Processing file:', file.name, `(${(file.size / 1024 / 1024).toFixed(2)} MB)`);

      // Show loading state
      uiManager.showLoading(CONFIG.UI.MESSAGES.PROCESSING);

      // Call API
      const result = await apiClient.identifyMedia(file, (progress) => {
        // Optional: Update progress indicator
        console.log('Upload progress:', progress);
      });

      console.log('✅ Recognition result:', result);

      // Show result
      uiManager.showResult(result);

    } catch (error) {
      console.error('❌ Recognition error:', error);

      // Determine user-friendly error message
      let errorMessage = error.message;

      if (error.message.includes('timeout')) {
        errorMessage = 'Request timed out. The video might be too large.';
      } else if (error.message.includes('No internet')) {
        errorMessage = CONFIG.UI.MESSAGES.NETWORK_ERROR;
      } else if (!error.message.includes('File')) {
        // Generic error for API errors
        errorMessage = 'Could not identify this video. Please try another.';
      }

      uiManager.showError(errorMessage);
    }
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const app = new VisualRecognitionApp();
    app.init();
  });
} else {
  const app = new VisualRecognitionApp();
  app.init();
}

export default VisualRecognitionApp;