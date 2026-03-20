// DOM elements
const modelSelect = document.getElementById('modelSelect');
const textBox = document.getElementById('textBox');
const generateBtn = document.getElementById('generateBtn');
const checkBtn = document.getElementById('checkBtn');
const diffView = document.getElementById('diffView');
const applyChangesBtn = document.getElementById('applyChangesBtn');
const editAgainBtn = document.getElementById('editAgainBtn');
const doneBtn = document.getElementById('doneBtn');
const themeToggle = document.getElementById('themeToggle');

// Theme toggle
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
    document.documentElement.classList.add('light');
    themeToggle.textContent = '☀️';
}

themeToggle.addEventListener('click', () => {
    const isLight = document.documentElement.classList.toggle('light');
    themeToggle.textContent = isLight ? '☀️' : '🌙';
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
});

// Call /set_model when model selector changes
modelSelect.addEventListener('change', async () => {
    try {
        const response = await fetch(`/set_model?model=${encodeURIComponent(modelSelect.value)}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error(`Server Error: ${response.status}`);
    } catch (err) {
        console.error('Failed to set model:', err);
    }
});

// Escape HTML for safe display
function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Build overlay of original text with word-level changes. Style: -error- +correction+
// diff: [{original, correction, start, end}, ...]
// acceptanceState: Map<index, true|false> - true=accepted, false=denied, undefined=pending
function renderOverlay(originalText, diff, acceptanceState) {
    if (!diff || !Array.isArray(diff) || diff.length === 0) {
        return escapeHtml(originalText) + ' <span class="diff-no-changes">No changes found.</span>';
    }

    const parts = [];
    let lastEnd = 0;

    diff.forEach((change, idx) => {
        const { original, correction, start, end } = change;
        // Unchanged text before this change
        if (start > lastEnd) {
            parts.push(escapeHtml(originalText.slice(lastEnd, start)));
        }
        lastEnd = end;

        const decided = acceptanceState.get(idx);
        let content;
        if (decided === true) {
            // Accepted: show correction in green
            content = `<span class="diff-correction">${escapeHtml(correction || original)}</span>`;
        } else if (decided === false) {
            // Denied: show original, no highlight
            content = `<span class="diff-unchanged">${escapeHtml(original)}</span>`;
        } else {
            // Pending: error (red) + correction (green) inline in original text flow
            const errPart = original ? `<span class="diff-error">${escapeHtml(original)}</span>` : '';
            const corrPart = correction ? ` <span class="diff-correction-suggestion">${escapeHtml(correction)}</span>` : '';
            content = `<span class="diff-change" data-change-idx="${idx}">${errPart}${corrPart}<span class="diff-actions"><span class="btn-accept" role="button" tabindex="0" title="Accept">✓</span><span class="btn-deny" role="button" tabindex="0" title="Deny">✗</span></span></span>`;
        }
        parts.push(content);
    });

    // Trailing unchanged text
    if (lastEnd < originalText.length) {
        parts.push(escapeHtml(originalText.slice(lastEnd)));
    }

    return parts.join('');
}

// Rebuild final text from original + diff + acceptance state
function buildFinalText(originalText, diff, acceptanceState) {
    if (!diff || diff.length === 0) return originalText;

    const parts = [];
    let lastEnd = 0;

    diff.forEach((change, idx) => {
        const { original, correction, start, end } = change;
        if (start > lastEnd) {
            parts.push(originalText.slice(lastEnd, start));
        }
        lastEnd = end;
        const denied = acceptanceState.get(idx) === false;
        parts.push(denied ? (original || '') : (correction !== undefined && correction !== null ? correction : original || ''));
    });
    if (lastEnd < originalText.length) {
        parts.push(originalText.slice(lastEnd));
    }
    return parts.join('');
}

// Switch to diff view mode with overlay
function showDiffView(originalText, diff, correctedText) {
    textBox.style.display = 'none';
    diffView.style.display = 'block';
    diffView.dataset.originalText = originalText;
    diffView.dataset.correctedText = correctedText || originalText;

    const acceptanceState = new Map();
    diffView._diff = diff;
    diffView._acceptanceState = acceptanceState;

    const allDecided = () => diff.every((_, idx) => acceptanceState.has(idx));

    const updateDisplay = () => {
        diffView.innerHTML = renderOverlay(originalText, diff, acceptanceState);
        // Re-bind Accept/Deny buttons
        const handleAccept = (btn) => {
            const idx = parseInt(btn.closest('.diff-change').dataset.changeIdx, 10);
            acceptanceState.set(idx, true);
            updateDisplay();
            updateButtonVisibility();
        };
        const handleDeny = (btn) => {
            const idx = parseInt(btn.closest('.diff-change').dataset.changeIdx, 10);
            acceptanceState.set(idx, false);
            updateDisplay();
            updateButtonVisibility();
        };
        diffView.querySelectorAll('.btn-accept').forEach(btn => {
            btn.onclick = () => handleAccept(btn);
            btn.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleAccept(btn); } };
        });
        diffView.querySelectorAll('.btn-deny').forEach(btn => {
            btn.onclick = () => handleDeny(btn);
            btn.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleDeny(btn); } };
        });
    };

    const updateButtonVisibility = () => {
        if (diff.length === 0) {
            applyChangesBtn.style.display = 'none';
            editAgainBtn.style.display = 'inline-block';
            doneBtn.style.display = 'none';
        } else if (allDecided()) {
            applyChangesBtn.style.display = 'none';
            editAgainBtn.style.display = 'none';
            doneBtn.style.display = 'inline-block';
        } else {
            applyChangesBtn.style.display = 'inline-block';
            editAgainBtn.style.display = 'inline-block';
            doneBtn.style.display = 'none';
        }
    };

    updateDisplay();

    applyChangesBtn._originalText = originalText;
    editAgainBtn._originalText = originalText;
    updateButtonVisibility();
}

// Switch back to edit mode
function showEditMode() {
    textBox.style.display = 'block';
    diffView.style.display = 'none';
    diffView.innerHTML = '';
    diffView._diff = null;
    diffView._acceptanceState = null;
    applyChangesBtn.style.display = 'none';
    editAgainBtn.style.display = 'none';
    doneBtn.style.display = 'none';
}

generateBtn.addEventListener('click', async () => {
    const inputText = textBox.value;
    diffView.innerHTML = '<span class="loading-indicator"><span class="loading-dots"><span></span><span></span><span></span></span>Generating…</span>';
    textBox.style.display = 'none';
    diffView.style.display = 'block';
    applyChangesBtn.style.display = 'none';
    editAgainBtn.style.display = 'none';
    doneBtn.style.display = 'none';

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: inputText })
        });

        if (!response.ok) throw new Error(`Server Error: ${response.status}`);

        const data = await response.json();
        const generatedText = data.generated_text || '';

        diffView.innerHTML = escapeHtml(inputText) + (inputText ? '\n' : '') + '<span class="generated-text">' + escapeHtml(generatedText) + '</span>';
        editAgainBtn.style.display = 'inline-block';
        editAgainBtn._originalText = inputText + (inputText ? '\n' : '') + generatedText;
    } catch (err) {
        diffView.innerHTML = `<span class="diff-error">Error: ${escapeHtml(err.message)}</span>`;
        editAgainBtn.style.display = 'inline-block';
        editAgainBtn._originalText = inputText;
    }
});

checkBtn.addEventListener('click', async () => {
    const originalText = textBox.value;
    diffView.innerHTML = '<span class="loading-indicator"><span class="loading-dots"><span></span><span></span><span></span></span>Analyzing…</span>';
    textBox.style.display = 'none';
    diffView.style.display = 'block';
    applyChangesBtn.style.display = 'none';
    editAgainBtn.style.display = 'none';

    try {
        const response = await fetch("/correct_orthography", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: originalText })
        });

        if (!response.ok) throw new Error(`Server Error: ${response.status}`);

        const data = await response.json();
        const diff = data.diff || [];
        const correctedText = data.corrected_text;

        showDiffView(originalText, diff, correctedText);
    } catch (err) {
        diffView.innerHTML = `<span class="diff-error">Error: ${escapeHtml(err.message)}</span>`;
        editAgainBtn.style.display = 'inline-block';
        editAgainBtn._originalText = originalText;
    }
});

applyChangesBtn.addEventListener('click', () => {
    const originalText = applyChangesBtn._originalText;
    const diff = diffView._diff;
    const acceptanceState = diffView._acceptanceState;
    const finalText = diff && acceptanceState
        ? buildFinalText(originalText, diff, acceptanceState)
        : originalText;
    textBox.value = finalText;
    showEditMode();
});

editAgainBtn.addEventListener('click', () => {
    const original = editAgainBtn._originalText;
    if (original !== undefined) {
        textBox.value = original;
    }
    showEditMode();
});

doneBtn.addEventListener('click', () => {
    const originalText = applyChangesBtn._originalText;
    const diff = diffView._diff;
    const acceptanceState = diffView._acceptanceState;
    const finalText = diff && acceptanceState
        ? buildFinalText(originalText, diff, acceptanceState)
        : originalText;
    textBox.value = finalText;
    showEditMode();
});
