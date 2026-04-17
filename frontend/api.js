/**
 * OMNISCIENT ULTIMATE SYSTEM FINAL - API Client
 * Handles all API communication with the backend
 */

// API Configuration
const API = {
    baseURL: null,
    token: null,
    timeout: 30000, // 30 seconds
    retries: 3
};

// Initialize API
function initializeAPI() {
    const settings = localStorage.getItem('omniscient_settings');
    if (settings) {
        const parsedSettings = JSON.parse(settings);
        API.baseURL = parsedSettings.apiEndpoint || 'http://localhost:8000/api/v1';
    } else {
        API.baseURL = 'http://localhost:8000/api/v1';
    }
    
    API.token = localStorage.getItem('omniscient_token');
    
    console.log('🔌 API initialized with base URL:', API.baseURL);
}

// HTTP Client
class HTTPClient {
    constructor(baseURL, token = null) {
        this.baseURL = baseURL;
        this.token = token;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        // Add authorization header if token exists
        if (this.token) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }
        
        // Add timeout
        config.signal = AbortSignal.timeout(API.timeout);
        
        let lastError;
        
        // Retry logic
        for (let attempt = 0; attempt < API.retries; attempt++) {
            try {
                console.log(`🌐 API Request: ${config.method || 'GET'} ${url} (attempt ${attempt + 1})`);
                
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    if (response.status === 401) {
                        // Token expired, try to refresh
                        if (await this.refreshToken()) {
                            config.headers.Authorization = `Bearer ${this.token}`;
                            continue; // Retry with new token
                        }
                    }
                    
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('✅ API Response:', data);
                return data;
                
            } catch (error) {
                lastError = error;
                console.warn(`⚠️ API Request failed (attempt ${attempt + 1}):`, error.message);
                
                if (attempt < API.retries - 1) {
                    // Exponential backoff
                    await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
                }
            }
        }
        
        throw lastError;
    }
    
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, { method: 'GET' });
    }
    
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
    
    async refreshToken() {
        try {
            const refreshToken = localStorage.getItem('omniscient_refresh_token');
            if (!refreshToken) {
                return false;
            }
            
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            
            if (!response.ok) {
                return false;
            }
            
            const data = await response.json();
            this.token = data.access_token;
            
            localStorage.setItem('omniscient_token', data.access_token);
            
            return true;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }
}

// API Client Instance
let apiClient = null;

// Initialize API Client
function getAPIClient() {
    if (!apiClient) {
        initializeAPI();
        apiClient = new HTTPClient(API.baseURL, API.token);
    }
    return apiClient;
}

// Authentication API
export const AuthAPI = {
    async login(username, password) {
        const client = getAPIClient();
        
        try {
            const response = await client.post('/auth/login', {
                username,
                password
            });
            
            // Store tokens
            localStorage.setItem('omniscient_token', response.access_token);
            localStorage.setItem('omniscient_refresh_token', response.refresh_token);
            
            apiClient.token = response.access_token;
            
            return response;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    },
    
    async register(userData) {
        const client = getAPIClient();
        
        try {
            const response = await client.post('/auth/register', userData);
            return response;
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    },
    
    async logout() {
        try {
            const client = getAPIClient();
            await client.post('/auth/logout');
        } catch (error) {
            console.error('Logout API call failed:', error);
        } finally {
            // Always clear local tokens
            localStorage.removeItem('omniscient_token');
            localStorage.removeItem('omniscient_refresh_token');
            localStorage.removeItem('omniscient_user');
            
            apiClient.token = null;
        }
    },
    
    async getCurrentUser() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/auth/me');
            return response;
        } catch (error) {
            console.error('Get current user failed:', error);
            throw error;
        }
    },
    
    async verifyToken() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/auth/verify-token');
            return response;
        } catch (error) {
            console.error('Token verification failed:', error);
            throw error;
        }
    }
};

// Search API
export const SearchAPI = {
    async executeSearch(query, options = {}) {
        const client = getAPIClient();
        
        try {
            const response = await client.post('/scan', {
                query,
                max_results: options.maxResults || 100,
                sources: options.sources,
                include_cache: options.includeCache !== false,
                deep_scan: options.deepScan || false,
                extract_data: options.extractData !== false,
                use_ai: options.useAI !== false
            });
            
            return response;
        } catch (error) {
            console.error('Search failed:', error);
            throw error;
        }
    },
    
    async getSearchStatus(scanId) {
        const client = getAPIClient();
        
        try {
            const response = await client.get(`/scan/${scanId}/status`);
            return response;
        } catch (error) {
            console.error('Get search status failed:', error);
            throw error;
        }
    },
    
    async cancelSearch(scanId) {
        const client = getAPIClient();
        
        try {
            const response = await client.delete(`/scan/${scanId}`);
            return response;
        } catch (error) {
            console.error('Cancel search failed:', error);
            throw error;
        }
    },
    
    async getActiveScans() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/scans/active');
            return response;
        } catch (error) {
            console.error('Get active scans failed:', error);
            throw error;
        }
    },
    
    async executeBatchSearch(queries) {
        const client = getAPIClient();
        
        try {
            const response = await client.post('/scan/batch', { queries });
            return response;
        } catch (error) {
            console.error('Batch search failed:', error);
            throw error;
        }
    },
    
    async getSearchHistory(limit = 50, offset = 0) {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/scan/history', { limit, offset });
            return response;
        } catch (error) {
            console.error('Get search history failed:', error);
            throw error;
        }
    },
    
    async retrySearch(scanId) {
        const client = getAPIClient();
        
        try {
            const response = await client.post(`/scan/${scanId}/retry`);
            return response;
        } catch (error) {
            console.error('Retry search failed:', error);
            throw error;
        }
    }
};

// Results API
export const ResultsAPI = {
    async getSearchResults(searchId, options = {}) {
        const client = getAPIClient();
        
        try {
            const params = {
                limit: options.limit || 100,
                offset: options.offset || 0,
                include_extracted_data: options.includeExtractedData !== false
            };
            
            const response = await client.get(`/search/${searchId}`, params);
            return response;
        } catch (error) {
            console.error('Get search results failed:', error);
            throw error;
        }
    },
    
    async exportSearchResults(searchId, exportOptions = {}) {
        const client = getAPIClient();
        
        try {
            const response = await client.get(`/search/${searchId}/export`, {
                format: exportOptions.format || 'json',
                include_extracted_data: exportOptions.includeExtractedData !== false,
                include_summary: exportOptions.includeSummary !== false,
                include_stats: exportOptions.includeStats !== false
            });
            
            // Handle file download
            if (response.blob) {
                return response;
            } else {
                return response;
            }
        } catch (error) {
            console.error('Export search results failed:', error);
            throw error;
        }
    },
    
    async getRecentResults(limit = 20) {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/results/recent', { limit });
            return response;
        } catch (error) {
            console.error('Get recent results failed:', error);
            throw error;
        }
    },
    
    async filterResults(filters = {}) {
        const client = getAPIClient();
        
        try {
            const response = await client.post('/results/filter', filters, {
                limit: filters.limit || 100,
                offset: filters.offset || 0
            });
            return response;
        } catch (error) {
            console.error('Filter results failed:', error);
            throw error;
        }
    },
    
    async getSearchStatistics(searchId) {
        const client = getAPIClient();
        
        try {
            const response = await client.get(`/search/${searchId}/stats`);
            return response;
        } catch (error) {
            console.error('Get search statistics failed:', error);
            throw error;
        }
    },
    
    async deleteSearch(searchId) {
        const client = getAPIClient();
        
        try {
            const response = await client.delete(`/search/${searchId}`);
            return response;
        } catch (error) {
            console.error('Delete search failed:', error);
            throw error;
        }
    }
};

// Health API
export const HealthAPI = {
    async getHealthStatus() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/health');
            return response;
        } catch (error) {
            console.error('Get health status failed:', error);
            throw error;
        }
    },
    
    async getReadinessStatus() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/health/ready');
            return response;
        } catch (error) {
            console.error('Get readiness status failed:', error);
            throw error;
        }
    },
    
    async getLivenessStatus() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/health/live');
            return response;
        } catch (error) {
            console.error('Get liveness status failed:', error);
            throw error;
        }
    },
    
    async getMetrics() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/metrics');
            return response;
        } catch (error) {
            console.error('Get metrics failed:', error);
            throw error;
        }
    },
    
    async getComponentHealth() {
        const client = getAPIClient();
        
        try {
            const response = await client.get('/health/components');
            return response;
        } catch (error) {
            console.error('Get component health failed:', error);
            throw error;
        }
    }
};

// WebSocket for real-time updates
export class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
        this.listeners = new Map();
    }
    
    connect(url = null) {
        if (!url) {
            const baseURL = API.baseURL.replace('http://', 'ws://').replace('https://', 'wss://');
            url = `${baseURL}/ws`;
        }
        
        try {
            console.log('🔌 Connecting to WebSocket:', url);
            
            this.ws = new WebSocket(url);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('connected');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.emit('message', data);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                    this.emit('error', { type: 'parse_error', message: error.message });
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket disconnected:', event.code, event.reason);
                this.emit('disconnected', { code: event.code, reason: event.reason });
                
                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        console.log(`🔄 WebSocket reconnection attempt ${this.reconnectAttempts}`);
                        this.connect(url);
                    }, this.reconnectInterval);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('🔌 WebSocket error:', error);
                this.emit('error', { type: 'websocket_error', error });
            };
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.emit('error', { type: 'connection_error', message: error.message });
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }
    
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in WebSocket event listener for ${event}:`, error);
                }
            });
        }
    }
    
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// File download utility
export const FileAPI = {
    async downloadFile(url, filename = null) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename || getFilenameFromUrl(url);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            window.URL.revokeObjectURL(downloadUrl);
            
        } catch (error) {
            console.error('File download failed:', error);
            throw error;
        }
    },
    
    async downloadBlob(blob, filename) {
        const downloadUrl = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        window.URL.revokeObjectURL(downloadUrl);
    }
};

// Utility functions
function getFilenameFromUrl(url) {
    const urlParts = url.split('/');
    const filename = urlParts[urlParts.length - 1];
    
    if (filename && filename.includes('.')) {
        return filename;
    }
    
    return 'download';
}

// Error handling
export class APIError extends Error {
    constructor(message, status = null, code = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.code = code;
    }
}

// Response interceptor
function handleAPIResponse(response) {
    if (response.status >= 200 && response.status < 300) {
        return response;
    } else {
        throw new APIError(
            response.message || 'API request failed',
            response.status,
            response.code
        );
    }
}

// Initialize API on module load
initializeAPI();

// Export API client
export { getAPIClient, API };

// Export WebSocket client
export { WebSocketClient };
