const API_BASE = window.location.origin; // Dynamically use the current origin

// State
let authToken = localStorage.getItem("token");
let userRole = localStorage.getItem("role");
let currentUsername = localStorage.getItem("username");
let guestMessageCount = parseInt(localStorage.getItem("guestCount") || "0");
let currentGuestAgent = "auto";
let chatSessions = JSON.parse(localStorage.getItem("chat_sessions") || "[]");
let currentSessionId = null;
let currentAgent = "auto";

function isLoggedIn() {
    return !!authToken && authToken !== 'null' && authToken !== 'undefined' && !!userRole;
}


// DOM Elements
const views = {
    'main-scroll': document.getElementById('main-scroll-view'),
    'guest-chat': document.getElementById('guest-chat-view'),
    'login': document.getElementById('login-view'),
    'register': document.getElementById('register-view'),
    'reset': document.getElementById('reset-view'),
    'chat': document.getElementById('chat-view'),
    'admin': document.getElementById('admin-view'),
    'molecular': document.getElementById('molecular-view'),
    'profile': document.getElementById('profile-view')
};
const toastEl = document.getElementById('toast');

// App Initialization
function init() {
    // Restore or set default theme
    const savedTheme = localStorage.getItem("theme") || "dark";
    changeTheme(savedTheme, false);
    
    // Always show home page on startup regardless of login state
    showView('main-scroll');

    if (isLoggedIn()) {
        document.getElementById('current-role-badge').innerText = userRole.toUpperCase();
        
        // Restore Profile Details
        const profUsername = document.getElementById('profile-username');
        if (profUsername) profUsername.innerText = currentUsername;
        const prefTheme = document.getElementById('pref-theme');
        if (prefTheme) prefTheme.value = localStorage.getItem("theme") || "dark";
        const prefAgent = document.getElementById('pref-agent');
        if (prefAgent) prefAgent.value = localStorage.getItem("prefAgent") || "auto";
    }
    updateNavHeader();
    renderConversationList();
}

function scrollToSection(sectionId) {
    const mainView = document.getElementById('main-scroll-view');
    if (mainView.classList.contains('hidden')) {
        showView('main-scroll');
    }
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

function updateNavHeader() {
    if (isLoggedIn() && currentUsername) {
        document.getElementById("nav-unauth").classList.add("hidden");
        document.getElementById("nav-auth").classList.remove("hidden");
        document.getElementById("nav-user-display").innerText = currentUsername;
        
        // Update Profile Circle & Dropdown Header
        const iconEl = document.getElementById("nav-user-icon");
        if (iconEl) iconEl.innerText = currentUsername.charAt(0).toUpperCase();
        
        const dropName = document.getElementById("dropdown-user-name");
        if (dropName) dropName.innerText = currentUsername;
        
        const dropRole = document.getElementById("dropdown-user-role");
        if (dropRole) dropRole.innerText = userRole || "User";

        // Update Detailed Profile View
        const profName = document.getElementById("profile-username-val");
        if (profName) profName.innerText = currentUsername;
        
        const profRole = document.getElementById("profile-role-val");
        if (profRole) profRole.innerText = (userRole || "User").toUpperCase();
        document.getElementById("current-role-badge")?.classList.remove('hidden');
    } else {
        document.getElementById("nav-unauth").classList.remove("hidden");
        document.getElementById("nav-auth").classList.add("hidden");
        document.getElementById("current-role-badge")?.classList.add('hidden');
    }
}

// PROFILE SECTION NAVIGATION
function showProfileSection(section) {
    showView('profile');
    const main = document.getElementById('profile-section-main');
    const settings = document.getElementById('profile-section-settings');
    const title = document.getElementById('profile-title');
    const saveBtn = document.getElementById('profile-save-btn');

    if (section === 'profile') {
        main.classList.remove('hidden');
        settings.classList.add('hidden');
        title.innerText = "My Profile";
        saveBtn.classList.add('hidden'); // No need to save in readonly profile view
    } else {
        main.classList.add('hidden');
        settings.classList.remove('hidden');
        title.innerText = "Account Settings";
        saveBtn.classList.remove('hidden');
    }
    
    // Auto-close dropdown
    document.getElementById('profile-dropdown').classList.remove('show');
}


// Theme handling
function changeTheme(themeName, save = true) {
    document.documentElement.setAttribute('data-theme', themeName);
    if (save) localStorage.setItem('theme', themeName);
    
    const sel = document.getElementById('global-theme-select');
    if (sel) sel.value = themeName;
}

// UI Helpers
function showView(viewName) {
    // Security Guard: Prevent guests from entering authenticated views
    if (viewName === 'chat' || viewName === 'admin' || viewName === 'profile') {
        if (!isLoggedIn()) {
            console.warn("Unauthorized access attempt to " + viewName);
            showView('main-scroll');
            return;
        }
    }

    // TOGGLE NAVBAR: Molecular Explorer, Scientific Assistant, and Agents should feel like separate pages
    const standaloneViews = ['chat', 'guest-chat', 'molecular'];
    const navbar = document.querySelector('.app-navbar');
    if (navbar) {
        if (standaloneViews.includes(viewName)) {
            navbar.classList.add('navbar-hidden');
        } else {
            navbar.classList.remove('navbar-hidden');
        }
    }

    const targetId = viewName + '-view';
    
    // 1. Hide ALL views instantly
    Object.values(views).forEach(v => {
        if (!v) return;
        v.classList.add('hidden');
        v.classList.remove('active-view');
        // If it's the authenticated chat, explicitly hide the internal sidebar too
        if (v.id === 'chat-view') {
            const sidebar = v.querySelector('.chat-sidebar');
            if (sidebar) sidebar.style.display = 'none';
        }
    });
    
    // 2. Show the target view
    const target = views[viewName];
    if (target) {
        target.classList.remove('hidden');
        // Force a reflow for animations if needed
        void target.offsetWidth;
        target.classList.add('active-view');
        
        // 3. Special Case: Only show the sidebar if we are in 'chat' and logged in
        if (viewName === 'chat' && isLoggedIn()) {
            const sidebar = target.querySelector('.chat-sidebar');
            if (sidebar) sidebar.style.display = 'flex';
        }
    }
}

function showToast(msg, isError = false) {
    toastEl.textContent = msg;
    toastEl.className = `toast show ${isError ? 'error' : ''}`;
    setTimeout(() => toastEl.classList.remove('show'), 3000);
}

// --- NAVIGATION & PLATFORM ACCESS ---
function handleAccessPlatform() {
    scrollToSection('agents-hub-section');
}

function selectAgent(agentId, agentName) {
    if (!isLoggedIn()) {
        // Force clear guest history before switching
        const container = document.getElementById('guest-chat-history');
        if (container) container.innerHTML = '';
        localStorage.removeItem("guest_history");
    }

    if (isLoggedIn()) {
        openAuthenticatedAgent(agentId, agentName);
    } else {
        openGuestAgent(agentId, agentName);
    }
}

function openAuthenticatedAgent(agentId, agentName) {
    currentAgent = agentId;
    document.getElementById('chat-agent-label').innerText = agentName;
    
    const container = document.getElementById('chat-history');
    container.innerHTML = ''; // Force clear for fresh start as requested
    
    showView('chat');
    
    const welcome = agentId === 'auto' ? "Hi! I am the Scientific AI Assistant. How can I assist with your research today?" : `Hi! I am the ${agentName}. How can I assist with your domain-specific inquiry today?`;
    appendMessageToContainer(welcome, 'system', container, null, false);
    
    // Start a fresh session tracking
    currentSessionId = 'sess_' + Date.now();
    renderConversationList();
}

function openGeneralChat() {
    if (isLoggedIn()) {
        openAuthenticatedAgent('auto', 'Scientific AI Assistant');
    } else {
        openGuestAgent('auto', 'Scientific AI Assistant');
    }
}

// --- SESSION & HISTORY MANAGEMENT ---
function startNewChat(archiveCurrent = true) {
    if (isLoggedIn()) {
        const container = document.getElementById('chat-history');
        
        // Archive currently active chat if it has content
        if (archiveCurrent && currentSessionId && container.children.length > 0) {
            saveCurrentSession();
        }
        
        // Clear UI
        container.innerHTML = '';
        currentSessionId = 'sess_' + Date.now();
        
        // Re-add specialized greeting
        const agentName = document.getElementById('chat-agent-label').innerText;
        const welcome = currentAgent === 'auto' ? "Hi! I am the Scientific AI Assistant. How can I assist with your research today?" : `Hi! I am the ${agentName}. How can I assist with your domain-specific inquiry today?`;
        appendMessageToContainer(welcome, 'system', container, null, false);
        
        renderConversationList();
    } else {
        // Guest Mode Logic
        const container = document.getElementById('guest-chat-history');
        if (container) {
            container.innerHTML = '';
            guestMessageCount = 0;
            localStorage.setItem("guestCount", "0");
            localStorage.removeItem("guest_history");
            
            const guestCountEl = document.getElementById("guest-count");
            if (guestCountEl) guestCountEl.innerText = "0";
            
            // Re-add specialized greeting
            const fullTitle = document.getElementById("guest-agent-title").innerText;
            const agentName = fullTitle.includes(' (') ? fullTitle.split(' (')[0] : fullTitle;
            const welcome = currentGuestAgent === 'auto' ? "Hi! I am the Scientific AI Assistant. How can I assist with your research today?" : `Hi! I am the ${agentName}. How can I assist with your domain-specific inquiry today?`;
            appendMessageToContainer(welcome, 'system', container, null, false);
        }
    }
}

function saveCurrentSession() {
    const historyContainer = document.getElementById('chat-history');
    if (historyContainer.children.length === 0) return;

    const firstMsg = historyContainer.querySelector('.msg-bubble')?.innerText || "New Exploration";
    const title = firstMsg.split(' ').slice(0, 5).join(' ') + '...';
    
    const session = {
        id: currentSessionId,
        title: title,
        agent: currentAgent,
        timestamp: new Date().toLocaleString(),
        html: historyContainer.innerHTML
    };
    
    // Remove if already exists (update)
    chatSessions = chatSessions.filter(s => s.id !== currentSessionId);
    chatSessions.unshift(session);
    
    if (chatSessions.length > 50) chatSessions.pop(); // Cap history
    localStorage.setItem("chat_sessions", JSON.stringify(chatSessions));
    renderConversationList();
}

function loadSession(id) {
    const session = chatSessions.find(s => s.id === id);
    if (!session) return;
    
    // Save current before switching
    saveCurrentSession();
    
    currentSessionId = session.id;
    currentAgent = session.agent;
    document.getElementById('chat-agent-label').innerText = session.agent;
    document.getElementById('chat-history').innerHTML = session.html;
    
    showView('chat');
    renderConversationList();
}

function renderConversationList() {
    const list = document.getElementById('conversation-list');
    if (!list) return;
    
    list.innerHTML = '';
    chatSessions.forEach(session => {
        const item = document.createElement('div');
        item.className = `history-item ${session.id === currentSessionId ? 'active' : ''}`;
        item.innerHTML = `<i>📄</i> <span>${session.title}</span>`;
        item.onclick = () => loadSession(session.id);
        list.appendChild(item);
    });
}

// Global Nav Handlers
// Profile Dropdown Toggle
document.addEventListener('click', (e) => {
    const trigger = document.getElementById('profile-trigger');
    const dropdown = document.getElementById('profile-dropdown');
    
    if (trigger && trigger.contains(e.target)) {
        dropdown.classList.toggle('show');
    } else if (dropdown && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
    }
});

document.getElementById('nav-logout-btn').addEventListener('click', logout);
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    localStorage.removeItem("guest_history");
    authToken = null; userRole = null; currentUsername = null;
    guestMessageCount = 0;
    localStorage.setItem("guestCount", "0");
    changeTheme("dark");
    updateNavHeader();
    showView('main-scroll'); 
    showToast("Logout successful");
    loadGuestHistory();
}

function openGuestAgent(agentId, agentName) {
    currentGuestAgent = agentId;
    document.getElementById("guest-agent-title").innerText = agentId === 'auto' ? agentName : `${agentName} (${agentId})`;
    
    // Total isolation: Clear DOM and storage on every entry
    const container = document.getElementById('guest-chat-history');
    if (container) container.innerHTML = '';
    localStorage.removeItem("guest_history");
    localStorage.removeItem("guestCount"); // Optional: reset count too if wanted, but user didn't ask. 
    // Wait, the user said "chat history should not preserved"
    
    showView('guest-chat');
    const welcome = agentId === 'auto' ? "Hi! I am the Scientific AI Assistant. How can I assist with your research today?" : `Hi! I am the ${agentName}. How can I assist with your domain-specific inquiry today?`;
    appendMessageToContainer(welcome, 'system', container, null, false);
}


// --- LOGIN LOGIC ---
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    btn.innerHTML = `<span class="spinner"></span> Authenticating...`;
    
    const payload = {
        username: document.getElementById('login-username').value,
        password: document.getElementById('login-password').value,
        role: document.getElementById('login-role').value
    };

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (!res.ok) throw new Error(data.detail || 'Login failed');
        
        authToken = data.access_token;
        userRole = data.role;
        currentUsername = payload.username;
        localStorage.setItem("token", authToken);
        localStorage.setItem("role", userRole);
        localStorage.setItem("username", currentUsername);
        localStorage.setItem("prefAgent", "auto"); // Default on first login
        
        // Auto-switch to role-specific theme
        changeTheme(userRole);
        updateNavHeader();
        
        // Center-aligned "Login successful" message
        const successDiv = document.createElement('div');
        successDiv.style.cssText = "position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 9999; text-align: center; pointer-events: none;";
        successDiv.innerHTML = `<div class="glass" style="padding: 20px 40px; border: 2px solid var(--success); background: rgba(0,0,0,0.85); box-shadow: 0 0 25px rgba(0,230,118,0.3); animation: slideIn 0.4s easeOut;">
            <h1 style="color: var(--success); margin: 0; font-size: 1.5rem; font-weight: 700;">Login successful</h1>
        </div>`;
        document.body.appendChild(successDiv);
        setTimeout(() => {
            successDiv.style.opacity = '0';
            successDiv.style.transition = 'opacity 0.6s ease';
            setTimeout(() => successDiv.remove(), 600);
        }, 2000);

        document.getElementById('current-role-badge').innerText = userRole.toUpperCase();
        
        btn.innerHTML = `<span>Authenticate</span>`;
        showView('main-scroll');
        if (userRole === 'admin') fetchPendingApprovals();
        else loadChatHistory();
    } catch (err) {
        btn.innerHTML = `<span>Authenticate</span>`;
        showToast(err.message, true);
    }
});


// --- REGISTER LOGIC ---
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('reg-btn');
    btn.innerHTML = `<span class="spinner"></span> Working...`;
    
    const payload = {
        username: document.getElementById('reg-username').value,
        password: document.getElementById('reg-password').value,
        role: document.getElementById('reg-role').value
    };

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');
        
        showToast("Registration successful! You may now log in.");
        setTimeout(() => {
            document.getElementById('login-username').value = payload.username;
            document.getElementById('login-role').value = payload.role;
            btn.innerHTML = `<span>Register</span>`;
            showView('login');
        }, 1500);
    } catch (err) {
        btn.innerHTML = `<span>Register</span>`;
        showToast(err.message, true);
    }
});

// --- RESET PASSWORD LOGIC ---
document.getElementById('reset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('res-btn');
    btn.innerHTML = `<span class="spinner"></span> Working...`;
    
    const payload = {
        username: document.getElementById('res-username').value,
        password: document.getElementById('res-password').value,
        role: document.getElementById('res-role').value
    };

    try {
        const res = await fetch(`${API_BASE}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Reset failed');
        
        showToast("Password updated successfully!");
        setTimeout(() => {
            btn.innerHTML = `<span>Reset Password</span>`;
            showView('login');
        }, 1500);
    } catch (err) {
        btn.innerHTML = `<span>Reset Password</span>`;
        showToast(err.message, true);
    }
});


// --- SHARED CHAT LOGIC ---

function appendMessageToContainer(text, sender, container, storageKey = null, save = true) {
    const id = `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    const div = document.createElement('div');
    div.id = id;
    div.className = `message ${sender === 'user' ? 'user-msg' : 'system-msg'}`;
    div.innerHTML = `
        <div class="msg-avatar">${sender === 'user' ? 'U' : 'AI'}</div>
        <div class="msg-bubble">${text}</div>
    `;
    container.appendChild(div);
    container.scrollTo({top: container.scrollHeight, behavior: 'smooth'});
    
    if (save && storageKey) {
        const savedArr = JSON.parse(localStorage.getItem(storageKey) || "[]");
        savedArr.push({ text, sender });
        localStorage.setItem(storageKey, JSON.stringify(savedArr));
    }
    return id;
}


// --- GUEST QUERY LOGIC ---
document.getElementById('guest-query-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!authToken && guestMessageCount >= 10) {
        showToast("Guest limit of 10 messages reached! Please Login or Register to continue.", true);
        setTimeout(() => showView('login'), 2000);
        return;
    }
    
    const input = document.getElementById('guest-query-input');
    const query = input.value.trim();
    if (!query) return;

    if (!isLoggedIn()) {
        guestMessageCount++;
        localStorage.setItem("guestCount", guestMessageCount);
    }

    const container = document.getElementById("guest-chat-history");
    appendMessageToContainer(query, 'user', container, null, false);
    input.value = '';
    
    const loadId = appendMessageToContainer("Processing request via Agent...", 'system', container, null, false);

    try {
        const res = await fetch(`${API_BASE}/query/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, agent: currentGuestAgent })
        });
        const data = await res.json();
        document.getElementById(loadId).remove(); 
        
        if (!res.ok) {
            appendMessageToContainer(`❌ Error: ${data.detail || 'Query failed'}`, 'system', container, null, false);
            return;
        }

        let agent = data.agent_used || "orchestrator";
        let formatted = agent === 'orchestrator' ? '' : `<span class="agent-badge">${agent}</span><br/>`;
        formatted += formatAgentData(agent, data.result || {});
        appendMessageToContainer(formatted, 'system', container, null, false);
        
    } catch(err) {
        document.getElementById(loadId)?.remove();
        appendMessageToContainer(`❌ Error: ${err.message}`, 'system', container, null, false);
    }
});

function loadGuestHistory() {
    const container = document.getElementById('guest-chat-history');
    container.innerHTML = '';
    const saved = localStorage.getItem("guest_history");
    if (saved) {
        JSON.parse(saved).forEach(m => appendMessageToContainer(m.text, m.sender, container, null, false));
    }
}


// --- AUTHENTICATED/ROLE QUERY LOGIC ---
document.getElementById('query-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const container = document.getElementById("chat-history");
    const userMessages = Array.from(container.children).filter(msg => msg.classList.contains('user-msg')).length;
    
    if (userMessages >= 50) {
        showToast("Session limit of 50 messages reached! Please start a 'New Chat' in the sidebar to continue.", true);
        return;
    }

    const input = document.getElementById('query-input');
    const query = input.value.trim();
    if (!query) return;

    const historyKey = `history_${currentUsername}_${userRole}`;
    
    appendMessageToContainer(query, 'user', container, historyKey, true);
    input.value = '';
    
    const loadId = appendMessageToContainer("Orchestrating agents and analyzing...", 'system', container, null, false);

    try {
        const res = await fetch(`${API_BASE}/query/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ query: query, agent: currentAgent })
        });
        
        if (res.status === 401 || res.status === 403) throw new Error("Session expired. Please log in again.");
        
        const data = await res.json();
        document.getElementById(loadId).remove(); 
        
        if (!res.ok) {
            appendMessageToContainer(`❌ Error: ${data.detail || 'Query failed'}`, 'system', container, historyKey, true);
            return;
        }

        if (data.flagged_high_risk) {
            appendMessageToContainer(`⚠️ <b>High Risk Flagged</b><br/>${data.message}<br/><br/><i>Reason: ${data.result?.risk_reason || 'Unknown reason'}</i>`, 'system', container, historyKey, true);
        } else {
            let agent = data.agent_used || "orchestrator";
            let formatted = agent === 'orchestrator' ? '' : `<span class="agent-badge">${agent}</span><br/>`;
            formatted += formatAgentData(agent, data.result || {});
            appendMessageToContainer(formatted, 'system', container, historyKey, true);
        }
    } catch(err) {
        document.getElementById(loadId)?.remove();
        appendMessageToContainer(`❌ Error: ${err.message}`, 'system', container, null, false);
        if(err.message.includes("Session")) logout();
    }
});

function loadChatHistory() {
    const container = document.getElementById('chat-history');
    container.innerHTML = '';
    const historyKey = `history_${currentUsername}_${userRole}`;
    const saved = localStorage.getItem(historyKey);
    
    if (saved) {
        JSON.parse(saved).forEach(m => appendMessageToContainer(m.text, m.sender, container, null, false));
    } else {
        appendMessageToContainer("Assistant standing by. Please enter a research query or clinical topic.", "system", container, null, false);
    }
}


// FORMATTER FOR HUMAN-READABLE OUTPUTS
function formatAgentData(agent, result) {
    let html = `<div style="margin-top: 15px;">`;
    
    // Safety check for missing result
    if (!result) result = { summary: "Analysis complete, but no details were returned." };

    // Global Simple Rendering for Conversational/Out-of-Domain responses
    if (result.is_conversational || result.is_out_of_domain) {
        const summaryFormatted = ((result && result.summary) || "I am processing your scientific query...")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\n/g, "<br/>");
        return html + `<div style="padding: 10px; line-height: 1.8; font-size: 0.98rem; color: var(--text-main);">${summaryFormatted}</div></div>`;
    }

    const summaryFormatted = (result.summary || "No summary provided.")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br/>");

    if (agent === "DPEA") {
        let decision = result.prescription_decision || "Refer to details";
        let uses = result.drug_indications?.indications?.map(i => i.indication).join(", ") || "General medical use";
        
        html += `
            <div style="background: var(--surface-bg); padding: 25px; border-radius: 12px; border-left: 4px solid var(--accent); margin-top: 15px;">
                <h3 style="margin-bottom: 15px; color: var(--secondary); font-size: 1.2rem;">🩺 Clinical Assessment: ${result.drug_name ? result.drug_name.toUpperCase() : 'Prescription Inquiry'}</h3>
                <p style="margin-bottom: 12px; font-size: 1.1rem;"><strong>Decision:</strong> <span style="color: var(--accent); font-weight: 700;">${decision}</span></p>
                <div style="line-height: 1.8; font-size: 1rem; color: var(--text-main);">${summaryFormatted}</div>
                
                <h4 style="margin-top: 20px; color: var(--text-muted); font-size: 0.9rem;">💊 Relevant Clinical Context</h4>
                <p style="font-size: 0.95rem; opacity: 0.9;"><strong>Indications:</strong> ${uses}</p>
                <ul style="margin-left: 20px; margin-top: 10px; font-size: 0.95rem; opacity: 0.9;">
                    ${result.drug_drug_interactions ? result.drug_drug_interactions.map(i => `<li>${i}</li>`).join('') : '<li>No major interactions noted in primary datasets.</li>'}
                </ul>
            </div>
        `;
    } else if (agent === "CRA") {
        html += `
            <div style="background: var(--surface-bg); padding: 25px; border-radius: 12px; border-left: 4px solid var(--secondary); margin-top: 15px;">
                <h3 style="margin-bottom: 15px; color: var(--accent); font-size: 1.2rem;">🧪 Chemical Research: ${result.compound_name || 'Target Compound'}</h3>
                <div style="line-height: 1.8; font-size: 1rem; color: var(--text-main);">${summaryFormatted}</div>
            </div>
        `;
    } else if (agent === "DDRA") {
        let score = result.feasibility_score ? Math.round(result.feasibility_score * 100) : "N/A";
        html += `
            <div style="background: var(--surface-bg); padding: 25px; border-radius: 12px; border-left: 4px solid #00e5ff; margin-top: 15px;">
                <h3 style="margin-bottom: 15px; color: var(--accent); font-size: 1.2rem;">⚗️ Drug Discovery: ${result.compound_name || 'Candidate'}</h3>
                <p style="margin-bottom: 10px;"><strong>Feasibility Score:</strong> ${score}%</p>
                <div style="line-height: 1.8; font-size: 1rem; color: var(--text-main);">${summaryFormatted}</div>
            </div>
        `;
    } else if (agent === "orchestrator") {
        html += `
            <div style="background: var(--surface-bg); padding: 25px; border-radius: 12px; border-left: 4px solid var(--accent); margin-top: 15px;">
                <h3 style="margin-bottom: 15px; color: var(--secondary); font-size: 1.2rem;">🔬 Research Narrative: ${result.compound_name ? result.compound_name.toUpperCase() : 'Integrated Study'}</h3>
                <div style="line-height: 1.9; font-size: 1.05rem; color: var(--text-main);">${summaryFormatted}</div>
            </div>`;
    } else {
        html += `<pre class="obj-view" style="margin-top:15px; background: var(--surface-bg); color: var(--text-main); padding: 15px; border-radius: 8px;">${JSON.stringify(result, null, 2)}</pre>`;
    }
    
    html += `</div>`;
    return html;
}

// --- ADMIN LOGIC ---
async function fetchPendingApprovals() {
    const grid = document.getElementById('approvals-grid');
    grid.innerHTML = '<p>Loading pending reviews...</p>';
    try {
        const res = await fetch(`${API_BASE}/admin/approvals`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) throw new Error('Unauthorized');
        const tasks = await res.json();
        
        if (tasks.length === 0) {
            grid.innerHTML = '<p style="color:var(--success);">✅ All systems clear. No pending safety violations.</p>';
            return;
        }
        
        grid.innerHTML = tasks.map(t => `
            <div class="approval-card glass" id="task-${t.approval_id}">
                <div class="risk-badge">HIGH RISK DETECTED</div>
                <div class="ap-query">Query: "${t.query}"</div>
                <div class="ap-reason">Reason: ${t.risk_reason}</div>
                <div class="ap-actions">
                    <button class="btn btn-approve" onclick="resolveTask('${t.approval_id}', true)">Approve Release</button>
                    <button class="btn btn-reject" onclick="resolveTask('${t.approval_id}', false)">Reject & Block</button>
                </div>
            </div>
        `).join('');
    } catch(err) {
        grid.innerHTML = `<p style="color:var(--danger)">Error: ${err.message}</p>`;
    }
}

async function resolveTask(id, approved) {
    try {
        const res = await fetch(`${API_BASE}/admin/approve`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ approval_id: id, approved: approved })
        });
        if (!res.ok) throw new Error('Action failed');
        
        showToast(approved ? "Output Approved & Released" : "Output Rejected & Blocked", !approved);
        document.getElementById(`task-${id}`).remove();
    } catch(err) {
        showToast(err.message, true);
    }
}

// --- MOLECULAR EXPLORER LOGIC (Premium Redesign) ---
function toggleMolecularSearch() {
    showView('molecular');
}

async function searchMolecule(mode = 'standalone') {
    const inputId = mode === 'integrated' ? 'int-mol-search-input' : 'mol-search-input';
    const queryInput = document.getElementById(inputId);
    const query = queryInput.value.trim();
    if (!query) return;

    const prefix = mode === 'integrated' ? 'int-' : '';
    const nameEl = document.getElementById(`${prefix}mol-name`);
    const formulaEl = document.getElementById(`${prefix}mol-formula`);
    const propsContainer = document.getElementById(`${prefix}mol-props-container`);
    const loader = document.getElementById(`${prefix}mol-loading`);
    
    nameEl.innerText = "Searching...";
    if (propsContainer) propsContainer.innerHTML = '';
    loader.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/chem/search/${query}`);
        if (!res.ok) throw new Error("Molecule not found");
        const data = await res.json();
        
        nameEl.innerText = data.name.toUpperCase();
        if (formulaEl) formulaEl.innerText = data.molecular_formula;

        // Create cards for properties
        const propItems = [
            { label: "CID", val: data.cid, icon: "🆔" },
            { label: "Weight", val: data.molecular_weight, icon: "⚖️" },
            { label: "SMILES", val: data.canonical_smiles, icon: "🔗" }
        ];

        if (propsContainer) {
            propsContainer.innerHTML = propItems.map(p => `
                <div class="mol-card">
                    <h4>${p.icon} ${p.label}</h4>
                    <p style="font-size: ${p.val.toString().length > 15 ? '0.8rem' : '1.1rem'}; word-break: break-all;">${p.val}</p>
                </div>
            `).join('') + `
                <a href="https://pubchem.ncbi.nlm.nih.gov/compound/${data.cid}" target="_blank" 
                   style="display: block; text-align: center; color: var(--secondary); margin-top: 10px; font-size: 0.85rem; text-decoration: none; border: 1px solid var(--secondary); padding: 8px; border-radius: 8px; background: rgba(0, 230, 118, 0.1);">
                   View on PubChem ↗
                </a>
            `;
        }
        
        renderMolecule3D(data.cid, mode);
    } catch (err) {
        nameEl.innerText = "Error";
        showToast(err.message, true);
    } finally {
        loader.classList.add('hidden');
    }
}

async function renderMolecule3D(cid, mode = 'standalone') {
    const prefix = mode === 'integrated' ? 'int-' : '';
    const loader = document.getElementById(`${prefix}mol-loading`);
    loader.classList.remove('hidden');
    
    try {
        const res = await fetch(`${API_BASE}/chem/3d/${cid}`);
        if (!res.ok) throw new Error("SDF data not available");
        const data = await res.json();
        
        const container = document.getElementById(`${prefix}mol-3d-viewer`);
        container.innerHTML = ''; // Clear
        
        const viewer = $3Dmol.createViewer(container, { backgroundColor: 'black' });
        viewer.addModel(data.sdf, "sdf");
        viewer.setStyle({}, { stick: { radius: 0.15 }, sphere: { scale: 0.25 } });
        viewer.zoomTo();
        viewer.render();
        viewer.spin([0.5, 1, 0.2], 1); 
        
    } catch (err) {
        console.error(err);
        showToast("Could not load 3D model", true);
    } finally {
        loader.classList.add('hidden');
    }
}

// --- PROFILE LOGIC ---
function saveProfilePreferences() {
    const agent = document.getElementById('pref-agent').value;
    const theme = document.getElementById('pref-theme').value;
    
    localStorage.setItem("prefAgent", agent);
    localStorage.setItem("theme", theme);
    
    changeTheme(theme);
    showToast("Preferences saved successfully!");
}

// --- PDF EXPORT LOGIC ---
function exportChatToPDF() {
    if (!window.jspdf) {
        showToast("PDF library not loaded", true);
        return;
    }
    
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const historyKey = `history_${currentUsername}_${userRole}`;
    const saved = localStorage.getItem(historyKey);
    
    if (!saved) {
        showToast("No chat history to export", true);
        return;
    }
    
    const messages = JSON.parse(saved);
    let y = 20;

    // Header
    doc.setFontSize(20);
    doc.setTextColor(107, 76, 255); // Accent color
    doc.text("Scientific Assistant - Research Report", 20, y);
    y += 15;
    
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`User: ${currentUsername} | Role: ${userRole.toUpperCase()} | Date: ${new Date().toLocaleString()}`, 20, y);
    y += 10;
    doc.line(20, y, 190, y);
    y += 15;

    messages.forEach((m, i) => {
        if (y > 270) {
            doc.addPage();
            y = 20;
        }
        
        doc.setFont("helvetica", "bold");
        doc.setTextColor(m.sender === 'user' ? 0 : 50);
        doc.text(m.sender === 'user' ? "User Query:" : "AI Response:", 20, y);
        y += 7;
        
        doc.setFont("helvetica", "normal");
        doc.setTextColor(0);
        
        // Strip HTML tags for PDF
        const cleanText = m.text.replace(/<[^>]*>?/gm, '');
        const splitText = doc.splitTextToSize(cleanText, 160);
        doc.text(splitText, 25, y);
        y += (splitText.length * 7) + 10;
    });

    doc.save(`Research_Report_${currentUsername}_${Date.now()}.pdf`);
    showToast("PDF Report Downloaded!");
}

// Kickstart
init();
