// Configuration
const API_BASE_URL = 'http://localhost:8000';
const ITEMS_PER_PAGE = 10;

// State
let state = {
    hackathons: [],
    currentPage: 1,
    searchQuery: '',
    isSearchAI: false,
    isLoggedIn: false,
    userToken: null,
};

// UI Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const aiSearchBtn = document.getElementById('aiSearchBtn');
const refreshBtn = document.getElementById('refreshBtn');
const hackathonsList = document.getElementById('hackathonsList');
const messageBox = document.getElementById('messageBox');
const loadingIndicator = document.getElementById('loadingIndicator');
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const loginModal = document.getElementById('loginModal');
const detailModal = document.getElementById('detailModal');
const loginForm = document.getElementById('loginForm');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
const pageInfo = document.getElementById('pageInfo');
const closeButtons = document.querySelectorAll('.close');

// Event Listeners
searchBtn.addEventListener('click', () => handleSearch(false));
aiSearchBtn.addEventListener('click', () => handleSearch(true));
refreshBtn.addEventListener('click', handleRefresh);
loginBtn.addEventListener('click', openLoginModal);
logoutBtn.addEventListener('click', handleLogout);
loginForm.addEventListener('submit', handleLogin);
nextBtn.addEventListener('click', () => changePage(1));
prevBtn.addEventListener('click', () => changePage(-1));
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch(false);
});

// Close modals
closeButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.target.closest('.modal').style.display = 'none';
    });
});

// Modal close on outside click
window.addEventListener('click', (e) => {
    if (e.target === loginModal) loginModal.style.display = 'none';
    if (e.target === detailModal) detailModal.style.display = 'none';
});

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    checkLoginStatus();
    loadHackathons();
});

// API Functions
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (state.userToken) {
        headers['Authorization'] = `Bearer ${state.userToken}`;
    }

    try {
        showLoading(true);
        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    } finally {
        showLoading(false);
    }
}

// Hackathon Functions
async function loadHackathons() {
    try {
        const skip = (state.currentPage - 1) * ITEMS_PER_PAGE;
        const data = await apiCall(`/hackathons?skip=${skip}&limit=${ITEMS_PER_PAGE}`);
        state.hackathons = data;
        renderHackathons(data);
        updatePagination();
    } catch (error) {
        showMessage(`Error loading hackathons: ${error.message}`, 'error');
    }
}

async function handleSearch(isAI) {
    const query = searchInput.value.trim();
    if (!query) {
        showMessage('Please enter a search query', 'error');
        return;
    }

    try {
        state.searchQuery = query;
        state.isSearchAI = isAI;
        state.currentPage = 1;

        const endpoint = isAI
            ? `/hackathons/search/ai?q=${encodeURIComponent(query)}&limit=${ITEMS_PER_PAGE}`
            : `/hackathons/search/query?q=${encodeURIComponent(query)}&limit=${ITEMS_PER_PAGE}`;

        const data = await apiCall(endpoint);
        state.hackathons = data;
        renderHackathons(data);
        updatePagination();
        showMessage(`Found ${data.length} hackathons`, 'success');
    } catch (error) {
        showMessage(`Search error: ${error.message}`, 'error');
    }
}

async function handleRefresh() {
    try {
        const result = await apiCall('/hackathons/parse/update', {
            method: 'POST',
        });

        const message = `Parser Update:
- Total found: ${result.total_found}
- Added: ${result.total_added}
- Duplicates skipped: ${result.duplicates_skipped}
${result.errors.length > 0 ? `\nErrors: ${result.errors.length}` : ''}`;

        showMessage(message, result.errors.length === 0 ? 'success' : 'info');

        // Reload hackathons
        state.currentPage = 1;
        loadHackathons();
    } catch (error) {
        showMessage(`Refresh error: ${error.message}`, 'error');
    }
}

function renderHackathons(hackathons) {
    if (hackathons.length === 0) {
        hackathonsList.innerHTML = '<div class="empty-state"><h2>No hackathons found</h2><p>Try adjusting your search or refresh the data</p></div>';
        return;
    }

    hackathonsList.innerHTML = hackathons.map(h => `
        <div class="hackathon-card" onclick="showDetail(${h.id})">
            <h3>${escapeHtml(h.title)}</h3>
            <p>${escapeHtml((h.description || '').substring(0, 100))}${h.description && h.description.length > 100 ? '...' : ''}</p>

            <div class="hackathon-meta">
                ${h.format ? `<span class="meta-tag">${escapeHtml(h.format)}</span>` : ''}
                ${h.location ? `<span class="meta-tag">📍 ${escapeHtml(h.location)}</span>` : ''}
                ${h.source ? `<span class="meta-tag">From: ${escapeHtml(h.source)}</span>` : ''}
            </div>

            ${h.technologies && h.technologies.length > 0 ? `
                <div class="tech-tags">
                    ${h.technologies.slice(0, 3).map(t => `<span class="tech-tag">${escapeHtml(t)}</span>`).join('')}
                    ${h.technologies.length > 3 ? `<span class="tech-tag">+${h.technologies.length - 3} more</span>` : ''}
                </div>
            ` : ''}

            ${h.url ? `<a href="${h.url}" target="_blank" class="hackathon-url" onclick="event.stopPropagation()">Visit →</a>` : ''}
        </div>
    `).join('');
}

async function showDetail(id) {
    try {
        const hackathon = await apiCall(`/hackathons/${id}`);
        const detailContent = `
            <h2>${escapeHtml(hackathon.title)}</h2>

            ${hackathon.description ? `
                <div class="detail-section">
                    <div class="detail-label">Description</div>
                    <div class="detail-value">${escapeHtml(hackathon.description)}</div>
                </div>
            ` : ''}

            ${hackathon.start_date ? `
                <div class="detail-section">
                    <div class="detail-label">Start Date</div>
                    <div class="detail-value">${new Date(hackathon.start_date).toLocaleDateString()}</div>
                </div>
            ` : ''}

            ${hackathon.end_date ? `
                <div class="detail-section">
                    <div class="detail-label">End Date</div>
                    <div class="detail-value">${new Date(hackathon.end_date).toLocaleDateString()}</div>
                </div>
            ` : ''}

            ${hackathon.registration_deadline ? `
                <div class="detail-section">
                    <div class="detail-label">Registration Deadline</div>
                    <div class="detail-value">${new Date(hackathon.registration_deadline).toLocaleDateString()}</div>
                </div>
            ` : ''}

            ${hackathon.location ? `
                <div class="detail-section">
                    <div class="detail-label">Location</div>
                    <div class="detail-value">${escapeHtml(hackathon.location)}</div>
                </div>
            ` : ''}

            ${hackathon.url ? `
                <div class="detail-section">
                    <div class="detail-label">URL</div>
                    <div class="detail-value"><a href="${hackathon.url}" target="_blank" class="hackathon-url">${escapeHtml(hackathon.url)}</a></div>
                </div>
            ` : ''}

            ${hackathon.technologies && hackathon.technologies.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-label">Technologies</div>
                    <div class="tech-tags">${hackathon.technologies.map(t => `<span class="tech-tag">${escapeHtml(t)}</span>`).join('')}</div>
                </div>
            ` : ''}

            ${state.isLoggedIn ? `
                <div class="detail-section">
                    <button class="btn btn-accent" onclick="addToCalendar(${id})">📅 Add to Google Calendar</button>
                </div>
            ` : ''}
        `;
        document.getElementById('hackathonDetail').innerHTML = detailContent;
        detailModal.style.display = 'flex';
    } catch (error) {
        showMessage(`Error loading details: ${error.message}`, 'error');
    }
}

async function addToCalendar(hackathonId) {
    try {
        const result = await apiCall('/calendar/add-hackathon', {
            method: 'POST',
            body: JSON.stringify({ hackathon_id: hackathonId }),
        });
        showMessage('Added to Google Calendar!', 'success');
    } catch (error) {
        showMessage(`Calendar error: ${error.message}`, 'error');
    }
}

// Auth Functions
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('emailInput').value;
    const name = document.getElementById('nameInput').value;

    try {
        const response = await apiCall('/auth/dev-login', {
            method: 'POST',
            body: JSON.stringify({ email, name }),
        });

        state.userToken = response.access_token;
        localStorage.setItem('userToken', state.userToken);
        state.isLoggedIn = true;

        loginModal.style.display = 'none';
        loginForm.reset();
        updateAuthButtons();
        showMessage('Logged in successfully!', 'success');
    } catch (error) {
        showMessage(`Login error: ${error.message}`, 'error');
    }
}

function handleLogout() {
    state.userToken = null;
    state.isLoggedIn = false;
    localStorage.removeItem('userToken');
    updateAuthButtons();
    showMessage('Logged out', 'success');
}

function checkLoginStatus() {
    const token = localStorage.getItem('userToken');
    if (token) {
        state.userToken = token;
        state.isLoggedIn = true;
        updateAuthButtons();
    }
}

function updateAuthButtons() {
    if (state.isLoggedIn) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
    } else {
        loginBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
    }
}

function openLoginModal() {
    loginModal.style.display = 'flex';
}

// UI Functions
function changePage(direction) {
    state.currentPage += direction;
    if (state.searchQuery) {
        handleSearch(state.isSearchAI);
    } else {
        loadHackathons();
    }
}

function updatePagination() {
    pageInfo.textContent = `Page ${state.currentPage}`;
    prevBtn.style.display = state.currentPage > 1 ? 'block' : 'none';
    nextBtn.style.display = state.hackathons.length === ITEMS_PER_PAGE ? 'block' : 'none';
}

function showMessage(text, type = 'info') {
    messageBox.className = `message-box ${type}`;
    messageBox.textContent = text;
    messageBox.style.display = 'block';

    setTimeout(() => {
        messageBox.style.display = 'none';
    }, 4000);
}

function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
