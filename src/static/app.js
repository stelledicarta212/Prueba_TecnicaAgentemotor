// Global State (SQLite & API remain the source of truth, no LocalStorage used)
let dashboardData = null;
let currentFilter = 'all';
let searchQuery = '';

// DOM Elements
const policiesContainer = document.getElementById('policies-container');
const loadingSpinner = document.getElementById('loading-spinner');
const errorBanner = document.getElementById('error-banner');
const errorMessage = document.getElementById('error-message');
const emptyState = document.getElementById('empty-state');
const searchInput = document.getElementById('search-input');
const toastContainer = document.getElementById('toast-container');

// Stats DOM Elements
const statTotal = document.getElementById('stat-total');
const statProxima = document.getElementById('stat-proxima');
const statCritica = document.getElementById('stat-critica');
const statNueva = document.getElementById('stat-nueva');
const statRenovada = document.getElementById('stat-renovada');

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    // Theme initialization
    const savedTheme = localStorage.getItem('theme');
    const themeIcon = document.getElementById('theme-icon');
    const themeToggle = document.getElementById('theme-toggle');

    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        if (themeIcon) themeIcon.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-theme');
        if (themeIcon) themeIcon.textContent = '🌙';
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            if (themeIcon) {
                themeIcon.textContent = isDark ? '☀️' : '🌙';
            }
        });
    }

    // Search input listener with basic event handling
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderPolicies();
    });

    // Load initial data
    loadDashboard();
});

// Load dashboard data from the API
async function loadDashboard() {
    showLoading(true);
    showError(false);
    showEmptyState(false);

    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) {
            throw new Error(`Error en el servidor: ${response.status} ${response.statusText}`);
        }
        
        dashboardData = await response.json();
        
        // Update Advisor Name if available
        if (dashboardData.policies && dashboardData.policies.length > 0) {
            const advisorName = dashboardData.policies[0].advisor?.name;
            if (advisorName) {
                document.getElementById('advisor-name').textContent = advisorName;
                document.querySelector('.avatar').textContent = getInitials(advisorName);
            }
        }

        updateStats(dashboardData.summary);
        renderPolicies();
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showError(true, error.message);
        showToast('No se pudieron cargar los datos del servidor.', 'error');
    } finally {
        showLoading(false);
    }
}

// Update stats in KPI cards
function updateStats(summary) {
    if (!summary) return;
    
    statTotal.textContent = summary.total || 0;
    statProxima.textContent = summary.proxima_a_vencer || 0;
    statCritica.textContent = summary.ventana_critica || 0;
    statNueva.textContent = summary.nueva_contratacion || 0;
    statRenovada.textContent = summary.renovada || 0;
}

// Tab and KPI card filter selection
function filterByPriority(priority) {
    currentFilter = priority;
    
    // Update active tab styles
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        if (tab.id === `tab-${priority}`) {
            tab.classList.add('active');
        } else if (priority === 'all' && tab.id === 'tab-all') {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update active card border/styles if desired
    const cards = document.querySelectorAll('.metric-card');
    cards.forEach(card => {
        if (card.dataset.filter === priority) {
            card.style.transform = 'translateY(-4px)';
            card.style.boxShadow = 'var(--shadow-md)';
        } else {
            card.style.transform = '';
            card.style.boxShadow = '';
        }
    });

    renderPolicies();
}

// Render filtered policy list
function renderPolicies() {
    policiesContainer.innerHTML = '';
    
    if (!dashboardData || !dashboardData.policies) {
        showEmptyState(true);
        return;
    }

    // Filter policies
    const filteredPolicies = dashboardData.policies.filter(policy => {
        // Priority filter
        if (currentFilter !== 'all' && policy.priority !== currentFilter) {
            return false;
        }

        // Search query filter (search by name, policy number, insurer)
        if (searchQuery) {
            const clientName = (policy.client?.full_name || '').toLowerCase();
            const policyNum = (policy.policy_number || '').toLowerCase();
            const insurer = (policy.insurer || '').toLowerCase();
            const insuranceType = (policy.insurance_type || '').toLowerCase();
            
            return clientName.includes(searchQuery) || 
                   policyNum.includes(searchQuery) || 
                   insurer.includes(searchQuery) ||
                   insuranceType.includes(searchQuery);
        }

        return true;
    });

    if (filteredPolicies.length === 0) {
        showEmptyState(true);
        return;
    }

    showEmptyState(false);

    // Create cards for each policy
    filteredPolicies.forEach(policy => {
        const card = document.createElement('article');
        card.className = `policy-card priority-${policy.priority}`;
        
        // Format Priority Badge
        const priorityLabels = {
            'proxima_a_vencer': 'Próxima a vencer',
            'ventana_critica': 'Ventana crítica',
            'nueva_contratacion': 'Nueva contratación',
            'renovada': 'Renovada',
            'sin_prioridad': 'Sin prioridad'
        };
        const priorityLabel = priorityLabels[policy.priority] || policy.priority;

        // Render contact history attempts (if any)
        let historyHtml = '<div class="empty-history">Sin gestiones registradas</div>';
        if (policy.contact_attempts && policy.contact_attempts.length > 0) {
            historyHtml = `<div class="history-timeline">`;
            policy.contact_attempts.forEach(attempt => {
                const channelIcons = {
                    'call': '📞',
                    'email': '✉️',
                    'message': '💬'
                };
                const channelIcon = channelIcons[attempt.channel] || '👤';
                const attemptDate = formatDate(attempt.attempted_at);
                
                historyHtml += `
                    <div class="timeline-item channel-${attempt.channel}">
                        <div class="timeline-dot"></div>
                        <div class="timeline-content">
                            <span class="timeline-meta">${channelIcon} ${attemptDate} - <strong>${attempt.result}</strong></span>
                            ${attempt.notes ? `<span class="timeline-notes">"${attempt.notes}"</span>` : ''}
                        </div>
                    </div>
                `;
            });
            historyHtml += `</div>`;
        }

        // Render card action buttons dynamically depending on renewal status
        let actionsHtml = '';
        if (policy.renewal_status === 'pending') {
            actionsHtml = `
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick="openGestionModal(${policy.id})">
                        <span>📝</span> Registrar Gestión
                    </button>
                    <button class="btn btn-primary" onclick="openRenewModal(${policy.id})">
                        <span>🔄</span> Renovar
                    </button>
                </div>
            `;
        } else {
            const renewalDate = formatDate(policy.renewed_at);
            actionsHtml = `
                <div class="card-actions">
                    <div class="renewed-banner">
                        <span>✨</span> Renovada el ${renewalDate}
                    </div>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="card-header-row">
                <div class="header-policy-info">
                    <span class="policy-number">${policy.policy_number}</span>
                    <div class="header-actions-inline">
                        <button class="btn-icon-inline" onclick="openEditPolicyModal(${policy.id})" title="Editar Póliza">✏️</button>
                        <button class="btn-icon-inline btn-archive" onclick="confirmArchivePolicy(${policy.id}, '${policy.policy_number}')" title="Archivar Póliza">📦</button>
                    </div>
                </div>
                <span class="priority-badge">${priorityLabel}</span>
            </div>
            
            <div class="card-section client-info">
                <h4>${policy.client?.full_name || 'Sin Nombre'}</h4>
                <div class="info-item">
                    <span>📞</span>
                    <a href="tel:${policy.client?.phone}">${policy.client?.phone || 'No registra'}</a>
                </div>
                <div class="info-item">
                    <span>✉️</span>
                    <a href="mailto:${policy.client?.email}">${policy.client?.email || 'No registra'}</a>
                </div>
            </div>

            <div class="card-section">
                <div class="policy-details">
                    <span class="detail-label">Aseguradora:</span>
                    <span class="detail-val">${policy.insurer || 'N/A'}</span>
                </div>
                <div class="policy-details">
                    <span class="detail-label">Ramo:</span>
                    <span class="detail-val">${policy.insurance_type}</span>
                </div>
                <div class="date-highlight">
                    <span class="expiration-label">Vencimiento:</span>
                    <span class="expiration-date">${formatDate(policy.expiration_date)}</span>
                </div>
            </div>

            <div class="card-section history-section">
                <h5>Historial de Gestiones</h5>
                ${historyHtml}
            </div>

            ${actionsHtml}
        `;
        
        policiesContainer.appendChild(card);
    });
}

// Modal: Open Registrar Gestión
function openGestionModal(policyId) {
    const policy = dashboardData.policies.find(p => p.id === policyId);
    if (!policy) return;

    document.getElementById('gestion-policy-id').value = policy.id;
    document.getElementById('gestion-policy-info').textContent = `${policy.policy_number} | ${policy.client?.full_name}`;
    
    // Clear inputs
    const radios = document.getElementsByName('channel');
    radios.forEach(radio => radio.checked = false);
    document.getElementById('gestion-result').selectedIndex = 0;
    document.getElementById('gestion-notes').value = '';
    
    // Auto-populate local date time
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(now - offset)).toISOString().slice(0, 16);
    document.getElementById('gestion-date').value = localISOTime;

    document.getElementById('modal-gestion').classList.remove('hidden');
}

// Modal: Open Renovar Póliza
function openRenewModal(policyId) {
    const policy = dashboardData.policies.find(p => p.id === policyId);
    if (!policy) return;

    document.getElementById('renew-policy-id').value = policy.id;
    document.getElementById('renew-policy-info').textContent = `${policy.policy_number} | ${policy.client?.full_name}`;
    
    // Default expiration date to 1 year from current expiration date
    const currentExp = new Date(policy.expiration_date);
    currentExp.setFullYear(currentExp.getFullYear() + 1);
    const defaultNewExp = currentExp.toISOString().split('T')[0];
    document.getElementById('renew-expiration-date').value = defaultNewExp;

    document.getElementById('modal-renew').classList.remove('hidden');
}

// Modal: Close
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// API Post: Registrar Gestión Commercial
async function submitGestion(event) {
    event.preventDefault();
    
    const policyId = parseInt(document.getElementById('gestion-policy-id').value);
    const channelInput = document.querySelector('input[name="channel"]:checked');
    const resultInput = document.getElementById('gestion-result');
    const notesInput = document.getElementById('gestion-notes');
    const dateInput = document.getElementById('gestion-date');

    if (!channelInput) {
        showToast('Debe seleccionar un canal de contacto.', 'error');
        return;
    }

    const payload = {
        policy_id: policyId,
        channel: channelInput.value,
        result: resultInput.value,
        notes: notesInput.value.trim() || null
    };

    // Format the date picker if defined, otherwise leave it blank to let backend handle it
    if (dateInput.value) {
        try {
            // Convert to YYYY-MM-DDTHH:MM:SS format
            const selectedDate = new Date(dateInput.value);
            payload.attempted_at = selectedDate.toISOString().slice(0, 19);
        } catch (e) {
            console.error('Invalid date format:', e);
        }
    }

    try {
        const response = await fetch('/api/contact-attempts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ocurrió un error al registrar la gestión.');
        }

        showToast('Gestión comercial registrada con éxito.', 'success');
        closeModal('modal-gestion');
        
        // Refresh dashboard from API
        await loadDashboard();
    } catch (error) {
        console.error('Error submitting contact attempt:', error);
        showToast(error.message, 'error');
    }
}

// API Post: Renovar Póliza
async function submitRenew(event) {
    event.preventDefault();

    const policyId = parseInt(document.getElementById('renew-policy-id').value);
    const expirationDate = document.getElementById('renew-expiration-date').value;

    if (!expirationDate) {
        showToast('Debe seleccionar una nueva fecha de vencimiento.', 'error');
        return;
    }

    const payload = {
        expiration_date: expirationDate
    };

    try {
        const response = await fetch(`/api/policies/${policyId}/renew`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ocurrió un error al renovar la póliza.');
        }

        showToast(`La póliza se renovó con éxito.`, 'success');
        closeModal('modal-renew');
        
        // Refresh dashboard from API
        await loadDashboard();
    } catch (error) {
        console.error('Error renewing policy:', error);
        showToast(error.message, 'error');
    }
}

// UI State Toggles
function showLoading(visible) {
    if (visible) {
        loadingSpinner.classList.remove('hidden');
    } else {
        loadingSpinner.classList.add('hidden');
    }
}

function showError(visible, msg = '') {
    if (visible) {
        errorMessage.textContent = msg || 'Ocurrió un error inesperado al conectar con el servidor.';
        errorBanner.classList.remove('hidden');
    } else {
        errorBanner.classList.add('hidden');
    }
}

function showEmptyState(visible) {
    if (visible) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
}

// Toast Notifications Helper
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        'success': '✨',
        'error': '⚠️',
        'info': 'ℹ️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || '⚡'}</span>
        <span class="toast-msg">${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto dismiss after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s reverse cubic-bezier(0.16, 1, 0.3, 1)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// General Utilities
function getInitials(name) {
    if (!name) return 'MG';
    const parts = name.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    
    // Simple display formatter for dates in standard format
    try {
        const d = new Date(dateStr.replace(' ', 'T'));
        if (isNaN(d.getTime())) {
            return dateStr; // fallback if string isn't parsed
        }
        
        // Month names in Spanish
        const months = [
            'ene', 'feb', 'mar', 'abr', 'may', 'jun',
            'jul', 'ago', 'sep', 'oct', 'nov', 'dic'
        ];
        
        const day = d.getDate();
        const month = months[d.getMonth()];
        const year = d.getFullYear();
        
        // If it includes time, append it
        if (dateStr.includes(':')) {
            const hours = String(d.getHours()).padStart(2, '0');
            const minutes = String(d.getMinutes()).padStart(2, '0');
            return `${day} ${month} ${year}, ${hours}:${minutes}`;
        }
        
        return `${day} ${month} ${year}`;
    } catch (e) {
        return dateStr;
    }
}

// Modal: Open Create Policy
function openCreatePolicyModal() {
    // Clear create policy form inputs
    document.getElementById('form-create-policy').reset();
    document.getElementById('modal-create-policy').classList.remove('hidden');
}

// API Post: Crear Cliente + Póliza
async function submitCreatePolicy(event) {
    event.preventDefault();

    const payload = {
        client: {
            full_name: document.getElementById('create-client-name').value.trim(),
            document_number: document.getElementById('create-client-document').value.trim() || null,
            email: document.getElementById('create-client-email').value.trim() || null,
            phone: document.getElementById('create-client-phone').value.trim() || null
        },
        policy: {
            policy_number: document.getElementById('create-policy-number').value.trim(),
            insurance_type: document.getElementById('create-policy-type').value,
            insurer: document.getElementById('create-policy-insurer').value.trim() || null,
            expiration_date: document.getElementById('create-policy-expiration').value
        }
    };

    try {
        const response = await fetch('/api/policies', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ocurrió un error al crear la póliza.');
        }

        showToast('Cliente y póliza creados exitosamente.', 'success');
        closeModal('modal-create-policy');
        
        // Refresh dashboard data
        await loadDashboard();
    } catch (error) {
        console.error('Error creating policy:', error);
        showToast(error.message, 'error');
    }
}

// Modal: Open Edit Policy
function openEditPolicyModal(policyId) {
    const policy = dashboardData.policies.find(p => p.id === policyId);
    if (!policy) return;

    document.getElementById('edit-policy-id').value = policy.id;
    document.getElementById('edit-client-name').value = policy.client?.full_name || '';
    document.getElementById('edit-client-document').value = policy.client?.document_number || '';
    document.getElementById('edit-client-email').value = policy.client?.email || '';
    document.getElementById('edit-client-phone').value = policy.client?.phone || '';

    document.getElementById('edit-policy-number').value = policy.policy_number;
    document.getElementById('edit-policy-type').value = policy.insurance_type;
    document.getElementById('edit-policy-insurer').value = policy.insurer || '';
    document.getElementById('edit-policy-expiration').value = policy.expiration_date;

    document.getElementById('modal-edit-policy').classList.remove('hidden');
}

// API Put: Editar Cliente + Póliza
async function submitEditPolicy(event) {
    event.preventDefault();

    const policyId = parseInt(document.getElementById('edit-policy-id').value);
    
    const payload = {
        client: {
            full_name: document.getElementById('edit-client-name').value.trim(),
            document_number: document.getElementById('edit-client-document').value.trim() || null,
            email: document.getElementById('edit-client-email').value.trim() || null,
            phone: document.getElementById('edit-client-phone').value.trim() || null
        },
        policy: {
            policy_number: document.getElementById('edit-policy-number').value.trim(),
            insurance_type: document.getElementById('edit-policy-type').value,
            insurer: document.getElementById('edit-policy-insurer').value.trim() || null,
            expiration_date: document.getElementById('edit-policy-expiration').value
        }
    };

    try {
        const response = await fetch(`/api/policies/${policyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ocurrió un error al actualizar la póliza.');
        }

        showToast('Datos actualizados exitosamente.', 'success');
        closeModal('modal-edit-policy');
        
        // Refresh dashboard data
        await loadDashboard();
    } catch (error) {
        console.error('Error updating policy:', error);
        showToast(error.message, 'error');
    }
}

// API Patch: Archivar Póliza
async function confirmArchivePolicy(policyId, policyNumber) {
    const isConfirmed = confirm(`¿Está seguro de que desea archivar la póliza ${policyNumber}?\nEsta acción la quitará de la vista de gestión activa.`);
    if (!isConfirmed) return;

    try {
        const response = await fetch(`/api/policies/${policyId}/archive`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ocurrió un error al archivar la póliza.');
        }

        showToast(`La póliza ${policyNumber} se archivó exitosamente.`, 'success');
        
        // Refresh dashboard data
        await loadDashboard();
    } catch (error) {
        console.error('Error archiving policy:', error);
        showToast(error.message, 'error');
    }
}
