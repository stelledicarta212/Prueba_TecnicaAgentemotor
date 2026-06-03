/**
 * ============================================================================
 * Agentemotor SPA Frontend Application Logic
 * ============================================================================
 * 
 * Principio Arquitectónico:
 * - SQLite es la ÚNICA fuente de verdad.
 * - No se almacena información crítica ni estado de negocio en LocalStorage.
 * - El frontend es reactivo: cada acción exitosa de escritura (creación, edición,
 *   archivación, renovación o gestión) refresca los datos mediante la API.
 * - Las prioridades de las pólizas se reciben precalculadas desde el Backend.
 */

// --- Estado Global de la Aplicación ---
let dashboardData = null; // Almacena la última respuesta íntegra de /api/dashboard
let currentFilter = 'all'; // Filtro de prioridad activo ('all', 'proxima_a_vencer', etc.)
let searchQuery = '';     // Filtro de texto de búsqueda activo (minúsculas y sin espacios extras)

// --- Referencias a Elementos DOM Comunes ---
const policiesContainer = document.getElementById('policies-container');
const loadingSpinner = document.getElementById('loading-spinner');
const errorBanner = document.getElementById('error-banner');
const errorMessage = document.getElementById('error-message');
const emptyState = document.getElementById('empty-state');
const searchInput = document.getElementById('search-input');
const toastContainer = document.getElementById('toast-container');

// --- Referencias a los Indicadores de las Tarjetas de Estadísticas (KPIs) ---
const statTotal = document.getElementById('stat-total');
const statProxima = document.getElementById('stat-proxima');
const statCritica = document.getElementById('stat-critica');
const statNueva = document.getElementById('stat-nueva');
const statRenovada = document.getElementById('stat-renovada');

/**
 * Evento de Inicio de la Aplicación (DOMContentLoaded)
 * Inicializa las preferencias visuales de tema y vincula los escuchadores base.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicialización y Carga de Tema Visual (Claro / Oscuro) desde LocalStorage
    const savedTheme = localStorage.getItem('theme');
    const themeIcon = document.getElementById('theme-icon');
    const themeToggle = document.getElementById('theme-toggle');

    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        if (themeIcon) themeIcon.textContent = '☀️'; // Sol para sugerir cambio a modo claro
    } else {
        document.body.classList.remove('dark-theme');
        if (themeIcon) themeIcon.textContent = '🌙'; // Luna para sugerir cambio a modo oscuro
    }

    // Vinculación de clic al selector de tema
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

    // 2. Vinculación del buscador en tiempo real (con filtrado reactivo)
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderPolicies();
    });

    // 3. Ejecución de carga inicial de datos desde la base de datos
    loadDashboard();
});

/**
 * Consulta de Datos Principal (GET /api/dashboard)
 * Recupera el listado y métricas de la base de datos SQLite y pobla la UI.
 */
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
        
        // Sincronización del perfil de usuario y avatar con el nombre del asesor actual
        if (dashboardData.policies && dashboardData.policies.length > 0) {
            const advisorName = dashboardData.policies[0].advisor?.name;
            if (advisorName) {
                document.getElementById('advisor-name').textContent = advisorName;
                document.querySelector('.avatar').textContent = getInitials(advisorName);
            }
        }

        // Actualización de KPIs y renderizado de tarjetas
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

/**
 * Actualiza los contadores numéricos de las tarjetas de resumen (KPIs)
 * @param {Object} summary - Resumen de pólizas clasificado por prioridad enviado por la API
 */
function updateStats(summary) {
    if (!summary) return;
    
    statTotal.textContent = summary.total || 0;
    statProxima.textContent = summary.proxima_a_vencer || 0;
    statCritica.textContent = summary.ventana_critica || 0;
    statNueva.textContent = summary.nueva_contratacion || 0;
    statRenovada.textContent = summary.renovada || 0;
}

/**
 * Filtra el listado de pólizas según la métrica seleccionada
 * @param {string} priority - Código de prioridad de la póliza ('all', 'ventana_critica', etc.)
 */
function filterByPriority(priority) {
    currentFilter = priority;
    
    // Sincroniza la clase activa de las pestañas (tabs)
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

    // Sincroniza el relieve visual de las tarjetas métricas (KPIs)
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

/**
 * Renderizado de Tarjetas de Pólizas en Pantalla
 * Filtra y crea la estructura DOM para cada póliza con sus respectivas acciones e historiales.
 */
function renderPolicies() {
    policiesContainer.innerHTML = '';
    
    if (!dashboardData || !dashboardData.policies) {
        showEmptyState(true);
        return;
    }

    // Aplica los filtros de prioridad y búsqueda de texto cruzadamente
    const filteredPolicies = dashboardData.policies.filter(policy => {
        // Filtro por prioridad
        if (currentFilter !== 'all' && policy.priority !== currentFilter) {
            return false;
        }

        // Filtro por texto en tiempo real
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

    // En caso de que el listado esté vacío para el filtro actual
    if (filteredPolicies.length === 0) {
        showEmptyState(true);
        return;
    }

    showEmptyState(false);

    // Iteración para construir cada tarjeta del grid
    filteredPolicies.forEach(policy => {
        const card = document.createElement('article');
        card.className = `policy-card priority-${policy.priority}`;
        
        // Mapeo amigable para el badge de prioridad comercial
        const priorityLabels = {
            'proxima_a_vencer': 'Próxima a vencer',
            'ventana_critica': 'Ventana crítica',
            'nueva_contratacion': 'Nueva contratación',
            'renovada': 'Renovada',
            'sin_prioridad': 'Sin prioridad'
        };
        const priorityLabel = priorityLabels[policy.priority] || policy.priority;

        // Renderizado del historial de intentos de contacto (Gestiones)
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

        // Renderizado condicionado de botones de acción en base a su renovación
        let actionsHtml = '';
        if (policy.renewal_status === 'pending') {
            actionsHtml = `
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick="openGestionModal(${policy.id})" title="Registrar un intento de llamada o contacto">
                        <span>📝</span> Registrar Gestión
                    </button>
                    <button class="btn btn-primary" onclick="openRenewModal(${policy.id})" title="Actualizar vigencia de la póliza">
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

        // Estructura interna de la tarjeta de póliza
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
                    <a href="tel:${policy.client?.phone}" title="Llamar por teléfono">${policy.client?.phone || 'No registra'}</a>
                </div>
                <div class="info-item">
                    <span>✉️</span>
                    <a href="mailto:${policy.client?.email}" title="Enviar correo electrónico">${policy.client?.email || 'No registra'}</a>
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

/**
 * Modal: Abre y configura el formulario para Registrar Gestión Comercial
 * @param {number} policyId - ID único de la póliza
 */
function openGestionModal(policyId) {
    const policy = dashboardData.policies.find(p => p.id === policyId);
    if (!policy) return;

    // Configuración de campos de control
    document.getElementById('gestion-policy-id').value = policy.id;
    document.getElementById('gestion-policy-info').textContent = `${policy.policy_number} | ${policy.client?.full_name}`;
    
    // Limpieza de inputs previos
    const radios = document.getElementsByName('channel');
    radios.forEach(radio => radio.checked = false);
    document.getElementById('gestion-result').selectedIndex = 0;
    document.getElementById('gestion-notes').value = '';
    
    // Autocompleta con la fecha y hora local del sistema actual en formato datetime-local
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(now - offset)).toISOString().slice(0, 16);
    document.getElementById('gestion-date').value = localISOTime;

    document.getElementById('modal-gestion').classList.remove('hidden');
}

/**
 * Modal: Abre y configura el formulario para Renovar Póliza
 * @param {number} policyId - ID único de la póliza
 */
function openRenewModal(policyId) {
    const policy = dashboardData.policies.find(p => p.id === policyId);
    if (!policy) return;

    // Configuración de campos de control
    document.getElementById('renew-policy-id').value = policy.id;
    document.getElementById('renew-policy-info').textContent = `${policy.policy_number} | ${policy.client?.full_name}`;
    
    // Proyecta la nueva fecha de vencimiento a 1 año después de su vencimiento actual
    const currentExp = new Date(policy.expiration_date);
    currentExp.setFullYear(currentExp.getFullYear() + 1);
    const defaultNewExp = currentExp.toISOString().split('T')[0];
    document.getElementById('renew-expiration-date').value = defaultNewExp;

    document.getElementById('modal-renew').classList.remove('hidden');
}

/**
 * Modal: Cierra cualquier modal abierto por su ID
 * @param {string} modalId - Atributo id del contenedor del modal
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

/**
 * API Post: Registra un nuevo intento de contacto (POST /api/contact-attempts)
 * @param {Event} event - Evento nativo del formulario onsubmit
 */
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

    // Si se especificó una fecha personalizada, se envía formateada como ISO
    if (dateInput.value) {
        try {
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
        
        // Recarga de datos para mantener SQLite como única fuente de verdad
        await loadDashboard();
    } catch (error) {
        console.error('Error submitting contact attempt:', error);
        showToast(error.message, 'error');
    }
}

/**
 * API Post: Renueva comercialmente una póliza (POST /api/policies/<id>/renew)
 * @param {Event} event - Evento nativo del formulario onsubmit
 */
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
        
        // Recarga de datos para mantener SQLite como única fuente de verdad
        await loadDashboard();
    } catch (error) {
        console.error('Error renewing policy:', error);
        showToast(error.message, 'error');
    }
}

/**
 * Modal: Abre el formulario limpio para Crear Cliente y Póliza
 */
function openCreatePolicyModal() {
    document.getElementById('form-create-policy').reset();
    document.getElementById('modal-create-policy').classList.remove('hidden');
}

/**
 * API Post: Registra un nuevo Cliente con su Póliza (POST /api/policies)
 * @param {Event} event - Evento nativo del formulario onsubmit
 */
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
        
        // Recarga de datos para mantener SQLite como única fuente de verdad
        await loadDashboard();
    } catch (error) {
        console.error('Error creating policy:', error);
        showToast(error.message, 'error');
    }
}

/**
 * Modal: Abre y precarga los campos existentes para Editar Cliente y Póliza
 * @param {number} policyId - ID único de la póliza a modificar
 */
function openEditPolicyModal(policyId) {
    const policy = dashboardData.policies.find(p => p.id === policyId);
    if (!policy) return;

    // Precarga de los inputs en el formulario
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

/**
 * API Put: Modifica los datos de Cliente + Póliza (PUT /api/policies/<id>)
 * @param {Event} event - Evento nativo del formulario onsubmit
 */
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
        
        // Recarga de datos para mantener SQLite como única fuente de verdad
        await loadDashboard();
    } catch (error) {
        console.error('Error updating policy:', error);
        showToast(error.message, 'error');
    }
}

/**
 * API Patch: Archiva lógicamente una póliza (PATCH /api/policies/<id>/archive)
 * @param {number} policyId - ID de la póliza
 * @param {string} policyNumber - Código o número identificador visible de la póliza
 */
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
        
        // Recarga de datos para mantener SQLite como única fuente de verdad
        await loadDashboard();
    } catch (error) {
        console.error('Error archiving policy:', error);
        showToast(error.message, 'error');
    }
}

// --- Métodos de Control Visual de Estados ---

/**
 * Muestra u oculta la animación de carga
 * @param {boolean} visible - Verdadero para mostrar, falso para ocultar
 */
function showLoading(visible) {
    if (visible) {
        loadingSpinner.classList.remove('hidden');
    } else {
        loadingSpinner.classList.add('hidden');
    }
}

/**
 * Muestra u oculta el banner de error crítico de API
 * @param {boolean} visible - Verdadero para mostrar
 * @param {string} msg - Texto descriptivo del error ocurrido
 */
function showError(visible, msg = '') {
    if (visible) {
        errorMessage.textContent = msg || 'Ocurrió un error inesperado al conectar con el servidor.';
        errorBanner.classList.remove('hidden');
    } else {
        errorBanner.classList.add('hidden');
    }
}

/**
 * Muestra u oculta la pantalla de "Sin resultados"
 * @param {boolean} visible - Verdadero para mostrar
 */
function showEmptyState(visible) {
    if (visible) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
}

// --- Componente: Notificaciones Flotantes (Toasts) ---

/**
 * Crea y anima un Toast en la esquina inferior derecha
 * @param {string} message - Mensaje visible del aviso
 * @param {string} type - Tipo de aviso para coloración ('success', 'error', 'info')
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        'success': '✨',
        'error': '⚠️',
        'info': 'ℹ️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon" aria-hidden="true">${icons[type] || '⚡'}</span>
        <span class="toast-msg">${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Desaparece y elimina el nodo DOM automáticamente tras 4 segundos
    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s reverse cubic-bezier(0.16, 1, 0.3, 1)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// --- Utilidades Generales ---

/**
 * Extrae las iniciales de un nombre completo para el avatar visual
 * @param {string} name - Nombre completo del asesor
 * @returns {string} Iniciales de dos caracteres
 */
function getInitials(name) {
    if (!name) return 'MG';
    const parts = name.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
}

/**
 * Formatea una fecha o fecha-hora en formato amigable e hispanohablante
 * @param {string} dateStr - Fecha ISO o cadena SQLite
 * @returns {string} Fecha formateada (ej. "15 jul 2026" o "15 jul 2026, 17:30")
 */
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    
    try {
        const d = new Date(dateStr.replace(' ', 'T'));
        if (isNaN(d.getTime())) {
            return dateStr;
        }
        
        const months = [
            'ene', 'feb', 'mar', 'abr', 'may', 'jun',
            'jul', 'ago', 'sep', 'oct', 'nov', 'dic'
        ];
        
        const day = d.getDate();
        const month = months[d.getMonth()];
        const year = d.getFullYear();
        
        // Agrega horas y minutos si la cadena original incluye marca de tiempo
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
