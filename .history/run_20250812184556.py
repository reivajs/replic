#!/usr/bin/env python3
"""
🚀 COMPLETE SYSTEM STARTUP SCRIPT
================================
Inicia el sistema completo enterprise con Discovery Service
Integra perfectamente con tu arquitectura existente
"""

import subprocess
import sys
import time
import os
import requests
from pathlib import Path
import asyncio
import json

def create_missing_files():
    """Crear archivos faltantes necesarios"""
    print("📁 Checking and creating missing files...")
    
    # Crear directorios necesarios
    dirs = [
        "services/discovery",
        "data",
        "sessions",
        "frontend/templates",
        "logs"
    ]
    
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 1. Crear services/discovery/main.py si no existe
    discovery_path = Path("services/discovery/main.py")
    if not discovery_path.exists():
        print("📝 Creating Discovery Service...")
        # Aquí irías al artifact anterior y copiarías el código
        print("💡 Copy the Discovery Service code from the artifact to services/discovery/main.py")
    
    # 2. Crear start script simplificado
    start_script = Path("scripts/start_all.py")
    start_script.parent.mkdir(exist_ok=True)
    
    if not start_script.exists():
        start_content = '''#!/usr/bin/env python3
import subprocess
import sys
import time

def start_service(name, port, script_path):
    """Start a service"""
    print(f"🚀 Starting {name} on port {port}...")
    return subprocess.Popen([
        sys.executable, script_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    processes = []
    
    try:
        # 1. Discovery Service (puerto 8002)
        discovery_proc = start_service("Discovery Service", 8002, "services/discovery/main.py")
        processes.append(("Discovery Service", discovery_proc))
        time.sleep(3)
        
        # 2. Message Replicator (puerto 8001) 
        replicator_proc = start_service("Message Replicator", 8001, "paste.txt")
        processes.append(("Message Replicator", replicator_proc))
        time.sleep(3)
        
        # 3. Main Orchestrator (puerto 8000)
        main_proc = start_service("Main Orchestrator", 8000, "paste-2.txt")
        processes.append(("Main Orchestrator", main_proc))
        time.sleep(3)
        
        print("✅ All services started!")
        print("🌐 Access URLs:")
        print("   Main Dashboard:    http://localhost:8000/dashboard")
        print("   Discovery UI:      http://localhost:8000/discovery")
        print("   Groups Hub:        http://localhost:8000/groups")
        print("   API Docs:          http://localhost:8000/docs")
        
        # Wait for processes
        for name, proc in processes:
            proc.wait()
            
    except KeyboardInterrupt:
        print("\\n🛑 Stopping all services...")
        for name, proc in processes:
            proc.terminate()
        print("👋 System stopped")

if __name__ == "__main__":
    main()
'''
        with open(start_script, 'w') as f:
            f.write(start_content)
        os.chmod(start_script, 0o755)
        print(f"✅ Created {start_script}")
    
    # 3. Crear template discovery_dashboard.html si no existe
    discovery_template = Path("frontend/templates/discovery_dashboard.html")
    if not discovery_template.exists():
        print("📝 Creating Discovery Dashboard template...")
        
        discovery_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Discovery System - Enterprise</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary: #6366f1;
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: rgba(30, 41, 59, 0.8);
            --bg-glass: rgba(255, 255, 255, 0.05);
            --border: rgba(255, 255, 255, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 1.5rem;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--border);
        }
        
        .header h1 {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .header-actions {
            display: flex;
            gap: 1rem;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-secondary {
            background: var(--bg-glass);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            border: 1px solid var(--border);
            padding: 1.5rem;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            display: block;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 2rem;
        }
        
        .sidebar {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--border);
            padding: 1.5rem;
            height: fit-content;
        }
        
        .sidebar h3 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }
        
        .filter-group {
            margin-bottom: 1.5rem;
        }
        
        .filter-label {
            display: block;
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .filter-input {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-glass);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.9rem;
        }
        
        .filter-buttons {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 0.5rem 1rem;
            background: var(--bg-glass);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-secondary);
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .filter-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .content-area {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--border);
            padding: 1.5rem;
        }
        
        .content-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .view-toggle {
            display: flex;
            background: var(--bg-glass);
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        
        .view-btn {
            padding: 0.5rem 1rem;
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .view-btn.active {
            background: var(--primary);
            color: white;
        }
        
        .search-bar {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .search-input {
            flex: 1;
            padding: 0.75rem 1rem;
            background: var(--bg-glass);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .search-input::placeholder {
            color: var(--text-muted);
        }
        
        .chats-container {
            min-height: 500px;
        }
        
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .chat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        
        .chat-card {
            background: var(--bg-glass);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .chat-card:hover {
            background: rgba(59, 130, 246, 0.1);
            border-color: var(--primary);
            transform: translateY(-2px);
        }
        
        .chat-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }
        
        .chat-avatar {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 700;
            color: white;
        }
        
        .chat-info {
            flex: 1;
        }
        
        .chat-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .chat-type {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        
        .chat-meta {
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
        }
        
        .chat-actions {
            display: flex;
            gap: 0.5rem;
        }
        
        .action-btn {
            padding: 0.5rem 1rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .action-btn:hover {
            background: var(--primary-dark);
        }
        
        .action-btn.secondary {
            background: var(--bg-glass);
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }
        
        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .chat-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div>
                <h1>🔍 Discovery System</h1>
                <p style="color: var(--text-secondary); margin-top: 0.5rem;">Auto-discovery and configuration of Telegram chats</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" onclick="triggerScan()">
                    <i class="fas fa-search"></i>
                    Scan Chats
                </button>
                <button class="btn btn-secondary" onclick="refreshData()">
                    <i class="fas fa-sync"></i>
                    Refresh
                </button>
                <a href="/dashboard" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i>
                    Dashboard
                </a>
            </div>
        </header>
        
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <span class="stat-value" id="totalChats">-</span>
                <div class="stat-label">Total Chats</div>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="channels">-</span>
                <div class="stat-label">Channels</div>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="groups">-</span>
                <div class="stat-label">Groups</div>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="publicChats">-</span>
                <div class="stat-label">Public</div>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="lastScan">-</span>
                <div class="stat-label">Last Scan</div>
            </div>
        </div>
        
        <div class="main-content">
            <aside class="sidebar">
                <h3>🎯 Smart Search</h3>
                
                <div class="filter-group">
                    <label class="filter-label">Search</label>
                    <input type="text" class="filter-input" id="searchInput" placeholder="Search chats by name, description, or username...">
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">Type</label>
                    <div class="filter-buttons">
                        <button class="filter-btn active" data-filter="type" data-value="">All</button>
                        <button class="filter-btn" data-filter="type" data-value="channel">Channels</button>
                        <button class="filter-btn" data-filter="type" data-value="supergroup">Supergroups</button>
                        <button class="filter-btn" data-filter="type" data-value="group">Groups</button>
                        <button class="filter-btn" data-filter="type" data-value="private">Private</button>
                    </div>
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">Size</label>
                    <div class="filter-buttons">
                        <button class="filter-btn active" data-filter="size" data-value="">Any</button>
                        <button class="filter-btn" data-filter="size" data-value="small">< 10</button>
                        <button class="filter-btn" data-filter="size" data-value="medium">10-100</button>
                        <button class="filter-btn" data-filter="size" data-value="large">100-1K</button>
                        <button class="filter-btn" data-filter="size" data-value="huge">1K+</button>
                    </div>
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">Status</label>
                    <div class="filter-buttons">
                        <button class="filter-btn active" data-filter="status" data-value="">All</button>
                        <button class="filter-btn" data-filter="status" data-value="active">Active</button>
                        <button class="filter-btn" data-filter="status" data-value="inactive">Inactive</button>
                    </div>
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">Min Members</label>
                    <input type="number" class="filter-input" id="minMembers" placeholder="0" min="0">
                </div>
            </aside>
            
            <main class="content-area">
                <div class="content-header">
                    <div>
                        <h2>Found <span id="foundCount">0</span> chats</h2>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Showing 1-20 of <span id="totalFound">0</span> results</p>
                    </div>
                    <div class="view-toggle">
                        <button class="view-btn active" data-view="grid">
                            <i class="fas fa-th"></i>
                            Grid
                        </button>
                        <button class="view-btn" data-view="list">
                            <i class="fas fa-list"></i>
                            List
                        </button>
                    </div>
                </div>
                
                <div class="search-bar">
                    <input type="text" class="search-input" placeholder="Search chats by name, description, or username..." id="mainSearch">
                    <select class="filter-input" id="sortBy" style="width: 150px;">
                        <option value="recent">Recent</option>
                        <option value="name">Name</option>
                        <option value="members">Members</option>
                        <option value="type">Type</option>
                    </select>
                </div>
                
                <div class="chats-container" id="chatsContainer">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading discovered chats...</p>
                    </div>
                </div>
            </main>
        </div>
    </div>
    
    <script>
        class DiscoveryDashboard {
            constructor() {
                this.chats = [];
                this.filteredChats = [];
                this.filters = {
                    search: '',
                    type: '',
                    size: '',
                    status: '',
                    minMembers: 0
                };
                this.viewMode = 'grid';
                this.isScanning = false;
                
                this.init();
            }
            
            async init() {
                this.setupEventListeners();
                await this.loadData();
                this.render();
                this.setupWebSocket();
            }
            
            setupEventListeners() {
                // Search inputs
                document.getElementById('searchInput').addEventListener('input', (e) => {
                    this.filters.search = e.target.value;
                    this.applyFilters();
                });
                
                document.getElementById('mainSearch').addEventListener('input', (e) => {
                    this.filters.search = e.target.value;
                    this.applyFilters();
                });
                
                document.getElementById('minMembers').addEventListener('input', (e) => {
                    this.filters.minMembers = parseInt(e.target.value) || 0;
                    this.applyFilters();
                });
                
                // Filter buttons
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const filter = e.target.dataset.filter;
                        const value = e.target.dataset.value;
                        
                        // Update active state
                        e.target.parentElement.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                        e.target.classList.add('active');
                        
                        // Apply filter
                        this.filters[filter] = value;
                        this.applyFilters();
                    });
                });
                
                // View toggle
                document.querySelectorAll('.view-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const view = e.target.dataset.view;
                        
                        document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                        e.target.classList.add('active');
                        
                        this.viewMode = view;
                        this.render();
                    });
                });
                
                // Sort
                document.getElementById('sortBy').addEventListener('change', (e) => {
                    this.sortChats(e.target.value);
                    this.render();
                });
            }
            
            async loadData() {
                try {
                    // Load stats
                    const statsResponse = await fetch('/api/discovery/stats');
                    if (statsResponse.ok) {
                        const stats = await statsResponse.json();
                        this.updateStats(stats);
                    }
                    
                    // Load chats
                    const chatsResponse = await fetch('/api/discovery/chats?limit=100');
                    if (chatsResponse.ok) {
                        const data = await chatsResponse.json();
                        this.chats = data.chats || [];
                        this.applyFilters();
                    }
                } catch (error) {
                    console.error('Error loading data:', error);
                    this.showError('Failed to load discovery data');
                }
            }
            
            updateStats(stats) {
                const { database } = stats;
                
                document.getElementById('totalChats').textContent = database.total_chats || 0;
                document.getElementById('channels').textContent = database.channels || 0;
                document.getElementById('groups').textContent = database.groups || 0;
                document.getElementById('publicChats').textContent = database.public_chats || 0;
                
                const lastScan = stats.scanner?.last_scan;
                if (lastScan) {
                    const date = new Date(lastScan);
                    document.getElementById('lastScan').textContent = date.toLocaleDateString();
                } else {
                    document.getElementById('lastScan').textContent = 'Never';
                }
            }
            
            applyFilters() {
                this.filteredChats = this.chats.filter(chat => {
                    // Search filter
                    if (this.filters.search) {
                        const search = this.filters.search.toLowerCase();
                        const title = (chat.title || '').toLowerCase();
                        const description = (chat.description || '').toLowerCase();
                        const username = (chat.username || '').toLowerCase();
                        
                        if (!title.includes(search) && !description.includes(search) && !username.includes(search)) {
                            return false;
                        }
                    }
                    
                    // Type filter
                    if (this.filters.type && chat.type !== this.filters.type) {
                        return false;
                    }
                    
                    // Size filter
                    if (this.filters.size) {
                        const count = chat.participants_count || 0;
                        switch (this.filters.size) {
                            case 'small': if (count >= 10) return false; break;
                            case 'medium': if (count < 10 || count >= 100) return false; break;
                            case 'large': if (count < 100 || count >= 1000) return false; break;
                            case 'huge': if (count < 1000) return false; break;
                        }
                    }
                    
                    // Min members filter
                    if (this.filters.minMembers > 0) {
                        if ((chat.participants_count || 0) < this.filters.minMembers) {
                            return false;
                        }
                    }
                    
                    return true;
                });
                
                this.render();
            }
            
            sortChats(sortBy) {
                this.filteredChats.sort((a, b) => {
                    switch (sortBy) {
                        case 'name':
                            return (a.title || '').localeCompare(b.title || '');
                        case 'members':
                            return (b.participants_count || 0) - (a.participants_count || 0);
                        case 'type':
                            return (a.type || '').localeCompare(b.type || '');
                        case 'recent':
                        default:
                            return new Date(b.discovered_at || 0) - new Date(a.discovered_at || 0);
                    }
                });
            }
            
            render() {
                const container = document.getElementById('chatsContainer');
                
                // Update counters
                document.getElementById('foundCount').textContent = this.filteredChats.length;
                document.getElementById('totalFound').textContent = this.filteredChats.length;
                
                if (this.filteredChats.length === 0) {
                    container.innerHTML = `
                        <div class="loading">
                            <p>No chats found matching your criteria</p>
                        </div>
                    `;
                    return;
                }
                
                if (this.viewMode === 'grid') {
                    container.innerHTML = `
                        <div class="chat-grid">
                            ${this.filteredChats.map(chat => this.renderChatCard(chat)).join('')}
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="chat-list">
                            ${this.filteredChats.map(chat => this.renderChatListItem(chat)).join('')}
                        </div>
                    `;
                }
            }
            
            renderChatCard(chat) {
                const avatar = (chat.title || 'Unknown').charAt(0).toUpperCase();
                const memberCount = chat.participants_count ? `${chat.participants_count} members` : 'Private';
                const typeIcon = this.getTypeIcon(chat.type);
                const badges = this.getBadges(chat);
                
                return `
                    <div class="chat-card" onclick="discovery.showChatDetails(${chat.id})">
                        <div class="chat-header">
                            <div class="chat-avatar">${avatar}</div>
                            <div class="chat-info">
                                <div class="chat-title">${chat.title || 'Unknown'}</div>
                                <div class="chat-type">${typeIcon} ${chat.type}</div>
                            </div>
                            ${badges}
                        </div>
                        <div class="chat-meta">
                            <span>${memberCount}</span>
                            ${chat.username ? `<span>@${chat.username}</span>` : ''}
                        </div>
                        <div class="chat-actions">
                            <button class="action-btn" onclick="event.stopPropagation(); discovery.configureChat(${chat.id})">
                                Configure
                            </button>
                            <button class="action-btn secondary" onclick="event.stopPropagation(); discovery.previewChat(${chat.id})">
                                Preview
                            </button>
                        </div>
                    </div>
                `;
            }
            
            renderChatListItem(chat) {
                // Similar to card but in list format
                return this.renderChatCard(chat); // For now, use same format
            }
            
            getTypeIcon(type) {
                switch (type) {
                    case 'channel': return '📺';
                    case 'supergroup': return '👥';
                    case 'group': return '👨‍👩‍👧‍👦';
                    case 'private': return '💬';
                    default: return '❓';
                }
            }
            
            getBadges(chat) {
                const badges = [];
                
                if (chat.is_verified) badges.push('<span style="color: #10b981;">✓</span>');
                if (chat.is_scam) badges.push('<span style="color: #ef4444;">⚠</span>');
                if (chat.username) badges.push('<span style="color: #3b82f6;">🌐</span>');
                
                return badges.length > 0 ? `<div>${badges.join(' ')}</div>` : '';
            }
            
            async configureChat(chatId) {
                try {
                    const chat = this.chats.find(c => c.id === chatId);
                    if (!chat) return;
                    
                    const config = {
                        chat_id: chatId,
                        chat_title: chat.title,
                        enabled: true
                    };
                    
                    const response = await fetch('/api/discovery/configure', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
                    
                    if (response.ok) {
                        this.showSuccess(`Chat "${chat.title}" configured successfully!`);
                    } else {
                        throw new Error('Configuration failed');
                    }
                } catch (error) {
                    console.error('Configuration error:', error);
                    this.showError('Failed to configure chat');
                }
            }
            
            showChatDetails(chatId) {
                const chat = this.chats.find(c => c.id === chatId);
                if (!chat) return;
                
                alert(`Chat Details:\\n\\nTitle: ${chat.title}\\nType: ${chat.type}\\nMembers: ${chat.participants_count || 'Unknown'}\\nUsername: ${chat.username || 'None'}\\nVerified: ${chat.is_verified ? 'Yes' : 'No'}`);
            }
            
            previewChat(chatId) {
                this.showInfo(`Preview for chat ${chatId} - Feature coming soon!`);
            }
            
            setupWebSocket() {
                try {
                    const ws = new WebSocket(`ws://${window.location.host}/ws`);
                    
                    ws.onopen = () => {
                        console.log('🔌 WebSocket connected');
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'scan_update') {
                            this.handleScanUpdate(data.data);
                        }
                    };
                    
                    ws.onclose = () => {
                        console.log('🔌 WebSocket disconnected');
                        // Attempt to reconnect after 5 seconds
                        setTimeout(() => this.setupWebSocket(), 5000);
                    };
                } catch (error) {
                    console.error('WebSocket error:', error);
                }
            }
            
            handleScanUpdate(scanData) {
                if (scanData.is_scanning) {
                    this.showScanProgress(scanData.progress);
                } else if (scanData.progress.status === 'completed') {
                    this.showSuccess('Scan completed successfully!');
                    this.loadData(); // Reload data
                }
            }
            
            showScanProgress(progress) {
                const { current, total, status } = progress;
                const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
                
                // You could show a progress bar here
                console.log(`Scan progress: ${current}/${total} (${percentage}%)`);
            }
            
            showSuccess(message) {
                // Simple notification - you could use a proper notification library
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--success);
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    z-index: 1000;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 3000);
            }
            
            showError(message) {
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--error);
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    z-index: 1000;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 3000);
            }
            
            showInfo(message) {
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--primary);
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    z-index: 1000;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 3000);
            }
        }
        
        // Global instance
        let discovery;
        
        // Global functions
        async function triggerScan() {
            try {
                const response = await fetch('/api/discovery/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ force_refresh: true, max_chats: 1000 })
                });
                
                if (response.ok) {
                    discovery.showSuccess('Discovery scan started!');
                } else {
                    throw new Error('Scan failed to start');
                }
            } catch (error) {
                console.error('Scan error:', error);
                discovery.showError('Failed to start scan');
            }
        }
        
        async function refreshData() {
            await discovery.loadData();
            discovery.render();
            discovery.showInfo('Data refreshed!');
        }
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', () => {
            discovery = new DiscoveryDashboard();
        });
    </script>
</body>
</html>'''
        
        with open(discovery_template, 'w', encoding='utf-8') as f:
            f.write(discovery_html)
        print(f"✅ Created {discovery_template}")

def check_service_health(port, service_name):
    """Check if a service is running"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name} (port {port}) - Healthy")
            return True
        else:
            print(f"❌ {service_name} (port {port}) - Unhealthy (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ {service_name} (port {port}) - Not responding")
        return False

def start_service(name, script_path, port):
    """Start a microservice"""
    if not Path(script_path).exists():
        print(f"❌ {script_path} not found")
        return None
    
    print(f"🚀 Starting {name}...")
    return subprocess.Popen([
        sys.executable, script_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def wait_for_service(port, service_name, max_wait=30):
    """Wait for service to be ready"""
    print(f"⏳ Waiting for {service_name} to be ready...")
    
    for i in range(max_wait):
        if check_service_health(port, service_name):
            return True
        time.sleep(1)
    
    print(f"❌ {service_name} failed to start within {max_wait} seconds")
    return False

def main():
    """Main startup orchestrator"""
    print("🚀 STARTING COMPLETE ENTERPRISE SYSTEM")
    print("="*60)
    
    # 1. Create missing files
    create_missing_files()
    
    print("\n📋 STARTING MICROSERVICES...")
    print("-"*40)
    
    processes = []
    
    try:
        # 1. Start Discovery Service (puerto 8002)
        discovery_script = "services/discovery/main.py"
        if Path(discovery_script).exists():
            discovery_proc = start_service("Discovery Service", discovery_script, 8002)
            if discovery_proc:
                processes.append(("Discovery Service", discovery_proc, 8002))
                if wait_for_service(8002, "Discovery Service"):
                    print("✅ Discovery Service ready")
                else:
                    print("⚠️ Discovery Service may not be fully ready")
        else:
            print(f"⚠️ {discovery_script} not found, skipping")
        
        time.sleep(2)
        
        # 2. Start Message Replicator (puerto 8001)
        replicator_script = "paste.txt"  # Tu archivo paste.txt
        if Path(replicator_script).exists():
            # Rename to proper script name
            proper_script = "services/message_replicator/main.py"
            Path("services/message_replicator").mkdir(parents=True, exist_ok=True)
            if not Path(proper_script).exists():
                import shutil
                shutil.copy(replicator_script, proper_script)
                print(f"📝 Copied {replicator_script} to {proper_script}")
            
            replicator_proc = start_service("Message Replicator", proper_script, 8001)
            if replicator_proc:
                processes.append(("Message Replicator", replicator_proc, 8001))
                if wait_for_service(8001, "Message Replicator"):
                    print("✅ Message Replicator ready")
        else:
            print(f"⚠️ {replicator_script} not found, skipping")
        
        time.sleep(2)
        
        # 3. Start Main Orchestrator (puerto 8000)
        orchestrator_script = "paste-2.txt"  # Tu archivo paste-2.txt
        if Path(orchestrator_script).exists():
            # Rename to proper script name
            proper_main = "main.py"
            if not Path(proper_main).exists():
                import shutil
                shutil.copy(orchestrator_script, proper_main)
                print(f"📝 Copied {orchestrator_script} to {proper_main}")
            
            orchestrator_proc = start_service("Main Orchestrator", proper_main, 8000)
            if orchestrator_proc:
                processes.append(("Main Orchestrator", orchestrator_proc, 8000))
                if wait_for_service(8000, "Main Orchestrator"):
                    print("✅ Main Orchestrator ready")
        else:
            print(f"⚠️ {orchestrator_script} not found, skipping")
        
        time.sleep(3)
        
        # 4. Final health check
        print("\n🏥 FINAL HEALTH CHECK")
        print("-"*40)
        
        services_status = [
            (8002, "Discovery Service"),
            (8001, "Message Replicator"), 
            (8000, "Main Orchestrator")
        ]
        
        healthy_services = 0
        for port, name in services_status:
            if check_service_health(port, name):
                healthy_services += 1
        
        print(f"\n📊 SYSTEM STATUS: {healthy_services}/{len(services_status)} services healthy")
        
        if healthy_services > 0:
            print("\n🌐 ACCESS URLS:")
            print("="*50)
            print("🎭 Main Dashboard:      http://localhost:8000/dashboard")
            print("🔍 Discovery System:    http://localhost:8000/discovery")  
            print("👥 Groups Hub:          http://localhost:8000/groups")
            print("📚 API Documentation:   http://localhost:8000/docs")
            print("🏥 Health Check:        http://localhost:8000/health")
            print()
            print("🔗 DIRECT SERVICE ACCESS:")
            print("🔍 Discovery Service:   http://localhost:8002/")
            print("📡 Message Replicator:  http://localhost:8001/")
            print("="*50)
            print("\n✨ ENTERPRISE SYSTEM IS READY!")
            print("Press Ctrl+C to stop all services...")
            
            # Wait for keyboard interrupt
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ No services started successfully")
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Startup error: {e}")
    finally:
        print("\n🛑 STOPPING ALL SERVICES...")
        print("-"*40)
        
        for name, proc, port in processes:
            try:
                print(f"🛑 Stopping {name}...")
                proc.terminate()
                proc.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Force killing {name}...")
                proc.kill()
                proc.wait()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        print("\n👋 ENTERPRISE SYSTEM STOPPED")
        print("="*60)

if __name__ == "__main__":
    main()