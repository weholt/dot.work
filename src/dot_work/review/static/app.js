// dot-work review frontend JavaScript

const AUTH_TOKEN_KEY = 'review-auth-token';

function getAuthHeaders() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return {};
    return { 'Authorization': `Bearer ${token}` };
}

let current = { path: null, side: null, line: null };

function openComment(el) {
    const path = el.getAttribute("data-path");
    const side = el.getAttribute("data-side");
    const line = el.getAttribute("data-line");
    if (!path || !side || !line) return;

    current = { path, side, line: parseInt(line, 10) };
    document.getElementById("modalMeta").textContent = `${path} · ${side} · line ${line}`;
    document.getElementById("msg").value = "";
    document.getElementById("sug").value = "";
    document.getElementById("modal").classList.remove("hidden");
}

function hideModal() {
    document.getElementById("modal").classList.add("hidden");
}

function closeIfBackdrop(ev) {
    if (ev.target && ev.target.id === "modal") hideModal();
}

async function submitComment() {
    const message = document.getElementById("msg").value.trim();
    const suggestion = document.getElementById("sug").value;
    if (!message) return;

    // Preserve scroll position across reload
    const scrollPos = window.scrollY || document.documentElement.scrollTop;
    sessionStorage.setItem('review-scroll-pos', scrollPos.toString());

    const headers = {
        "Content-Type": "application/json",
        ...getAuthHeaders()
    };

    const res = await fetch("/api/comment", {
        method: "POST",
        headers,
        body: JSON.stringify({
            path: current.path,
            side: current.side,
            line: current.line,
            message,
            suggestion: suggestion && suggestion.trim() ? suggestion : null
        })
    });

    if (res.ok) {
        window.location.reload();
        // Scroll position will be restored in DOMContentLoaded handler
    } else if (res.status === 401 || res.status === 403) {
        // Authentication failed - clear token and notify user
        localStorage.removeItem(AUTH_TOKEN_KEY);
        sessionStorage.removeItem('review-scroll-pos');
        alert('Authentication failed. Please refresh and enter a valid auth token.');
    } else if (res.status === 429) {
        // Rate limited
        sessionStorage.removeItem('review-scroll-pos');
        alert('Rate limit exceeded. Please wait before submitting more comments.');
    } else {
        // Clear saved scroll position on error
        sessionStorage.removeItem('review-scroll-pos');
    }
}

// Handle Escape key to close modal
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideModal();

    // Skip keyboard nav if modal is open or user is typing
    const modal = document.getElementById("modal");
    if (modal && !modal.classList.contains("hidden")) return;
    if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;

    // Keyboard navigation: j=next file, k=prev file, n=next changed, p=prev changed
    if (e.key === "j" || e.key === "k" || e.key === "n" || e.key === "p") {
        navigateFiles(e.key);
    }
});

// Theme management
const THEMES = ['mocha', 'macchiato', 'frappe', 'latte'];
const THEME_KEY = 'dot-work-review-theme';

function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'mocha';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
}

function cycleTheme() {
    const current = getCurrentTheme();
    const idx = THEMES.indexOf(current);
    const next = THEMES[(idx + 1) % THEMES.length];
    setTheme(next);
}

// Initialize theme from localStorage
function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved && THEMES.includes(saved)) {
        setTheme(saved);
    }
}

// Setup theme toggle button
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    const btn = document.getElementById("themeToggle");
    if (btn) {
        btn.addEventListener("click", cycleTheme);
    }
    // Initialize diff view from localStorage
    initDiffView();

    // Restore scroll position after comment submission
    const savedScroll = sessionStorage.getItem('review-scroll-pos');
    if (savedScroll) {
        const scrollPos = parseInt(savedScroll, 10);
        if (!isNaN(scrollPos)) {
            window.scrollTo(0, scrollPos);
        }
        sessionStorage.removeItem('review-scroll-pos');
    }
});

// ============================================
// Diff View Toggle (Unified/Split)
// ============================================

const DIFF_VIEW_KEY = 'dot-work-review-diff-view';

function initDiffView() {
    const saved = localStorage.getItem(DIFF_VIEW_KEY) || 'unified';
    setDiffView(saved);
}

function setDiffView(view) {
    const unifiedView = document.getElementById('unifiedView');
    const splitView = document.getElementById('splitView');
    const unifiedBtn = document.getElementById('unifiedViewBtn');
    const splitBtn = document.getElementById('splitViewBtn');

    if (!unifiedView || !splitView) return;

    localStorage.setItem(DIFF_VIEW_KEY, view);

    if (view === 'split') {
        unifiedView.classList.add('hidden');
        splitView.classList.remove('hidden');
        if (unifiedBtn) {
            unifiedBtn.classList.remove('bg-ctp-surface0', 'text-ctp-text');
            unifiedBtn.classList.add('bg-ctp-surface1', 'text-ctp-subtext0');
        }
        if (splitBtn) {
            splitBtn.classList.add('bg-ctp-surface0', 'text-ctp-text');
            splitBtn.classList.remove('bg-ctp-surface1', 'text-ctp-subtext0');
        }
    } else {
        unifiedView.classList.remove('hidden');
        splitView.classList.add('hidden');
        if (unifiedBtn) {
            unifiedBtn.classList.add('bg-ctp-surface0', 'text-ctp-text');
            unifiedBtn.classList.remove('bg-ctp-surface1', 'text-ctp-subtext0');
        }
        if (splitBtn) {
            splitBtn.classList.remove('bg-ctp-surface0', 'text-ctp-text');
            splitBtn.classList.add('bg-ctp-surface1', 'text-ctp-subtext0');
        }
    }
}

// ============================================
// File Tree Component
// ============================================

const TREE_STATE_KEY = 'dot-work-review-tree-state';

/**
 * Build a hierarchical tree structure from flat file paths.
 * @param {string[]} files - Array of file paths
 * @returns {Object} Tree structure with folders and files
 */
function buildFileTree(files) {
    const tree = { name: '', children: {}, files: [] };

    for (const filePath of files) {
        const parts = filePath.split('/');
        let node = tree;

        // Navigate/create folder structure
        for (let i = 0; i < parts.length - 1; i++) {
            const folder = parts[i];
            if (!node.children[folder]) {
                node.children[folder] = { name: folder, children: {}, files: [] };
            }
            node = node.children[folder];
        }

        // Add file to current folder
        node.files.push({ name: parts[parts.length - 1], path: filePath });
    }

    return tree;
}

/**
 * Get saved tree expansion state from localStorage.
 * @returns {Set<string>} Set of expanded folder paths
 */
function getTreeState() {
    try {
        const saved = localStorage.getItem(TREE_STATE_KEY);
        return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch {
        return new Set();
    }
}

/**
 * Save tree expansion state to localStorage.
 * @param {Set<string>} expanded - Set of expanded folder paths
 */
function saveTreeState(expanded) {
    localStorage.setItem(TREE_STATE_KEY, JSON.stringify([...expanded]));
}

/**
 * Render the file tree into a container element.
 * @param {string} containerId - ID of the container element
 * @param {string[]} files - Array of file paths
 * @param {Set<string>} changed - Set of changed file paths
 * @param {string} currentPath - Currently selected file path
 */
function initFileTree(containerId, files, changed, currentPath) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const tree = buildFileTree(files);
    const expanded = getTreeState();

    // Auto-expand path to current file
    if (currentPath) {
        const parts = currentPath.split('/');
        let path = '';
        for (let i = 0; i < parts.length - 1; i++) {
            path = path ? `${path}/${parts[i]}` : parts[i];
            expanded.add(path);
        }
        saveTreeState(expanded);
    }

    container.innerHTML = '';
    renderTree(container, tree, '', changed, currentPath, expanded);
}

/**
 * Recursively render tree nodes.
 */
function renderTree(container, node, parentPath, changed, currentPath, expanded) {
    // Sort folders first, then files
    const folders = Object.keys(node.children).sort();
    const files = [...node.files].sort((a, b) => a.name.localeCompare(b.name));

    // Render folders
    for (const folderName of folders) {
        const folder = node.children[folderName];
        const folderPath = parentPath ? `${parentPath}/${folderName}` : folderName;
        const isExpanded = expanded.has(folderPath);

        // Check if folder contains changed files
        const hasChangedFiles = hasChangedDescendant(folder, changed, folderPath);

        // Folder row
        const folderEl = document.createElement('div');
        folderEl.className = 'folder-row px-2 py-1.5 flex items-center gap-1.5 cursor-pointer hover:bg-ctp-surface0 select-none';
        folderEl.style.paddingLeft = `${(parentPath.split('/').filter(Boolean).length) * 12 + 8}px`;
        folderEl.innerHTML = `
            <span class="text-ctp-overlay1 transition-transform ${isExpanded ? 'rotate-90' : ''}" style="font-size: 10px;">▶</span>
            <span class="text-ctp-yellow">📁</span>
            <span class="text-ctp-text flex-1 truncate">${folderName}</span>
            ${hasChangedFiles ? '<span class="w-2 h-2 rounded-full bg-ctp-blue"></span>' : ''}
        `;

        folderEl.addEventListener('click', () => {
            if (expanded.has(folderPath)) {
                expanded.delete(folderPath);
            } else {
                expanded.add(folderPath);
            }
            saveTreeState(expanded);
            initFileTree(container.id, Array.from(changed).concat(
                container.querySelectorAll('[data-path]').length > 0
                    ? [...container.querySelectorAll('[data-path]')].map(el => el.getAttribute('data-path'))
                    : []
            ).filter((v, i, a) => a.indexOf(v) === i), changed, currentPath);
            // Re-render
            const allFiles = [];
            collectFiles(node, parentPath ? parentPath.split('/').slice(0, -1).join('/') : '', allFiles);
            // Just toggle visibility instead of full re-render
            const childContainer = folderEl.nextElementSibling;
            if (childContainer && childContainer.classList.contains('folder-children')) {
                const arrow = folderEl.querySelector('span');
                if (expanded.has(folderPath)) {
                    childContainer.style.display = 'block';
                    arrow.classList.add('rotate-90');
                } else {
                    childContainer.style.display = 'none';
                    arrow.classList.remove('rotate-90');
                }
            }
        });

        container.appendChild(folderEl);

        // Child container
        const childContainer = document.createElement('div');
        childContainer.className = 'folder-children';
        childContainer.style.display = isExpanded ? 'block' : 'none';
        renderTree(childContainer, folder, folderPath, changed, currentPath, expanded);
        container.appendChild(childContainer);
    }

    // Render files
    for (const file of files) {
        const isChanged = changed.has(file.path);
        const isActive = file.path === currentPath;

        const fileEl = document.createElement('a');
        fileEl.href = `/?path=${encodeURIComponent(file.path)}`;
        fileEl.className = `file-row px-2 py-1.5 flex items-center gap-1.5 no-underline hover:bg-ctp-surface0 ${isActive ? 'bg-ctp-surface0' : ''}`;
        fileEl.style.paddingLeft = `${(parentPath.split('/').filter(Boolean).length) * 12 + 24}px`;
        fileEl.setAttribute('data-path', file.path);

        const icon = getFileIcon(file.name);
        fileEl.innerHTML = `
            <span>${icon}</span>
            <span class="text-ctp-text flex-1 truncate">${file.name}</span>
            ${isChanged ? '<span class="text-xs px-1.5 py-0.5 border border-ctp-surface2 rounded-full text-ctp-blue">M</span>' : ''}
        `;

        container.appendChild(fileEl);
    }
}

/**
 * Check if a folder contains any changed files.
 */
function hasChangedDescendant(node, changed, basePath) {
    for (const file of node.files) {
        if (changed.has(file.path)) return true;
    }
    for (const folderName of Object.keys(node.children)) {
        const folderPath = basePath ? `${basePath}/${folderName}` : folderName;
        if (hasChangedDescendant(node.children[folderName], changed, folderPath)) return true;
    }
    return false;
}

/**
 * Collect all files from a tree node.
 */
function collectFiles(node, basePath, result) {
    for (const file of node.files) {
        result.push(file.path);
    }
    for (const folderName of Object.keys(node.children)) {
        collectFiles(node.children[folderName], basePath ? `${basePath}/${folderName}` : folderName, result);
    }
}

/**
 * Get an appropriate icon for a file based on extension.
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop()?.toLowerCase();
    const icons = {
        'py': '🐍',
        'js': '📜',
        'ts': '📘',
        'jsx': '⚛️',
        'tsx': '⚛️',
        'html': '🌐',
        'css': '🎨',
        'json': '📋',
        'md': '📝',
        'yml': '⚙️',
        'yaml': '⚙️',
        'toml': '⚙️',
        'txt': '📄',
        'sh': '🖥️',
        'bash': '🖥️',
        'sql': '🗃️',
        'rs': '🦀',
        'go': '🔵',
        'java': '☕',
        'rb': '💎',
        'php': '🐘',
        'c': '©️',
        'cpp': '➕',
        'h': '📎',
        'swift': '🦅',
        'kt': '🟣',
        'lock': '🔒',
        'gitignore': '👁️',
    };
    return icons[ext] || '📄';
}

// ============================================
// Keyboard Navigation
// ============================================

/**
 * Navigate between files using keyboard shortcuts.
 * j = next file, k = prev file, n = next changed, p = prev changed
 */
function navigateFiles(key) {
    // FILES and CHANGED are defined in the HTML template
    if (typeof FILES === 'undefined' || !FILES.length) return;

    const currentPath = typeof CURRENT_PATH !== 'undefined' ? CURRENT_PATH : '';
    const currentIdx = FILES.indexOf(currentPath);
    const changedArray = typeof CHANGED !== 'undefined' ? [...CHANGED] : [];

    let targetPath = null;

    if (key === 'j') {
        // Next file
        const nextIdx = currentIdx < FILES.length - 1 ? currentIdx + 1 : 0;
        targetPath = FILES[nextIdx];
    } else if (key === 'k') {
        // Previous file
        const prevIdx = currentIdx > 0 ? currentIdx - 1 : FILES.length - 1;
        targetPath = FILES[prevIdx];
    } else if (key === 'n') {
        // Next changed file
        if (!changedArray.length) return;
        const changedIdx = changedArray.indexOf(currentPath);
        const nextIdx = changedIdx < changedArray.length - 1 ? changedIdx + 1 : 0;
        targetPath = changedArray[nextIdx];
    } else if (key === 'p') {
        // Previous changed file
        if (!changedArray.length) return;
        const changedIdx = changedArray.indexOf(currentPath);
        const prevIdx = changedIdx > 0 ? changedIdx - 1 : changedArray.length - 1;
        targetPath = changedArray[prevIdx];
    }

    if (targetPath && targetPath !== currentPath) {
        window.location.href = `/?path=${encodeURIComponent(targetPath)}`;
    }
}
