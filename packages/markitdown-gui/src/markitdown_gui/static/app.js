let currentMarkdown = '';
let currentFilename = 'converted.md';

document.addEventListener('DOMContentLoaded', () => {
    setupDropzone();
    setupMarked();
});

function setupMarked() {
    if (window.marked) {
        marked.setOptions({
            highlight: function(code, lang) {
                if (window.hljs && lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return code;
            },
            breaks: true,
            gfm: true
        });
    }
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    document.getElementById(`tab-${tab}-btn`).classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
}

function setupDropzone() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });

    dropzone.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        processFiles(Array.from(files));
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFiles(Array.from(files));
    }
}

async function processFiles(files) {
    const enablePlugins = document.getElementById('plugins-toggle').checked;
    
    if (files.length === 1) {
        await convertSingleFile(files[0], enablePlugins);
    } else {
        await convertBatchFiles(files, enablePlugins);
    }
}

async function convertSingleFile(file, enablePlugins) {
    showLoadingState(file.name);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_plugins', enablePlugins);

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Conversion failed');
        }

        const data = await response.json();
        updateDisplay(data);
    } catch (error) {
        alert(`Error: ${error.message}`);
        resetPreviewState();
    }
}

async function convertBatchFiles(files, enablePlugins) {
    showQueueSection(files);

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('enable_plugins', enablePlugins);

    try {
        const response = await fetch('/api/convert-batch', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Batch conversion failed');
        }

        const data = await response.json();
        
        // Show first result in display
        if (data.results && data.results.length > 0) {
            updateDisplay(data.results[0]);
            updateQueueStatus(data.results);
        }
    } catch (error) {
        alert(`Batch Error: ${error.message}`);
    }
}

async function convertUrl() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value.trim();
    if (!url) return;

    const enablePlugins = document.getElementById('plugins-toggle').checked;
    showLoadingState(url);

    const formData = new FormData();
    formData.append('url', url);
    formData.append('enable_plugins', enablePlugins);

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'URL conversion failed');
        }

        const data = await response.json();
        updateDisplay(data);
    } catch (error) {
        alert(`URL Error: ${error.message}`);
        resetPreviewState();
    }
}

function showLoadingState(name) {
    document.getElementById('markdown-output').value = `Converting ${name}... Please wait.`;
    document.getElementById('preview-output').innerHTML = `
        <div class="placeholder-state">
            <div class="placeholder-icon">⏳</div>
            <p>Processing <strong>${name}</strong>...</p>
        </div>
    `;
}

function resetPreviewState() {
    document.getElementById('markdown-output').value = '';
    document.getElementById('preview-output').innerHTML = `
        <div class="placeholder-state">
            <div class="placeholder-icon">✦</div>
            <p>Upload a document to view formatted live preview</p>
        </div>
    `;
    document.getElementById('raw-stats').textContent = '0 chars | 0 words';
}

function updateDisplay(data) {
    currentMarkdown = data.markdown || '';
    currentFilename = (data.filename || 'converted') + '.md';

    document.getElementById('markdown-output').value = currentMarkdown;
    
    if (window.marked) {
        document.getElementById('preview-output').innerHTML = marked.parse(currentMarkdown);
        if (window.hljs) {
            document.querySelectorAll('.markdown-rendered pre code').forEach(el => hljs.highlightElement(el));
        }
    } else {
        document.getElementById('preview-output').textContent = currentMarkdown;
    }

    const durationText = data.duration_seconds ? ` (${data.duration_seconds}s)` : '';
    document.getElementById('raw-stats').textContent = `${data.char_count} chars | ${data.word_count} words${durationText}`;
}

function showQueueSection(files) {
    const queueSec = document.getElementById('queue-section');
    const queueList = document.getElementById('queue-list');
    const queueCount = document.getElementById('queue-count');

    queueSec.style.display = 'block';
    queueCount.textContent = `${files.length} files`;

    queueList.innerHTML = files.map(f => `
        <div class="queue-item status-converting" id="q-${f.name}">
            <span>⚙️</span> ${f.name}
        </div>
    `).join('');
}

function updateQueueStatus(results) {
    results.forEach(res => {
        const item = document.getElementById(`q-${res.filename}`);
        if (item) {
            item.className = 'queue-item status-done';
            item.innerHTML = `<span>✅</span> ${res.filename}`;
            item.onclick = () => updateDisplay(res);
            item.style.cursor = 'pointer';
        }
    });
}

function copyMarkdown() {
    if (!currentMarkdown) return;
    navigator.clipboard.writeText(currentMarkdown).then(() => {
        const copyBtn = document.getElementById('copy-btn');
        const origText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<span>✓ Copied!</span>';
        setTimeout(() => copyBtn.innerHTML = origText, 2000);
    });
}

function downloadMarkdown() {
    if (!currentMarkdown) return;
    const blob = new Blob([currentMarkdown], { type: 'text/markdown;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = currentFilename;
    link.click();
    URL.revokeObjectURL(link.href);
}
