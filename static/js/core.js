/**
 * F-AI Accountant - Core Application JavaScript
 * Professional enterprise-grade frontend architecture
 * Version: 2.0.0
 */

(function(window, document) {
    'use strict';

    // Core application namespace
    const FaiCore = {
        // Application configuration
        config: {
            version: '2.0.0',
            apiBaseUrl: '/api',
            csrfToken: null,
            debug: false,
            theme: {
                storageKey: 'f-ai-theme',
                default: 'light',
                options: ['light', 'dark']
            }
        },

        // Application modules
        modules: {
            theme: null,
            validation: null,
            charts: null,
            upload: null,
            navigation: null
        },

        // Application state
        state: {
            initialized: false,
            user: null,
            currentPage: null,
            loading: false
        },

        // Utility functions
        utils: {
            debounce: function(func, wait) {
                let timeout;
                return function executedFunction(...args) {
                    const later = () => {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            }
        },

        // Error handling
        errors: {
            handlers: [],
            log: function(error, context) {
                console.error(`[F-AI Error] ${context}:`, error);
                this.handlers.forEach(handler => handler(error, context));
            },

            addHandler: function(handler) {
                if (typeof handler === 'function') {
                    this.handlers.push(handler);
                }
            }
        },

        // DOM utilities with null checks
        dom: {
            ready: function(callback) {
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', callback);
                } else {
                    callback();
                }
            },

            find: function(selector, context = document) {
                try {
                    return context.querySelector(selector);
                } catch (e) {
                    FaiCore.errors.log(e, 'DOM find');
                    return null;
                }
            },

            findAll: function(selector, context = document) {
                try {
                    return context.querySelectorAll(selector);
                } catch (e) {
                    FaiCore.errors.log(e, 'DOM findAll');
                    return [];
                }
            },

            safeInnerHTML: function(element, content) {
                if (element && typeof element.innerHTML !== 'undefined') {
                    element.innerHTML = content;
                    return true;
                }
                FaiCore.errors.log(new Error('Invalid element for innerHTML'), 'DOM safeInnerHTML');
                return false;
            },

            safeTextContent: function(element, content) {
                if (element && typeof element.textContent !== 'undefined') {
                    element.textContent = content;
                    return true;
                }
                return false;
            }
        },

        // Get CSRF token from meta tag
        getCSRFToken() {
            const token = document.querySelector('meta[name="csrf-token"]');
            return token ? token.getAttribute('content') : '';
        },

        // API utilities
        api: {
            // API request method with enhanced error handling
            async apiRequest(endpoint, options = {}) {
                try {
                    const response = await fetch(endpoint, {
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest',
                            ...options.headers
                        },
                        ...options
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${data.message || 'Request failed'}`);
                    }

                    return data;
                } catch (error) {
                    console.error('[F-AI Error] API request failed:', {
                        endpoint,
                        error: error.message,
                        options
                    });

                    // Log error to backend
                    this.logError('API request failed', { 
                        endpoint, 
                        error: error.message,
                        status: error.status || 'unknown',
                        method: options.method || 'GET'
                    });

                    return { 
                        success: false, 
                        error: error.message,
                        endpoint: endpoint
                    };
                }
            },

            get: function(url, options = {}) {
                return this.apiRequest(url, { ...options, method: 'GET' });
            },

            post: function(url, data, options = {}) {
                return this.apiRequest(url, {
                    ...options,
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }
        },

        // Utility functions
        utils: {
            debounce: function(func, wait) {
                let timeout;
                return function executedFunction(...args) {
                    const later = () => {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            },

            throttle: function(func, limit) {
                let inThrottle;
                return function(...args) {
                    if (!inThrottle) {
                        func.apply(this, args);
                        inThrottle = true;
                        setTimeout(() => inThrottle = false, limit);
                    }
                };
            },

            formatCurrency: function(amount, currency = 'USD') {
                try {
                    return new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: currency
                    }).format(amount);
                } catch (e) {
                    return `${currency} ${amount}`;
                }
            },

            formatNumber: function(number, decimals = 2) {
                try {
                    return new Intl.NumberFormat('en-US', {
                        minimumFractionDigits: decimals,
                        maximumFractionDigits: decimals
                    }).format(number);
                } catch (e) {
                    return number.toFixed(decimals);
                }
            },

            validateEmail: function(email) {
                const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return re.test(email);
            },

            sanitizeHTML: function(str) {
                const div = document.createElement('div');
                div.textContent = str;
                return div.innerHTML;
            }
        },

        // Initialization
        init: function() {
            if (this.state.initialized) {
                return;
            }

            this.dom.ready(() => {
                try {
                    this.initializeCSRF();
                    this.initializeModules();
                    this.bindGlobalEvents();
                    this.setupErrorHandling();
                    this.state.initialized = true;

                    console.log(`✅ F-AI Core v${this.config.version} initialized successfully`);
                } catch (error) {
                    this.errors.log(error, 'Core initialization');
                }
            });
        },

        initializeCSRF: function() {
            const csrfToken = this.dom.find('meta[name="csrf-token"]');
            if (csrfToken) {
                this.config.csrfToken = csrfToken.getAttribute('content');
            }
        },

        initializeModules: function() {
            // Initialize theme module
            if (window.FaiTheme) {
                this.modules.theme = new window.FaiTheme();
            }

            // Initialize validation module
            if (window.FaiValidation) {
                this.modules.validation = new window.FaiValidation();
            }

            // Initialize charts module
            if (window.FaiCharts) {
                this.modules.charts = new window.FaiCharts();
            }

            // Initialize navigation module
            if (window.FaiNavigation) {
                this.modules.navigation = new window.FaiNavigation();
            }
        },

        bindGlobalEvents: function() {
            // Global error handler
            window.addEventListener('error', (event) => {
                this.errors.log(event.error, 'Global error');
            });

            // Unhandled promise rejections
            window.addEventListener('unhandledrejection', (event) => {
                this.errors.log(event.reason, 'Unhandled promise rejection');
            });

            // Page visibility change
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.handlePageHidden();
                } else {
                    this.handlePageVisible();
                }
            });
        },

        setupErrorHandling: function() {
            this.errors.addHandler((error, context) => {
                // Send error to server if in production
                if (!this.config.debug) {
                    this.api.post('/api/log-error', {
                        error: error.message,
                        context: context,
                        stack: error.stack,
                        timestamp: new Date().toISOString()
                    }).catch(() => {
                        // Silently fail if error logging fails
                    });
                }
            });
        },

        handlePageHidden: function() {
            // Pause any ongoing operations
            this.state.loading = false;
        },

        handlePageVisible: function() {
            // Resume operations if needed
        },

        // Public API
        getModule: function(name) {
            return this.modules[name];
        },

        ready: function(callback) {
            if (this.state.initialized) {
                callback();
            } else {
                this.dom.ready(callback);
            }
        },
        // Error logging with enhanced backend communication
        logError(message, details = {}) {
            console.error('[F-AI Error]', message, details);

            // Enhanced error data
            const errorData = {
                message: message,
                details: details,
                type: details.type || 'javascript',
                timestamp: new Date().toISOString(),
                url: window.location.href,
                userAgent: navigator.userAgent,
                stack: details.stack || new Error().stack,
                severity: details.severity || 'error'
            };

            // Send to backend for logging
            fetch('/api/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(errorData)
            })
            .then(response => {
                if (!response.ok) {
                    console.warn('Error logging response not OK:', response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    console.log('[F-AI] Error logged successfully:', data.error_id);
                }
            })
            .catch(err => {
                console.error('Failed to log error to backend:', err);
                // Store in localStorage as fallback
                try {
                    const errorLog = JSON.parse(localStorage.getItem('f_ai_error_log') || '[]');
                    errorLog.push(errorData);
                    localStorage.setItem('f_ai_error_log', JSON.stringify(errorLog.slice(-10))); // Keep last 10 errors
                } catch (storageErr) {
                    console.error('Failed to store error in localStorage:', storageErr);
                }
            });
        }
    };

    // Expose to global scope
    window.FaiCore = FaiCore;

    // Auto-initialize
    FaiCore.init();

})(window, document);