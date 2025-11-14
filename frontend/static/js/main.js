// SOAR Platform Frontend JavaScript

// Utility functions
const SOAR = {
    // API base URL
    apiBase: '/api/v1',

    // Make API request
    async request(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    // Format date
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString();
    },

    // Format duration (seconds to human readable)
    formatDuration(seconds) {
        if (!seconds) return 'N/A';

        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);

        if (minutes === 0) {
            return `${remainingSeconds}s`;
        }
        return `${minutes}m ${remainingSeconds}s`;
    },

    // Show toast notification
    showToast(message, type = 'info') {
        // You can integrate with Bootstrap Toast or other notification library
        console.log(`[${type.toUpperCase()}] ${message}`);

        // Simple alert for now
        if (type === 'error') {
            alert(`Error: ${message}`);
        }
    },

    // Show loading spinner
    showLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = '<div class="loading-spinner"></div> Loading...';
        }
    },

    // Hide loading spinner
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        // Caller should update content
    },

    // Get severity badge color
    getSeverityClass(severity) {
        const severityMap = {
            'critical': 'severity-critical',
            'high': 'severity-high',
            'medium': 'severity-medium',
            'low': 'severity-low'
        };
        return severityMap[severity?.toLowerCase()] || '';
    },

    // Get status badge color
    getStatusClass(status) {
        const statusMap = {
            'new': 'status-new',
            'investigating': 'status-investigating',
            'contained': 'status-contained',
            'remediated': 'status-remediated',
            'closed': 'status-closed'
        };
        return statusMap[status?.toLowerCase()] || '';
    }
};

// Auto-refresh functionality
class AutoRefresh {
    constructor(callback, interval = 30000) {
        this.callback = callback;
        this.interval = interval;
        this.timer = null;
    }

    start() {
        this.stop(); // Clear any existing timer
        this.timer = setInterval(this.callback, this.interval);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    refresh() {
        this.callback();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SOAR, AutoRefresh };
}
