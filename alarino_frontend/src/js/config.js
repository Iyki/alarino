
window.ALARINO_CONFIG = {
    domain: "alarino.com",

    get isLocalhost() {
        return window.location.hostname === 'localhost' ||
               window.location.hostname === '127.0.0.1';
    },
    
    // Get the base URL, including protocol and hostname with port
    get baseUrl() {
        if (this.isLocalhost) {
            // For local dev, use the current origin, which includes the port
            return window.location.origin;
        }
        return `https://${this.domain}`;
    },

    // Get the API base URL
    get apiBaseUrl() {
        if (this.isLocalhost) {
            // In local dev, the API is at /api relative to the base URL.
            return `${this.baseUrl}/api`;
        }
        // For production, use the dedicated API subdomain
        return `https://api.${this.domain}/api`;
    }
};