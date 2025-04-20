
window.ALARINO_CONFIG = {
    apiBaseUrl: (window.location.hostname === 'localhost' || 
                    window.location.hostname.includes('127.0.0.1'))
        ? 'http://localhost:5001/api'
        : 'https://api.alarino.com/api'
};