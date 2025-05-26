
window.ALARINO_CONFIG = {
    domain: "alarino.com",

    // Computed properties
    get fullDomain() {
        this.domain;
    },
    
    get baseUrl() {
        return `https://${this.fullDomain}`;
    },

    get apiBaseUrl() {
        if (window.location.hostname === 'localhost' || 
            window.location.hostname.includes('127.0.0.1')) {
            return 'http://127.0.0.1/api';
        }
        return `https://api.${this.domain}/api`;
    }
};