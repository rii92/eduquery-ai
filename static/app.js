/* BP Batam — frontend */

const STORAGE_KEY = 'eduquery_bp_history';

let sqlEditor = null;
let timerInterval = null;
let startTime = 0;
let aiInsightEnabled = true;

document.addEventListener('DOMContentLoaded', function () {
    loadHistory();
    sqlEditor = CodeMirror(document.getElementById('sqlBox'), {
        value: '',
        mode: 'text/x-mysql',
        theme: 'dracula',
        readOnly: true,
        lineNumbers: false,
        viewportMargin: Infinity,
        indentUnit: 2,
        tabSize: 2,
    });
    updateAIToggleUI();
});

function toggleAI() {
    aiInsightEnabled = !aiInsightEnabled;
    updateAIToggleUI();
}

function updateAIToggleUI() {
    const btn = document.getElementById('aiToggle');
    if (aiInsightEnabled) {
        btn.classList.remove('btn-outline-info');
        btn.classList.add('btn-info');
        btn.innerHTML = '<i class="bi bi-stars"></i>';
        btn.title = 'AI Insight aktif';
    } else {
        btn.classList.remove('btn-info');
        btn.classList.add('btn-outline-info');
        btn.innerHTML = '<i class="bi bi-stars-slash"></i>';
        btn.title = 'AI Insight nonaktif';
    }
}

function getSelectedProvider(name) {
    const sel = document.querySelector(`input[name="${name}"]:checked`);
    return sel ? sel.value : 'keyword';
}

function getFilterParams() {
    const tgl = document.getElementById('filterTgl').value || '';
    const izin = document.getElementById('filterIzin').value || '';
    const params = new URLSearchParams();
    if (tgl) params.set('tgl_status_terakhir', tgl);
    if (izin) params.set('perizinan', izin);
    return params.toString();
}

async function submitQuery() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question) return;

    const intentProvider = getSelectedProvider('intentProvider');
    const insightProvider = getSelectedProvider('insightProvider');
    const replyProvider = getSelectedProvider('replyProvider');
    let insightLLMProvider = 'local';
    if (insightProvider === 'llm_cloud') insightLLMProvider = 'cloud';
    else if (insightProvider === 'llm_llamacpp') insightLLMProvider = 'llamacpp';
    let actualInsightProvider = insightProvider;
    if (insightProvider === 'llm_cloud' || insightProvider === 'llm_llamacpp') actualInsightProvider = 'llm';

    try {
        showLoading(true);
        hideResult();
        resetSteps();
        startTimer();

        const encoded = encodeURIComponent(question);
        const filterParams = getFilterParams();
        let url = `/api/query/stream?message=${encoded}&intent_provider=${intentProvider}&insight_provider=${actualInsightProvider}&insight_llm_provider=${insightLLMProvider}&reply_provider=${replyProvider}`;
        if (filterParams) url += '&' + filterParams;

        const eventSource = new EventSource(url);

        eventSource.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                if (data.step) updateStep(data.step);
                if (data.progress != null) updateProgress(data.progress);
                if (data.done) {
                    eventSource.close();
                    stopTimer();
                    showResult(question, data);
                    saveToHistory(question, data);
                    showLoading(false);
                }
            } catch (e) {
                console.error('SSE parse error:', e);
            }
        };

        eventSource.onerror = function () {
            eventSource.close();
            stopTimer();
            showError('Gagal terhubung ke server.');
            showLoading(false);
        };
    } catch (e) {
        console.error('submitQuery error:', e);
        stopTimer();
        showError('Terjadi kesalahan: ' + e.message);
        showLoading(false);
    }
}

function startTimer() {
    startTime = performance.now();
    const el = document.getElementById('timerText');
    timerInterval = setInterval(() => {
        const sec = ((performance.now() - startTime) / 1000).toFixed(1);
        el.textContent = `${sec}s`;
    }, 100);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function showResult(question, data) {
    const panel = document.getElementById('resultPanel');
    panel.classList.remove('d-none');

    document.getElementById('replyBox').innerHTML = marked.parse(data.reply || '(kosong)');

    const elapsed = data.elapsed;
    if (elapsed != null) {
        document.getElementById('elapsedBadge').textContent = `${elapsed.toFixed(1)}s`;
        document.getElementById('elapsedBadge').classList.remove('d-none');
    }
    if (data.intent) {
        document.getElementById('intentBadge').textContent = data.intent;
        document.getElementById('intentBadge').classList.remove('d-none');
    }

    // Deterministic insight
    const detPanel = document.getElementById('detInsightPanel');
    if (data.deterministic_insight) {
        document.getElementById('detInsightBox').textContent = data.deterministic_insight.replace(/\*\*/g, '');
        detPanel.classList.remove('d-none');
    } else {
        detPanel.classList.add('d-none');
    }

    // LLM Insight
    const insightPanel = document.getElementById('insightPanel');
    if (data.ai_insight && aiInsightEnabled) {
        document.getElementById('insightBox').innerHTML = marked.parse(data.ai_insight);
        insightPanel.classList.remove('d-none');
    } else {
        insightPanel.classList.add('d-none');
    }

    if (sqlEditor) sqlEditor.setValue(data.sql || '-');

    renderTable(data.result);
    document.getElementById('resultBox').textContent =
        data.result ? JSON.stringify(data.result, null, 2) : '-';

    switchTab('table');
}

function hideResult() {
    document.getElementById('resultPanel').classList.add('d-none');
    document.getElementById('insightPanel').classList.add('d-none');
    document.getElementById('detInsightPanel').classList.add('d-none');
}

function showError(msg) {
    const panel = document.getElementById('resultPanel');
    panel.classList.remove('d-none');
    document.getElementById('replyBox').innerHTML = '⚠️ ' + msg;
    document.getElementById('insightPanel').classList.add('d-none');
    document.getElementById('detInsightPanel').classList.add('d-none');
    if (sqlEditor) sqlEditor.setValue('-');
    document.getElementById('resultBox').textContent = '-';
    document.getElementById('resultTable').innerHTML = '';
    document.getElementById('intentBadge').classList.add('d-none');
}

function switchTab(name) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${name}"]`).classList.add('active');
    document.getElementById(name + 'Panel').classList.add('active');
}

function renderTable(data) {
    const container = document.getElementById('resultTable');
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="text-muted small p-2 mb-0">Tidak ada data.</p>';
        return;
    }
    const cols = Object.keys(data[0]);
    let html = '<table class="table table-sm table-bordered table-striped mb-0"><thead class="table-warning"><tr>';
    cols.forEach(c => { html += `<th>${escapeHtml(c)}</th>`; });
    html += '</tr></thead><tbody>';
    data.forEach(row => {
        html += '<tr>';
        cols.forEach(c => {
            html += `<td>${escapeHtml(String(row[c] ?? ''))}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function resetSteps() {
    document.querySelectorAll('.step-item').forEach(el => {
        el.classList.remove('active', 'done');
        el.querySelector('i').className = 'bi bi-hourglass-split me-2';
        el.querySelector('.step-text').style.fontWeight = 'normal';
    });
    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.width = '0%';
}

function updateStep(stepText) {
    const steps = [
        { key: 'Menganalisis pertanyaan', id: 'analisis' },
        { key: 'Mencocokkan kata kunci', id: 'keyword' },
        { key: 'Mencocokkan semantik', id: 'embedding' },
        { key: 'Menggunakan LLM', id: 'llm' },
        { key: 'Menyusun query SQL', id: 'sql' },
        { key: 'Memvalidasi SQL', id: 'validasi' },
        { key: 'Menjalankan query ke database', id: 'eksekusi' },
        { key: 'Menganalisis insight', id: 'insight' },
        { key: 'Menyusun jawaban', id: 'jawaban' },
    ];
    const match = steps.find(s => stepText.startsWith(s.key));
    const stepId = match ? match.id : null;
    if (!stepId) return;

    document.querySelectorAll('.step-item').forEach(el => {
        if (el.dataset.step === stepId) {
            el.classList.add('active');
            el.querySelector('i').className = 'bi bi-arrow-repeat me-2 text-warning';
            el.querySelector('.step-text').style.fontWeight = 'bold';
        } else if (!el.classList.contains('done')) {
            el.querySelector('i').className = 'bi bi-hourglass-split me-2 text-muted';
        }
    });
}

function updateProgress(pct) {
    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.width = pct + '%';

    if (pct >= 10) markStepDone('analisis');
    if (pct >= 20) markStepDone('keyword');
    if (pct >= 30) markStepDone('embedding');
    if (pct >= 40) markStepDone('llm');
    if (pct >= 45) markStepDone('sql');
    if (pct >= 60) markStepDone('validasi');
    if (pct >= 75) markStepDone('eksekusi');
    if (pct >= 90) markStepDone('insight');
    if (pct >= 95) markStepDone('jawaban');
}

function markStepDone(stepId) {
    const el = document.querySelector(`.step-item[data-step="${stepId}"]`);
    if (!el || el.classList.contains('done')) return;
    el.classList.remove('active');
    el.classList.add('done');
    el.querySelector('i').className = 'bi bi-check-circle-fill me-2 text-success';
    el.querySelector('.step-text').style.fontWeight = 'normal';
}

function showLoading(v) {
    document.getElementById('loadingPanel').classList.toggle('d-none', !v);
}

function useExample(el) {
    document.getElementById('questionInput').value = el.textContent.trim();
    document.getElementById('questionInput').focus();
}

function getHistory() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch { return []; }
}

function saveToHistory(question, data) {
    const history = getHistory();
    const existing = history.findIndex(h => h.question === question);
    if (existing !== -1) history.splice(existing, 1);
    history.unshift({
        question,
        reply: data.reply || '',
        sql: data.sql || '',
        result: data.result || [],
        ai_insight: data.ai_insight || '',
        deterministic_insight: data.deterministic_insight || '',
        intent: data.intent || '',
        elapsed: data.elapsed || 0,
        timestamp: Date.now(),
    });
    if (history.length > 50) history.length = 50;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    renderHistory();
}

function loadHistory() { renderHistory(); }

function renderHistory() {
    const list = document.getElementById('historyList');
    const history = getHistory();
    list.querySelectorAll('.history-item').forEach(el => el.remove());
    if (history.length === 0) {
        document.getElementById('emptyHistory').classList.remove('d-none');
        return;
    }
    document.getElementById('emptyHistory').classList.add('d-none');
    history.forEach((item, idx) => {
        const div = document.createElement('div');
        div.className = 'list-group-item list-group-item-action history-item';
        const elapsed = item.elapsed != null ? `${item.elapsed.toFixed(1)}s` : '';
        const reply = item.reply || '';
        const truncated = reply.length > 50 ? reply.slice(0, 50) + '...' : reply;
        const intentTag = item.intent ? `<span class="badge bg-info ms-1">${escapeHtml(item.intent)}</span>` : '';
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1 me-2" onclick="restoreQuery(${idx})">
                    <div><span class="badge bg-secondary me-1">${escapeHtml(elapsed)}</span>${escapeHtml(item.question)}${intentTag}</div>
                    <small class="text-muted">${escapeHtml(truncated)}</small>
                </div>
                <button class="btn btn-sm btn-outline-danger border-0" onclick="deleteHistoryItem(${idx})" title="Hapus"><i class="bi bi-x"></i></button>
            </div>
        `;
        list.appendChild(div);
    });
}

function restoreQuery(idx) {
    const history = getHistory();
    const item = history[idx];
    if (!item) return;
    document.getElementById('questionInput').value = item.question;
    showResult(item.question, {
        reply: item.reply, sql: item.sql, result: item.result,
        ai_insight: item.ai_insight, deterministic_insight: item.deterministic_insight,
        intent: item.intent, elapsed: item.elapsed
    });
}

function deleteHistoryItem(idx) {
    const history = getHistory();
    history.splice(idx, 1);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    renderHistory();
}

function clearHistory() {
    if (!confirm('Hapus semua riwayat?')) return;
    localStorage.removeItem(STORAGE_KEY);
    renderHistory();
    hideResult();
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
