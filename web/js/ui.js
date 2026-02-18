/**
 * UI State Management
 * Handles all UI updates and state transitions
 * Separation of concerns: UI logic separate from business logic
 */

import CONFIG from './config.js';

class UIManager {
  constructor() {
    this.elements = {};
    this.state = {
      isLoading: false,
      hasResult: false,
      currentResult: null
    };
  }

  /**
   * Initialize and cache DOM elements
   */
  init() {
    this.elements = {
      uploadZone: document.getElementById('upload-zone'),
      fileInput: document.getElementById('file-input'),
      captureBtn: document.getElementById('capture-btn'),
      uploadBtn: document.getElementById('upload-btn'),
      resultsSection: document.getElementById('results-section'),
      statusIndicator: document.getElementById('status-indicator'),
      loadingState: document.getElementById('loading-state'),
      errorState: document.getElementById('error-state')
    };

    return this;
  }

  /**
   * Show loading state
   * @param {string} message - Loading message
   */
  showLoading(message = CONFIG.UI.MESSAGES.PROCESSING) {
    this.state.isLoading = true;
    
    // Update upload zone
    if (this.elements.uploadZone) {
      this.elements.uploadZone.classList.add('disabled');
    }

    // Show loading spinner
    if (this.elements.loadingState) {
      this.elements.loadingState.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <p class="loading-text">${message}</p>
        </div>
      `;
      this.elements.loadingState.style.display = 'block';
    }

    // Hide results and errors
    this.hideResults();
    this.hideError();

    // Disable buttons
    this.setButtonsDisabled(true);
  }

  /**
   * Hide loading state
   */
  hideLoading() {
    this.state.isLoading = false;

    if (this.elements.uploadZone) {
      this.elements.uploadZone.classList.remove('disabled');
    }

    if (this.elements.loadingState) {
      this.elements.loadingState.style.display = 'none';
    }

    this.setButtonsDisabled(false);
  }

  /**
   * Show recognition results
   * @param {Object} result - API response
   */
  showResult(result) {
    this.state.hasResult = true;
    this.state.currentResult = result;

    if (!this.elements.resultsSection) return;

    const {
      matched,
      title,
      year,
      confidence,
      match_type,
      processing_time_ms,
      timestamp
    } = result;

    if (!matched) {
      this.showError(CONFIG.UI.MESSAGES.ERROR);
      return;
    }

    // Build result HTML
    this.elements.resultsSection.innerHTML = `
      <div class="result-card">
        <div class="result-header">
          <div class="result-icon">🎬</div>
          <div>
            <h2 class="result-title">${this.escapeHtml(title)}</h2>
            ${year ? `<p class="result-year">${year}</p>` : ''}
          </div>
        </div>

        <div class="result-meta">
          <span class="badge badge-success">
            ${(confidence * 100).toFixed(1)}% Match
          </span>
          <span class="badge">
            ${match_type.charAt(0).toUpperCase() + match_type.slice(1)}
          </span>
          <span class="badge">
            ${(processing_time_ms / 1000).toFixed(1)}s
          </span>
        </div>

        <div class="result-details">
          ${timestamp !== null && timestamp !== undefined ? `
            <div class="detail-row">
              <span class="detail-label">Scene Timestamp</span>
              <span class="detail-value">${this.formatTime(timestamp)}</span>
            </div>
          ` : ''}
          
          <div class="detail-row">
            <span class="detail-label">Confidence</span>
            <span class="detail-value">${(confidence * 100).toFixed(2)}%</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Processing Time</span>
            <span class="detail-value">${(processing_time_ms / 1000).toFixed(2)} seconds</span>
          </div>
        </div>
      </div>
    `;

    this.elements.resultsSection.style.display = 'block';
    this.hideLoading();
    this.showToast(CONFIG.UI.MESSAGES.SUCCESS, 'success');
  }

  /**
   * Show error message
   * @param {string} message - Error message
   */
  showError(message) {
    this.hideLoading();

    if (this.elements.errorState) {
      this.elements.errorState.innerHTML = `
        <div class="error-state">
          <div class="error-icon">⚠️</div>
          <p class="error-message">${this.escapeHtml(message)}</p>
          <p class="error-details">Please try again with a different video</p>
        </div>
      `;
      this.elements.errorState.style.display = 'block';
    }

    this.showToast(message, 'error');
  }

  /**
   * Hide error state
   */
  hideError() {
    if (this.elements.errorState) {
      this.elements.errorState.style.display = 'none';
    }
  }

  /**
   * Hide results
   */
  hideResults() {
    if (this.elements.resultsSection) {
      this.elements.resultsSection.style.display = 'none';
    }
  }

  /**
   * Show toast notification
   * @param {string} message
   * @param {string} type - 'success' | 'error' | 'info'
   */
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), CONFIG.UI.ANIMATION_DURATION);
    }, 3000);
  }

  /**
   * Update status indicator
   * @param {boolean} online
   */
  updateStatus(online) {
    if (!this.elements.statusIndicator) return;

    this.elements.statusIndicator.innerHTML = `
      <span class="status-dot" style="background: ${online ? 'var(--color-success)' : 'var(--color-error)'}"></span>
      <span>${online ? 'Online' : 'Offline'}</span>
    `;
  }

  /**
   * Enable/disable action buttons
   * @param {boolean} disabled
   */
  setButtonsDisabled(disabled) {
    [this.elements.captureBtn, this.elements.uploadBtn].forEach(btn => {
      if (btn) {
        btn.disabled = disabled;
      }
    });
  }

  /**
   * Format seconds to MM:SS
   * @param {number} seconds
   * @returns {string}
   */
  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text
   * @returns {string}
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Create singleton instance
const uiManager = new UIManager();

export default uiManager;