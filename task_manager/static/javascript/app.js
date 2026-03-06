const STORAGE_KEYS = {
    token: 'task_orchestrator_token',
    refresh: 'task_orchestrator_refresh',
};

const API_ROOT = '/api';

function getToken() {
    return localStorage.getItem(STORAGE_KEYS.token) || '';
}

function setTokens(access, refresh = '') {
    localStorage.setItem(STORAGE_KEYS.token, access || '');
    if (refresh) {
        localStorage.setItem(STORAGE_KEYS.refresh, refresh);
    }
}

function clearTokens() {
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.refresh);
}

async function apiRequest(path, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };

    const token = getToken();
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_ROOT}${path}`, {
        ...options,
        headers,
    });

    const payload = await response.json().catch(() => ({}));
    return { response, payload };
}

function authGuard({ redirectTo = '/auth/' } = {}) {
    if (!getToken()) {
        window.location.href = redirectTo;
    }
}

function bindLogout(buttonSelector = '[data-action="logout"]') {
    document.querySelectorAll(buttonSelector).forEach((button) => {
        button.addEventListener('click', () => {
            clearTokens();
            window.location.href = '/auth/';
        });
    });
}