/**
 * OMNISCIENT ULTIMATE SYSTEM FINAL - Frontend Application
 * Main application logic and UI management
 */

// Application State
const AppState = {
    currentPage: 'search',
    user: null,
    token: null,
    searchResults: null,
    currentSearch: null,
    settings: {
        apiEndpoint: 'http://localhost:8000/api/v1',
        theme: 'dark',
        language: 'pt-BR',
        autoCache: true,
        autoAI: true,
        defaultMaxResults: 100,
        defaultSources: ['web', 'social', 'knowledge', 'news'],
        resultsPerPage: 50
    },
    systemStats: {
        uptime: 0,
        totalSearches: 0,
        cacheHitRate: 0,
        cpuUsage: 0,
        memoryUsage: 0
    }
};

// DOM Elements
const elements = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    
    // Search
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    searchLoading: document.getElementById('searchLoading'),
    searchResults: document.getElementById('searchResults'),
    loadingStatus: document.getElementById('loadingStatus'),
    progressFill: document.getElementById('progressFill'),
    
    // Results
    summaryContent: document.getElementById('summaryContent'),
    totalResults: document.getElementById('totalResults'),
    processingTime: document.getElementById('processingTime'),
    sourcesUsed: document.getElementById('sourcesUsed'),
    relevanceScore: document.getElementById('relevanceScore'),
    resultsList: document.getElementById('resultsList'),
    
    // Dashboard
    systemStatus: document.getElementById('systemStatus'),
    activeScans: document.getElementById('activeScans'),
    recentSearches: document.getElementById('recentSearches'),
    cpuMetric: document.getElementById('cpuMetric'),
    memoryMetric: document.getElementById('memoryMetric'),
    diskMetric: document.getElementById('diskMetric'),
    cacheMetric: document.getElementById('cacheMetric'),
    
    // History
    historyList: document.getElementById('historyList'),
    historySearch: document.getElementById('historySearch'),
    historyFilter: document.getElementById('historyFilter'),
    
    // User
    userMenuBtn: document.getElementById('userMenuBtn'),
    userDropdown: document.getElementById('userDropdown'),
    loginBtn: document.getElementById('loginBtn'),
    registerBtn: document.getElementById('registerBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    username: document.querySelector('.username'),
    
    // Modals
    loginModal: document.getElementById('loginModal'),
    exportModal: document.getElementById('exportModal'),
    closeLoginModal: document.getElementById('closeLoginModal'),
    closeExportModal: document.getElementById('closeExportModal'),
    
    // Forms
    loginForm: document.getElementById('loginForm'),
    exportFormat: document.getElementById('exportFormat'),
    confirmExportBtn: document.getElementById('confirmExportBtn')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 OMNISCIENT System initializing...');
    
    initializeApp();
    setupEventListeners();
    loadSettings();
    checkAuthStatus();
    
    // Start periodic updates
    setInterval(updateSystemStats, 30000); // Every 30 seconds
    
    console.log('✅ OMNISCIENT System ready');
});

// Initialize Application
function initializeApp() {
    // Load saved settings
    const savedSettings = localStorage.getItem('omniscient_settings');
    if (savedSettings) {
        AppState.settings = { ...AppState.settings, ...JSON.parse(savedSettings) };
    }
    
    // Apply theme
    applyTheme(AppState.settings.theme);
    
    // Show initial page
    showPage(AppState.currentPage);
    
    // Initialize tooltips and other UI elements
    initializeUI();
}

// Setup Event Listeners
function setupEventListeners() {
    // Navigation
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            showPage(page);
        });
    });
    
    // Search
    elements.searchBtn.addEventListener('click', executeSearch);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            executeSearch();
        }
    });
    
    // User menu
    elements.userMenuBtn.addEventListener('click', toggleUserDropdown);
    
    // Authentication
    elements.loginBtn.addEventListener('click', showLoginModal);
    elements.registerBtn.addEventListener('click', showRegisterModal);
    elements.logoutBtn.addEventListener('click', logout);
    
    // Close modals
    elements.closeLoginModal.addEventListener('click', () => hideModal('loginModal'));
    elements.closeExportModal.addEventListener('click', () => hideModal('exportModal'));
    
    // Login form
    elements.loginForm.addEventListener('submit', handleLogin);
    
    // Export
    document.getElementById('exportBtn')?.addEventListener('click', showExportModal);
    elements.confirmExportBtn.addEventListener('click', exportResults);
    
    // Settings
    document.getElementById('saveSettingsBtn')?.addEventListener('click', saveSettings);
    document.getElementById('resetSettingsBtn')?.addEventListener('click', resetSettings);
    document.getElementById('clearDataBtn')?.addEventListener('click', clearLocalData);
    
    // History
    elements.historySearch?.addEventListener('input', filterHistory);
    elements.historyFilter?.addEventListener('change', filterHistory);
    document.getElementById('clearHistoryBtn')?.addEventListener('click', clearHistory);
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!elements.userMenuBtn.contains(e.target) && !elements.userDropdown.contains(e.target)) {
            elements.userDropdown.classList.remove('show');
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'k':
                    e.preventDefault();
                    elements.searchInput.focus();
                    break;
                case '/':
                    e.preventDefault();
                    showPage('search');
                    elements.searchInput.focus();
                    break;
                case 'd':
                    e.preventDefault();
                    showPage('dashboard');
                    break;
                case 'h':
                    e.preventDefault();
                    showPage('history');
                    break;
                case 's':
                    e.preventDefault();
                    showPage('settings');
                    break;
            }
        }
    });
}

// Page Navigation
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show target page
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Update navigation
    elements.navBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.page === pageName) {
            btn.classList.add('active');
        }
    });
    
    AppState.currentPage = pageName;
    
    // Load page-specific data
    switch(pageName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'history':
            loadHistory();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Search Functionality
async function executeSearch() {
    const query = elements.searchInput.value.trim();
    if (!query) {
        showError('Por favor, digite um termo de busca');
        return;
    }
    
    const searchOptions = getSearchOptions();
    
    // Show loading state
    showSearchLoading();
    
    try {
        // Start search
        const response = await fetch(`${AppState.settings.apiEndpoint}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(AppState.token && { 'Authorization': `Bearer ${AppState.token}` })
            },
            body: JSON.stringify({
                query: query,
                ...searchOptions
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Update UI with results
        AppState.currentSearch = result;
        displaySearchResults(result);
        
        // Update history
        addToHistory(query, result);
        
    } catch (error) {
        console.error('Search error:', error);
        showError(`Erro na busca: ${error.message}`);
    } finally {
        hideSearchLoading();
    }
}

function getSearchOptions() {
    const options = {
        max_results: parseInt(document.getElementById('maxResults')?.value) || AppState.settings.defaultMaxResults,
        include_cache: document.getElementById('useCache')?.checked ?? AppState.settings.autoCache,
        deep_scan: document.getElementById('deepScan')?.checked ?? false,
        extract_data: document.getElementById('extractData')?.checked ?? true,
        use_ai: document.getElementById('useAI')?.checked ?? AppState.settings.autoAI
    };
    
    // Get selected sources
    const sourceCheckboxes = document.querySelectorAll('input[name="sources"]:checked');
    if (sourceCheckboxes.length > 0) {
        options.sources = Array.from(sourceCheckboxes).map(cb => cb.value);
    } else {
        options.sources = AppState.settings.defaultSources;
    }
    
    return options;
}

function showSearchLoading() {
    elements.searchLoading.style.display = 'block';
    elements.searchResults.style.display = 'none';
    
    // Reset progress
    elements.progressFill.style.width = '0%';
    elements.loadingStatus.textContent = 'Iniciando busca...';
    
    // Simulate progress updates
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        
        elements.progressFill.style.width = `${progress}%`;
        
        if (progress < 30) {
            elements.loadingStatus.textContent = 'Buscando em múltiplas fontes...';
        } else if (progress < 60) {
            elements.loadingStatus.textContent = 'Analisando e extraindo dados...';
        } else if (progress < 90) {
            elements.loadingStatus.textContent = 'Gerando resumo com IA...';
        }
    }, 500);
    
    // Store interval ID for cleanup
    elements.searchLoading.dataset.progressInterval = progressInterval;
}

function hideSearchLoading() {
    const progressInterval = elements.searchLoading.dataset.progressInterval;
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    elements.searchLoading.style.display = 'none';
}

function displaySearchResults(result) {
    elements.searchResults.style.display = 'block';
    
    // Update summary
    elements.summaryContent.innerHTML = formatMarkdown(result.summary);
    
    // Update stats
    elements.totalResults.textContent = result.stats?.total_results || result.results?.length || 0;
    elements.processingTime.textContent = `${(result.processing_time || 0).toFixed(2)}s`;
    elements.sourcesUsed.textContent = result.stats?.sources_used?.length || 0;
    elements.relevanceScore.textContent = `${Math.round((result.stats?.average_relevance || 0) * 100)}%`;
    
    // Display results
    displayResultsList(result.results || []);
}

function displayResultsList(results) {
    elements.resultsList.innerHTML = '';
    
    if (results.length === 0) {
        elements.resultsList.innerHTML = '<div class="no-data">Nenhum resultado encontrado</div>';
        return;
    }
    
    results.forEach((result, index) => {
        const resultElement = createResultElement(result, index);
        elements.resultsList.appendChild(resultElement);
    });
}

function createResultElement(result, index) {
    const div = document.createElement('div');
    div.className = 'result-item fade-in';
    div.style.animationDelay = `${index * 0.1}s`;
    
    const extractedData = result.extracted_data || {};
    
    div.innerHTML = `
        <div class="result-header">
            <div>
                <div class="result-title">
                    <a href="${result.url}" target="_blank" rel="noopener noreferrer">
                        ${escapeHtml(result.title)}
                    </a>
                </div>
                <div class="result-meta">
                    <span class="result-source">${result.source}</span>
                    <span class="result-relevance">
                        <span class="relevance-score">${Math.round(result.relevance_score * 100)}%</span>
                    </span>
                </div>
            </div>
        </div>
        <div class="result-description">
            ${escapeHtml(result.description || 'Sem descrição disponível')}
        </div>
        ${Object.keys(extractedData).length > 0 ? `
            <div class="result-extracted-data">
                <div class="extracted-data-title">📊 Dados Extraídos</div>
                <div class="extracted-data-content">
                    ${extractedData.emails ? `
                        <div class="extracted-data-item">
                            <span class="extracted-data-label">📧 Emails:</span>
                            ${extractedData.emails.slice(0, 3).join(', ')}
                            ${extractedData.emails.length > 3 ? ` (+${extractedData.emails.length - 3})` : ''}
                        </div>
                    ` : ''}
                    ${extractedData.phones ? `
                        <div class="extracted-data-item">
                            <span class="extracted-data-label">📞 Telefones:</span>
                            ${extractedData.phones.slice(0, 3).join(', ')}
                            ${extractedData.phones.length > 3 ? ` (+${extractedData.phones.length - 3})` : ''}
                        </div>
                    ` : ''}
                    ${extractedData.companies ? `
                        <div class="extracted-data-item">
                            <span class="extracted-data-label">🏢 Empresas:</span>
                            ${extractedData.companies.slice(0, 3).join(', ')}
                            ${extractedData.companies.length > 3 ? ` (+${extractedData.companies.length - 3})` : ''}
                        </div>
                    ` : ''}
                    ${extractedData.keywords ? `
                        <div class="extracted-data-item">
                            <span class="extracted-data-label">🔑 Palavras-chave:</span>
                            ${extractedData.keywords.slice(0, 5).join(', ')}
                            ${extractedData.keywords.length > 5 ? ` (+${extractedData.keywords.length - 5})` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        ` : ''}
    `;
    
    return div;
}

// Dashboard Functions
async function loadDashboard() {
    try {
        // Load system stats
        const healthResponse = await fetch(`${AppState.settings.apiEndpoint}/health`);
        const healthData = await healthResponse.json();
        
        updateSystemStatus(healthData);
        
        // Load active scans
        const activeResponse = await fetch(`${AppState.settings.apiEndpoint}/scans/active`);
        const activeData = await activeResponse.json();
        
        updateActiveScans(activeData);
        
        // Load recent searches
        const recentResponse = await fetch(`${AppState.settings.apiEndpoint}/results/recent`);
        const recentData = await recentResponse.json();
        
        updateRecentSearches(recentData);
        
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function updateSystemStatus(healthData) {
    const statusElement = elements.systemStatus;
    if (!statusElement) return;
    
    const status = healthData.status;
    const statusClass = status === 'healthy' ? 'healthy' : 
                         status === 'degraded' ? 'degraded' : 'unhealthy';
    
    statusElement.innerHTML = `
        <div class="status-item">
            <span class="status-indicator ${statusClass}"></span>
            <span class="status-text">Status: ${status}</span>
        </div>
        <div class="status-item">
            <span>Uptime: ${formatUptime(healthData.uptime || 0)}</span>
        </div>
        <div class="status-item">
            <span>Versão: ${healthData.version || 'N/A'}</span>
        </div>
    `;
}

function updateActiveScans(activeData) {
    const activeScansElement = elements.activeScans;
    if (!activeScansElement) return;
    
    const scans = activeData.active_scans || [];
    
    if (scans.length === 0) {
        activeScansElement.innerHTML = '<p class="no-data">Nenhuma busca ativa</p>';
        return;
    }
    
    activeScansElement.innerHTML = scans.map(scan => `
        <div class="scan-item">
            <div class="scan-query">${escapeHtml(scan.query)}</div>
            <div class="scan-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${scan.progress}%"></div>
                </div>
                <span>${Math.round(scan.progress)}%</span>
            </div>
            <div class="scan-status">${scan.current_step}</div>
        </div>
    `).join('');
}

function updateRecentSearches(recentData) {
    const recentSearchesElement = elements.recentSearches;
    if (!recentSearchesElement) return;
    
    const searches = recentData.history || [];
    
    if (searches.length === 0) {
        recentSearchesElement.innerHTML = '<p class="no-data">Nenhuma busca recente</p>';
        return;
    }
    
    recentSearchesElement.innerHTML = searches.map(search => `
        <div class="recent-search-item">
            <div class="recent-query">${escapeHtml(search.query)}</div>
            <div class="recent-meta">
                <span>${search.results_count} resultados</span>
                <span>${formatDate(search.created_at)}</span>
            </div>
        </div>
    `).join('');
}

// History Functions
async function loadHistory() {
    try {
        const response = await fetch(`${AppState.settings.apiEndpoint}/results/history`);
        const data = await response.json();
        
        displayHistory(data.history || []);
        
    } catch (error) {
        console.error('History load error:', error);
        elements.historyList.innerHTML = '<p class="no-data">Erro ao carregar histórico</p>';
    }
}

function displayHistory(historyItems) {
    const historyList = elements.historyList;
    if (!historyList) return;
    
    if (historyItems.length === 0) {
        historyList.innerHTML = '<p class="no-data">Nenhuma busca no histórico</p>';
        return;
    }
    
    historyList.innerHTML = historyItems.map(item => `
        <div class="history-item">
            <div class="history-query">${escapeHtml(item.query)}</div>
            <div class="history-meta">
                <span>${item.results_count} resultados</span>
                <span>${formatDate(item.created_at)}</span>
                <span>${(item.processing_time || 0).toFixed(2)}s</span>
            </div>
            <div class="history-actions">
                <button class="action-btn" onclick="rerunSearch('${escapeHtml(item.query)}')">
                    <span>🔄</span>
                    <span>Repetir</span>
                </button>
            </div>
        </div>
    `).join('');
}

function filterHistory() {
    const searchTerm = elements.historySearch?.value.toLowerCase() || '';
    const filterValue = elements.historyFilter?.value || '';
    
    const historyItems = document.querySelectorAll('.history-item');
    
    historyItems.forEach(item => {
        const query = item.querySelector('.history-query').textContent.toLowerCase();
        const date = item.querySelector('.history-meta').textContent;
        
        let show = true;
        
        if (searchTerm && !query.includes(searchTerm)) {
            show = false;
        }
        
        if (filterValue) {
            const itemDate = new Date(date);
            const now = new Date();
            
            switch(filterValue) {
                case 'today':
                    show = itemDate.toDateString() === now.toDateString();
                    break;
                case 'week':
                    show = (now - itemDate) < (7 * 24 * 60 * 60 * 1000);
                    break;
                case 'month':
                    show = (now - itemDate) < (30 * 24 * 60 * 60 * 1000);
                    break;
            }
        }
        
        item.style.display = show ? 'block' : 'none';
    });
}

async function rerunSearch(query) {
    elements.searchInput.value = query;
    showPage('search');
    await executeSearch();
}

// Settings Functions
function loadSettings() {
    // API Endpoint
    const apiEndpoint = document.getElementById('apiEndpoint');
    if (apiEndpoint) {
        apiEndpoint.value = AppState.settings.apiEndpoint;
    }
    
    // Theme
    const theme = document.getElementById('theme');
    if (theme) {
        theme.value = AppState.settings.theme;
    }
    
    // Language
    const language = document.getElementById('language');
    if (language) {
        language.value = AppState.settings.language;
    }
    
    // Default max results
    const defaultMaxResults = document.getElementById('defaultMaxResults');
    if (defaultMaxResults) {
        defaultMaxResults.value = AppState.settings.defaultMaxResults;
    }
    
    // Default sources
    const defaultSources = document.getElementById('defaultSources');
    if (defaultSources) {
        Array.from(defaultSources.options).forEach(option => {
            option.selected = AppState.settings.defaultSources.includes(option.value);
        });
    }
    
    // Auto cache
    const autoCache = document.getElementById('autoCache');
    if (autoCache) {
        autoCache.checked = AppState.settings.autoCache;
    }
    
    // Auto AI
    const autoAI = document.getElementById('autoAI');
    if (autoAI) {
        autoAI.checked = AppState.settings.autoAI;
    }
    
    // Results per page
    const resultsPerPage = document.getElementById('resultsPerPage');
    if (resultsPerPage) {
        resultsPerPage.value = AppState.settings.resultsPerPage;
    }
}

function saveSettings() {
    // Collect settings from form
    const apiEndpoint = document.getElementById('apiEndpoint')?.value;
    const theme = document.getElementById('theme')?.value;
    const language = document.getElementById('language')?.value;
    const defaultMaxResults = parseInt(document.getElementById('defaultMaxResults')?.value) || 100;
    const defaultSources = Array.from(document.getElementById('defaultSources')?.selectedOptions || [])
        .map(option => option.value);
    const autoCache = document.getElementById('autoCache')?.checked ?? true;
    const autoAI = document.getElementById('autoAI')?.checked ?? true;
    const resultsPerPage = parseInt(document.getElementById('resultsPerPage')?.value) || 50;
    
    // Update app state
    AppState.settings = {
        ...AppState.settings,
        apiEndpoint,
        theme,
        language,
        defaultMaxResults,
        defaultSources,
        autoCache,
        autoAI,
        resultsPerPage
    };
    
    // Save to localStorage
    localStorage.setItem('omniscient_settings', JSON.stringify(AppState.settings));
    
    // Apply theme
    applyTheme(theme);
    
    // Show success message
    showSuccess('Configurações salvas com sucesso!');
}

function resetSettings() {
    if (confirm('Tem certeza que deseja restaurar as configurações padrão?')) {
        AppState.settings = {
            apiEndpoint: 'http://localhost:8000/api/v1',
            theme: 'dark',
            language: 'pt-BR',
            autoCache: true,
            autoAI: true,
            defaultMaxResults: 100,
            defaultSources: ['web', 'social', 'knowledge', 'news'],
            resultsPerPage: 50
        };
        
        localStorage.setItem('omniscient_settings', JSON.stringify(AppState.settings));
        loadSettings();
        applyTheme(AppState.settings.theme);
        
        showSuccess('Configurações restauradas com sucesso!');
    }
}

function clearLocalData() {
    if (confirm('Tem certeza que deseja limpar todos os dados locais?')) {
        localStorage.clear();
        sessionStorage.clear();
        
        // Reset app state
        AppState.searchResults = null;
        AppState.currentSearch = null;
        AppState.user = null;
        AppState.token = null;
        
        // Reload page
        location.reload();
    }
}

// Authentication Functions
function toggleUserDropdown() {
    elements.userDropdown.classList.toggle('show');
}

function showLoginModal() {
    showModal('loginModal');
}

function showRegisterModal() {
    // For now, just show login modal with different title
    const modal = document.getElementById('loginModal');
    const title = modal.querySelector('h3');
    if (title) {
        title.textContent = '📝 Registrar';
    }
    showModal('loginModal');
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showError('Por favor, preencha todos os campos');
        return;
    }
    
    try {
        const response = await fetch(`${AppState.settings.apiEndpoint}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            throw new Error('Credenciais inválidas');
        }
        
        const data = await response.json();
        
        // Save token and user info
        AppState.token = data.access_token;
        AppState.user = { username };
        
        localStorage.setItem('omniscient_token', data.access_token);
        localStorage.setItem('omniscient_user', JSON.stringify(AppState.user));
        
        // Update UI
        updateUserUI();
        hideModal('loginModal');
        showSuccess('Login realizado com sucesso!');
        
    } catch (error) {
        console.error('Login error:', error);
        showError('Erro no login: ' + error.message);
    }
}

function logout() {
    AppState.token = null;
    AppState.user = null;
    
    localStorage.removeItem('omniscient_token');
    localStorage.removeItem('omniscient_user');
    
    updateUserUI();
    showSuccess('Logout realizado com sucesso!');
}

function checkAuthStatus() {
    const token = localStorage.getItem('omniscient_token');
    const user = localStorage.getItem('omniscient_user');
    
    if (token && user) {
        AppState.token = token;
        AppState.user = JSON.parse(user);
        updateUserUI();
    }
}

function updateUserUI() {
    const username = document.querySelector('.username');
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (AppState.user) {
        if (username) {
            username.textContent = AppState.user.username;
        }
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'block';
    } else {
        if (username) {
            username.textContent = 'Convidado';
        }
        if (loginBtn) loginBtn.style.display = 'block';
        if (registerBtn) registerBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

// Export Functions
function showExportModal() {
    if (!AppState.currentSearch) {
        showError('Nenhum resultado para exportar');
        return;
    }
    
    showModal('exportModal');
}

async function exportResults() {
    const format = elements.exportFormat?.value || 'json';
    const includeExtractedData = document.getElementById('includeExtractedData')?.checked ?? true;
    const includeSummary = document.getElementById('includeSummary')?.checked ?? true;
    const includeStats = document.getElementById('includeStats')?.checked ?? true;
    
    try {
        // This would call the export API
        const exportData = {
            format,
            include_extracted_data: includeExtractedData,
            include_summary: includeSummary,
            include_stats: includeStats
        };
        
        // Simulate export (in real implementation, call API)
        const dataStr = JSON.stringify(AppState.currentSearch, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `omniscient_search_${Date.now()}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        hideModal('exportModal');
        showSuccess('Resultados exportados com sucesso!');
        
    } catch (error) {
        console.error('Export error:', error);
        showError('Erro na exportação: ' + error.message);
    }
}

// Utility Functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }
}

function showError(message) {
    // Create toast notification
    showToast(message, 'error');
}

function showSuccess(message) {
    // Create toast notification
    showToast(message, 'success');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    Object.assign(toast.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        borderRadius: '8px',
        fontWeight: '600',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease',
        backgroundColor: type === 'error' ? 'var(--error-color)' :
                         type === 'success' ? 'var(--success-color)' :
                         'var(--info-color)',
        color: 'white',
        boxShadow: 'var(--shadow-lg)',
        maxWidth: '300px'
    });
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function applyTheme(theme) {
    if (theme === 'light') {
        document.documentElement.style.setProperty('--bg-primary', '#ffffff');
        document.documentElement.style.setProperty('--bg-secondary', '#f5f5f5');
        document.documentElement.style.setProperty('--bg-tertiary', '#e0e0e0');
        document.documentElement.style.setProperty('--text-primary', '#333333');
        document.documentElement.style.setProperty('--text-secondary', '#666666');
        document.documentElement.style.setProperty('--text-muted', '#999999');
        document.documentElement.style.setProperty('--border-color', '#cccccc');
    } else {
        // Reset to dark theme (default)
        document.documentElement.style.removeProperty('--bg-primary');
        document.documentElement.style.removeProperty('--bg-secondary');
        document.documentElement.style.removeProperty('--bg-tertiary');
        document.documentElement.style.removeProperty('--text-primary');
        document.documentElement.style.removeProperty('--text-secondary');
        document.documentElement.style.removeProperty('--text-muted');
        document.documentElement.style.removeProperty('--border-color');
    }
}

function formatMarkdown(text) {
    // Simple markdown to HTML conversion
    return text
        .replace(/^### (.*$)/gim, '<h4>$1</h4>')
        .replace(/^## (.*$)/gim, '<h3>$1</h3>')
        .replace(/^# (.*$)/gim, '<h2>$1</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^(.+)$/gm, '<p>$1</p>')
        .replace(/<p><\/p>/g, '')
        .replace(/<p>(<h[1-6]>)/g, '$1')
        .replace(/(<\/h[1-6]>)<\/p>/g, '$1')
        .replace(/<p>(<li>)/g, '<ul>$1')
        .replace(/(<\/li>)<\/p>/g, '$1</ul>');
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `${days} dia${days > 1 ? 's' : ''} atrás`;
    } else if (hours > 0) {
        return `${hours} hora${hours > 1 ? 's' : ''} atrás`;
    } else if (minutes > 0) {
        return `${minutes} minuto${minutes > 1 ? 's' : ''} atrás`;
    } else {
        return 'Agora';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addToHistory(query, result) {
    const history = JSON.parse(localStorage.getItem('omniscient_history') || '[]');
    
    history.unshift({
        query,
        result,
        timestamp: Date.now()
    });
    
    // Keep only last 100 items
    if (history.length > 100) {
        history.splice(100);
    }
    
    localStorage.setItem('omniscient_history', JSON.stringify(history));
}

function clearHistory() {
    if (confirm('Tem certeza que deseja limpar o histórico?')) {
        localStorage.removeItem('omniscient_history');
        loadHistory();
        showSuccess('Histórico limpo com sucesso!');
    }
}

// System Stats Updates
async function updateSystemStats() {
    try {
        const response = await fetch(`${AppState.settings.apiEndpoint}/health`);
        const healthData = await response.json();
        
        // Update metrics in UI
        if (healthData.system_metrics) {
            const metrics = healthData.system_metrics;
            
            if (metrics.system && metrics.system.cpu) {
                elements.cpuMetric.textContent = `${Math.round(metrics.system.cpu.percent)}%`;
            }
            
            if (metrics.system && metrics.system.memory) {
                elements.memoryMetric.textContent = `${Math.round(metrics.system.memory.percent)}%`;
            }
            
            if (metrics.system && metrics.system.disk) {
                elements.diskMetric.textContent = `${Math.round(metrics.system.disk.percent)}%`;
            }
            
            if (metrics.orchestrator && metrics.orchestrator.hit_rate) {
                elements.cacheMetric.textContent = `${Math.round(metrics.orchestrator.hit_rate)}%`;
            }
        }
        
    } catch (error) {
        console.error('Error updating system stats:', error);
    }
}

function initializeUI() {
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        .toast {
            transform: translateX(100%);
        }
        
        .toast-error {
            background: var(--error-color) !important;
        }
        
        .toast-success {
            background: var(--success-color) !important;
        }
        
        .toast-info {
            background: var(--info-color) !important;
        }
    `;
    document.head.appendChild(style);
}

// Make functions globally available
window.rerunSearch = rerunSearch;
window.showPage = showPage;
window.executeSearch = executeSearch;
