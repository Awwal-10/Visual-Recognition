/**
 * API Client
 * Handles all communication with the backend API
 * Implements retry logic, error handling, and request validation
 */

import CONFIG from './config.js';

class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.controller = null; // For request cancellation
  }

  /**
   * Make HTTP request with timeout and error handling
   * @private
   */
  async _request(endpoint, options = {}) {
    // Create abort controller for timeout
    this.controller = new AbortController();
    const timeoutId = setTimeout(
      () => this.controller.abort(),
      CONFIG.API.TIMEOUT
    );

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        signal: this.controller.signal
      });

      clearTimeout(timeoutId);

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      // Handle specific error types
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }

      if (!navigator.onLine) {
        throw new Error('No internet connection');
      }

      throw error;
    }
  }

  /**
   * Validate file before upload
   * @private
   */
  _validateFile(file) {
    if (!file) {
      throw new Error('No file provided');
    }

    // Check file size
    if (file.size > CONFIG.API.MAX_FILE_SIZE) {
      throw new Error(CONFIG.UI.MESSAGES.FILE_TOO_LARGE);
    }

    // Check file type
    if (!CONFIG.API.ALLOWED_TYPES.includes(file.type)) {
      throw new Error(CONFIG.UI.MESSAGES.INVALID_FILE);
    }

    return true;
  }

  /**
   * Check API health
   * @returns {Promise<Object>} Health status
   */
  async checkHealth() {
    return this._request(CONFIG.API.ENDPOINTS.HEALTH);
  }

  /**
   * Get list of media in database
   * @returns {Promise<Object>} List of media items
   */
  async getMediaList() {
    return this._request(CONFIG.API.ENDPOINTS.MEDIA);
  }

  /**
   * Identify media from file
   * @param {File} file - Video or image file
   * @param {Function} onProgress - Progress callback (optional)
   * @returns {Promise<Object>} Recognition result
   */
  async identifyMedia(file, onProgress = null) {
    // Validate file
    this._validateFile(file);

    // Create FormData
    const formData = new FormData();
    formData.append('file', file);

    // Track upload progress if callback provided
    const options = {
      method: 'POST',
      body: formData
    };

    if (onProgress && typeof onProgress === 'function') {
      // Note: Fetch API doesn't support upload progress directly
      // Would need XMLHttpRequest for true progress tracking
      onProgress({ loaded: 0, total: file.size });
    }

    const result = await this._request(CONFIG.API.ENDPOINTS.IDENTIFY, options);

    if (onProgress) {
      onProgress({ loaded: file.size, total: file.size });
    }

    return result;
  }

  /**
   * Cancel ongoing request
   */
  cancel() {
    if (this.controller) {
      this.controller.abort();
    }
  }
}

// Create singleton instance
const apiClient = new APIClient(CONFIG.API.BASE_URL);

export default apiClient;