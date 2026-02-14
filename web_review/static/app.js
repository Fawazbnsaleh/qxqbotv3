let allSamples = [];
const CATEGORIES = [
    'طبيعي',
    'سبام',
    'غش أكاديمي (عرض)', 'غش أكاديمي (طلب)',
    'احتيال طبي (عرض)', 'احتيال طبي (طلب)',
    'احتيال مالي (عرض)', 'احتيال مالي (طلب)',
    'تهكير (عرض)', 'تهكير (طلب)',
    'غير أخلاقي (عرض)', 'غير أخلاقي (طلب)'
];

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchSamples();

    document.getElementById('search').addEventListener('input', filterSamples);
    document.getElementById('filter-category').addEventListener('change', filterSamples);
    document.getElementById('filter-confidence').addEventListener('change', filterSamples);
    document.getElementById('filter-match').addEventListener('change', filterSamples);
});

async function fetchStats() {
    const res = await fetch('/api/stats');
    const stats = await res.json();
    const container = document.getElementById('stats-bar');
    container.innerHTML = Object.entries(stats)
        .map(([key, val]) => `<div class="stat-item">${key}: <span>${val}</span></div>`)
        .join('');
}

async function fetchSamples() {
    document.getElementById('loading').style.display = 'block';
    const res = await fetch('/api/samples');
    allSamples = await res.json();
    document.getElementById('loading').style.display = 'none';
    filterSamples();
}

function getLabels(sample) {
    // Support both old 'label' and new 'labels' format
    if (sample.labels && Array.isArray(sample.labels)) {
        return sample.labels;
    }
    return sample.label ? [sample.label] : [];
}

function filterSamples() {
    const query = document.getElementById('search').value.toLowerCase();
    const cat = document.getElementById('filter-category').value;
    const confFilter = document.getElementById('filter-confidence').value;
    const matchFilter = document.getElementById('filter-match').value;

    const filtered = allSamples.filter(s => {
        const matchesQuery = s.text.toLowerCase().includes(query);
        const labels = getLabels(s);
        const matchesCat = cat === 'all' || labels.includes(cat);

        let matchesConf = true;
        if (confFilter === 'gray') {
            matchesConf = s.is_gray_zone === true;
        } else if (confFilter === 'low') {
            matchesConf = s.confidence < s.threshold;
        } else if (confFilter === 'high') {
            matchesConf = s.confidence >= s.threshold + 10;
        }

        let matchesMatch = true;
        if (matchFilter === 'mismatch') {
            matchesMatch = !labels.includes(s.predicted_label);
        } else if (matchFilter === 'match') {
            matchesMatch = labels.includes(s.predicted_label);
        }

        return matchesQuery && matchesCat && matchesConf && matchesMatch;
    });

    document.getElementById('filter-count').textContent = `عرض ${Math.min(filtered.length, 100)} من ${filtered.length}`;
    renderSamples(filtered.slice(0, 100));
}

function renderSamples(samples) {
    const container = document.getElementById('sample-list');
    container.innerHTML = samples.map(s => {
        const index = allSamples.indexOf(s);
        const labels = getLabels(s);
        const isMismatch = !labels.includes(s.predicted_label);
        const mismatchClass = isMismatch ? 'mismatch' : '';
        const grayZoneClass = s.is_gray_zone ? 'gray-zone' : '';
        const keywordBadge = s.matched_keyword
            ? `<span class="keyword-badge">🔑 ${s.matched_keyword}</span>`
            : '';

        let confColor = '#22c55e';
        if (s.confidence < s.threshold) confColor = '#ef4444';
        else if (s.confidence < s.threshold + 10) confColor = '#f59e0b';

        // Helper to get consistent class name
        const getClassName = (l) => {
            if (l.startsWith('احتيال طبي')) return 'label-احتيال-طبي';
            if (l.startsWith('احتيال مالي')) return 'label-احتيال-مالي';
            if (l.startsWith('طبيعي')) return 'label-طبيعي';
            return 'label-' + l.split(' ')[0];
        };

        // Multi-label badges
        const labelBadges = labels.map(l =>
            `<span class="label-badge ${getClassName(l)}">${l}</span>`
        ).join(' ');

        // Checkbox buttons for each category
        const checkboxes = CATEGORIES.map(cat => {
            const isChecked = labels.includes(cat);
            const checkedClass = isChecked ? 'checked' : '';
            // Better display name
            let displayName = cat.split(' ').slice(0, 2).join(' '); // Take first 2 words
            if (cat === 'طبيعي' || cat === 'سبام') displayName = cat;

            return `<button class="label-btn ${checkedClass}" data-cat="${cat}" onclick="toggleLabel(${index}, '${cat}')">
                ${isChecked ? '✓ ' : ''}${displayName}
            </button>`;
        }).join('');

        return `
        <div class="sample-card ${mismatchClass} ${grayZoneClass}" data-index="${index}">
            <div class="sample-header">
                <div class="labels-container">${labelBadges}</div>
                <div class="prediction-info">
                    <span class="prediction-label">🤖 ${s.predicted_label}</span>
                    <span class="confidence-badge" style="background: ${confColor}">${s.confidence}%</span>
                    ${keywordBadge}
                </div>
            </div>
            <div class="sample-text">${escapeHtml(s.text)}</div>
            <div class="actions">
                ${checkboxes}
                <button class="btn-delete" onclick="deleteSample(${index})">🗑️</button>
            </div>
        </div>
    `}).join('');
}

async function toggleLabel(index, label) {
    const sample = allSamples[index];
    if (!sample) return;

    let labels = getLabels(sample);

    if (labels.includes(label)) {
        // Remove label (but keep at least one)
        if (labels.length > 1) {
            labels = labels.filter(l => l !== label);
        }
    } else {
        // Add label
        labels.push(label);
        // If adding a violation, remove Normal
        if (label !== 'طبيعي' && labels.includes('طبيعي')) {
            labels = labels.filter(l => l !== 'طبيعي');
        }
        // If adding Normal, remove all violations
        if (label === 'طبيعي') {
            labels = ['طبيعي'];
        }
    }

    // Update UI immediately
    sample.labels = labels;
    sample.label = labels[0]; // Keep backward compatibility

    const card = document.querySelector(`.sample-card[data-index="${index}"]`);
    if (card) {
        // Update badges
        const labelsContainer = card.querySelector('.labels-container');
        const getClassName = (l) => {
            if (l.startsWith('احتيال طبي')) return 'label-احتيال-طبي';
            if (l.startsWith('احتيال مالي')) return 'label-احتيال-مالي';
            if (l.startsWith('طبيعي')) return 'label-طبيعي';
            return 'label-' + l.split(' ')[0];
        };

        labelsContainer.innerHTML = labels.map(l =>
            `<span class="label-badge ${getClassName(l)}">${l}</span>`
        ).join(' ');

        // Update buttons
        const buttons = card.querySelectorAll('.label-btn');
        buttons.forEach(btn => {
            const btnLabel = btn.getAttribute('data-cat');
            if (btnLabel) {
                const isChecked = labels.includes(btnLabel);
                btn.className = `label-btn ${isChecked ? 'checked' : ''}`;

                let displayName = btnLabel.split(' ').slice(0, 2).join(' ');
                if (btnLabel === 'طبيعي' || btnLabel === 'سبام') displayName = btnLabel;

                btn.innerHTML = `${isChecked ? '✓ ' : ''}${displayName}`;
            }
        });
    }

    try {
        const res = await fetch('/api/update', {
            method: 'POST',
            body: JSON.stringify({
                original_text: sample.text,
                new_labels: labels
            })
        });

        if (!res.ok) throw new Error('Failed');
        fetchStats();

    } catch (e) {
        alert('Error updating labels');
        console.error(e);
    }
}

async function deleteSample(index) {
    if (!confirm('حذف هذه العينة؟')) return;

    const sample = allSamples[index];
    if (!sample) return;

    try {
        const res = await fetch('/api/delete', {
            method: 'POST',
            body: JSON.stringify({
                original_text: sample.text
            })
        });

        if (!res.ok) throw new Error('Failed');

        const card = document.querySelector(`.sample-card[data-index="${index}"]`);
        if (card) card.remove();

        allSamples.splice(index, 1);
        fetchStats();

    } catch (e) {
        alert('Error deleting sample');
        console.error(e);
    }
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function createBackup() {
    const btn = document.getElementById('backup-btn');
    const originalText = btn.innerText;
    btn.innerText = '⏳ جاري الحفظ...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/backup');
        const result = await res.json();

        if (result.success) {
            btn.innerText = `✅ تم الحفظ (${result.total_backups})`;
            setTimeout(() => {
                btn.innerText = originalText;
            }, 3000);
        } else {
            throw new Error(result.error);
        }
    } catch (e) {
        btn.innerText = '❌ فشل الحفظ';
        console.error(e);
        setTimeout(() => {
            btn.innerText = originalText;
        }, 3000);
    } finally {
        btn.disabled = false;
    }
}

async function retrainModel() {
    const btn = document.getElementById('retrain-btn');
    const originalText = btn.innerHTML;

    if (!confirm('هل أنت متأكد أنك تريد إعادة تدريب النموذج بالبيانات الحالية؟ قد تستغرق العملية دقيقة.')) return;

    btn.innerHTML = '⏳ جاري التدريب...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/retrain');
        const result = await res.json();

        if (result.success) {
            btn.innerHTML = '✅ تم التدريب!';
            alert("تم إعادة التدريب بنجاح!\\n\\nملخص النتائج:\\n" + result.output);
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 3000);
        } else {
            throw new Error(result.error);
        }
    } catch (e) {
        alert('فشل التدريب: ' + e.message);
        btn.innerHTML = '❌ خطأ';
        btn.disabled = false;
    }
}
