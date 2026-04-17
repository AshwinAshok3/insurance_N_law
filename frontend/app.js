const API_BASE_URL = 'http://localhost:8001/api';

// DOM Elements
const authForm = document.getElementById('auth-form');
const guestBtn = document.getElementById('guest-btn');
const authSwitchLink = document.getElementById('auth-switch-link');
const alertBox = document.getElementById('alert-box');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatContainer = document.getElementById('chat-container');
const uploadForm = document.getElementById('upload-form');

// State
let currentDomain = 'law';

// Generic Show Alert
function showAlert(message, type = 'error') {
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type}`;
    alertBox.classList.remove('hidden');
    setTimeout(() => {
        alertBox.classList.add('hidden');
    }, 5000);
}

// Ensure proper UI based on mode in URL (Login Page)
if (window.location.pathname.includes('login.html')) {
    const urlParams = new URLSearchParams(window.location.search);
    const isRegister = urlParams.get('mode') === 'register';
    
    if (isRegister) {
        document.getElementById('auth-title').textContent = 'Create Account';
        document.getElementById('auth-subtitle').textContent = 'Join Nexustice AI Enterprise';
        document.getElementById('submit-btn').textContent = 'Register';
        document.getElementById('auth-switch-text').textContent = 'Already have an account?';
        document.getElementById('auth-switch-link').textContent = 'Login here';
        document.getElementById('auth-switch-link').href = 'login.html';
    } else {
        document.getElementById('auth-switch-link').href = 'login.html?mode=register';
    }

    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const endpoint = isRegister ? '/register' : '/login';

            try {
                const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    localStorage.setItem('userId', data.user_id);
                    localStorage.setItem('username', data.username || username);
                    window.location.href = 'dashboard.html';
                } else {
                    showAlert(data.detail, 'error');
                }
            } catch (err) {
                showAlert('Failed to connect to the server.', 'error');
            }
        });
    }

    if (guestBtn) {
        guestBtn.addEventListener('click', () => {
            localStorage.setItem('userId', 0);
            localStorage.setItem('username', 'Guest');
            window.location.href = 'dashboard.html?guest=true';
        });
    }
}

// Dashboard Logic
if (window.location.pathname.includes('dashboard.html')) {
    const userId = localStorage.getItem('userId');
    const username = localStorage.getItem('username');
    
    if (!userId && !window.location.search.includes('guest=true')) {
        window.location.href = 'login.html';
    }
    
    document.getElementById('user-name').textContent = username || 'Guest';
    document.getElementById('user-avatar').textContent = (username || 'G')[0].toUpperCase();

    // Auto resize chat input
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            if(this.value === '') this.style.height = 'auto';
        });
        
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = chatInput.value.trim();
            if (!query) return;

            // Add User Message
            addMessage(query, 'user');
            chatInput.value = '';
            chatInput.style.height = 'auto';

            // Add Temp AI Loading
            const loadingId = addLoadingMessage();

            try {
                const response = await fetch(`${API_BASE_URL}/query_ai`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        query: query, 
                        domain: currentDomain,
                        user_id: parseInt(userId || 0)
                    })
                });
                
                const data = await response.json();
                removeElement(loadingId);
                
                if (response.ok) {
                    addMessage(data.response, 'ai');
                } else {
                    addMessage(`Error: ${data.detail}`, 'ai');
                }
            } catch (err) {
                removeElement(loadingId);
                addMessage('Failed to reach AI server.', 'ai');
            }
        });
    }
}

// Domain Switcher
window.switchDomain = function(domain) {
    currentDomain = domain;
    
    // Update active class
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    document.getElementById(`nav-${domain}`).classList.add('active');
    
    // Update title
    const titles = {
        'law': '<i class="fa-solid fa-gavel text-gradient"></i> Legal Reference Assistant',
        'banks': '<i class="fa-solid fa-building-columns text-gradient"></i> Bank Insurance Policy Checker',
        'irdai': '<i class="fa-solid fa-clipboard-check text-gradient"></i> IRDAI Compliance Explorer',
        'aa': '<i class="fa-solid fa-mobile-retro text-gradient"></i> AA Consent Sandbox',
        'heatmap': '<i class="fa-solid fa-map-location-dot text-gradient"></i> Regulatory Heatmap'
    };
    
    document.getElementById('active-domain-title').innerHTML = titles[domain];
    const inputArea = document.getElementById('input-area');
    
    if (domain === 'heatmap') {
        if(inputArea) inputArea.style.display = 'none';
        renderHeatmap();
    } else if (domain === 'aa') {
        if(inputArea) inputArea.style.display = 'none';
        renderAA();
    } else {
        if(inputArea) inputArea.style.display = 'block';
        // Reset Chat
        if (chatContainer) {
            chatContainer.innerHTML = `
                <div class="message ai animate-fade-in">
                    <div class="avatar" style="background: var(--bg-secondary); border: 1px solid var(--border-glass);"><i class="fa-solid fa-robot"></i></div>
                    <div class="message-bubble">
                        Switched to ${domain.toUpperCase()} domain. How can I help you?
                    </div>
                </div>
            `;
        }
    }
};

window.renderAA = function() {
    if (!chatContainer) return;
    chatContainer.innerHTML = `
        <div class="message ai animate-fade-in" style="max-width: 100%;">
            <div class="message-bubble" style="width: 100%;">
                <h3>Account Aggregator Integration (Sandbox)</h3>
                <p style="color: var(--text-secondary); margin-bottom: 15px;">Provide consent to quickly fetch your encrypted financial data to securely audit insurance compliance automatically.</p>
                <div style="display:flex; gap: 10px; margin-top: 15px;">
                    <input type="text" id="phone-input" placeholder="Enter Phone Number (e.g. 9876543210)" style="padding: 10px; border-radius: 4px; border: 1px solid var(--border-glass); background: rgba(0,0,0,0.2); color: white; flex:1;">
                    <button class="btn btn-primary" onclick="triggerAAFetch()">Generate OTP & Fetch</button>
                </div>
            </div>
        </div>
    `;
};

window.triggerAAFetch = async function() {
    const phone = document.getElementById('phone-input').value;
    if (!phone) {
        showAlert("Please enter a phone number.", "error"); return;
    }
    const loadingId = addLoadingMessage();
    const userId = localStorage.getItem('userId') || 0;
    
    try {
        const response = await fetch(`${API_BASE_URL}/aa/fetch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: phone, user_id: parseInt(userId) })
        });
        
        const data = await response.json();
        removeElement(loadingId);
        
        if (response.ok) {
            addMessage("**Account Data Interrogated via Sandbox.**", 'ai');
            addMessage(`AI Compliance Report:\n\n${data.analysis}`, 'ai');
        } else {
            addMessage(`Error: ${data.detail}`, 'ai');
        }
    } catch (err) {
        removeElement(loadingId);
        addMessage('Failed to reach AA processor API.', 'ai');
    }
};

window.renderHeatmap = async function() {
    if (!chatContainer) return;
    chatContainer.innerHTML = `
        <div style="width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px;">
            <div class="spinner" style="border-top-color: var(--accent-primary);"></div>
            <p style="margin-top:20px;">Aggregating National Telemetry...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/heatmap_stats`);
        const data = await response.json();
        
        chatContainer.innerHTML = `
            <div class="message-bubble" style="width: 100%; max-width: 800px; margin: 0 auto; background: rgba(0,0,0,0.3); padding: 2rem;">
                <h2 style="color: var(--accent-secondary); margin-bottom: 20px;">AI Compliance Heatmap</h2>
                <div style="background: white; padding: 10px; border-radius: 8px;">
                    <canvas id="heatmapChart" width="400" height="200"></canvas>
                </div>
                <h3 style="margin-top: 30px; margin-bottom: 10px;">Recent AI Flags</h3>
                <ul id="recent-flags" style="padding-left: 20px;"></ul>
            </div>
        `;
        
        const list = document.getElementById('recent-flags');
        if (data.recent_violations.length === 0) {
            list.innerHTML = "<li>No flags recorded yet.</li>";
        } else {
            data.recent_violations.forEach(v => {
                list.innerHTML += `<li style="margin-bottom: 8px;"><strong>${v.bank}</strong> (${v.state}): <span style="color: #ef4444;">${v.type}</span> <br><small style="color:var(--text-muted);">${v.timestamp}</small></li>`;
            });
        }
        
        // Render Chart
        const ctx = document.getElementById('heatmapChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.heatmap.map(x => x.state),
                    datasets: [{
                        label: 'Violations Detected',
                        data: data.heatmap.map(x => x.count),
                        backgroundColor: 'rgba(239, 68, 68, 0.5)',
                        borderColor: 'rgb(239, 68, 68)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });
        }
    } catch(err) {
        console.error(err);
        chatContainer.innerHTML = `<div class="alert alert-error">Failed to load Heatmap stats.</div>`;
    }
};

// Chat Helpers
function addMessage(text, sender) {
    if (!chatContainer) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender} animate-fade-in`;
    
    const parsedText = sender === 'ai' ? marked.parse(text) : text;
    
    if (sender === 'ai') {
        msgDiv.innerHTML = `
            <div class="avatar" style="background: var(--bg-secondary); border: 1px solid var(--border-glass);"><i class="fa-solid fa-robot"></i></div>
            <div class="message-bubble">${parsedText}</div>
        `;
    } else {
        msgDiv.innerHTML = `<div class="message-bubble">${parsedText}</div>`;
    }
    
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ai animate-fade-in`;
    msgDiv.id = id;
    msgDiv.innerHTML = `
        <div class="avatar" style="background: var(--bg-secondary); border: 1px solid var(--border-glass);"><i class="fa-solid fa-robot"></i></div>
        <div class="message-bubble"><div class="spinner" style="border-top-color: var(--accent-primary);"></div></div>
    `;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

window.logout = function() {
    localStorage.clear();
    window.location.href = 'login.html';
};

// Upload Logic
if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('file-input');
        const namespaceSelect = document.getElementById('namespace-select');
        
        if (fileInput.files.length === 0) return;
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', namespaceSelect.value);
        
        const btnUpload = document.getElementById('btn-upload');
        const progressBar = document.getElementById('progress-bar');
        const progressContainer = document.getElementById('progress-container');
        const progressStatus = document.getElementById('progress-status');
        
        btnUpload.disabled = true;
        progressContainer.classList.remove('hidden');
        progressStatus.textContent = "Uploading securely to AI engine...";
        progressBar.style.width = '50%';

        try {
            const response = await fetch(`${API_BASE_URL}/upload_document`, {
                method: 'POST',
                body: formData
            });
            
            progressBar.style.width = '100%';
            
            const data = await response.json();
            
            if (response.ok) {
                progressStatus.textContent = "Queued!";
                showAlert(data.message, 'success');
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    progressBar.style.width = '0%';
                    btnUpload.disabled = false;
                    fileInput.value = '';
                }, 3000);
            } else {
                progressStatus.textContent = "Failed.";
                showAlert(data.detail || "API Error", 'error');
                btnUpload.disabled = false;
            }
        } catch (err) {
            progressStatus.textContent = "Network Error.";
            showAlert('Failed to reach server.', 'error');
            btnUpload.disabled = false;
        }
    });
}
