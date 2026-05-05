
'use strict';

// ── Formatting ────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const fmt = n => '$' + (+n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

// ── Default Dates ─────────────────────────────────────────────────
(function setDates() {
    const now = new Date();
    const iso = d => d.toISOString().slice(0, 10);
    const due = new Date(now); due.setDate(due.getDate() + 30);
    $('issue-date').value = iso(now);
    $('due-date').value = iso(due);
})();

// ── Invoice Ref Sync ──────────────────────────────────────────────
function syncRef(v) { $('sum-ref').textContent = v || '—'; }

// ── Line Items ────────────────────────────────────────────────────
let rowId = 0;

function addRow(desc = '', qty = '', price = '') {
    const id = ++rowId;
    const tr = document.createElement('tr');
    tr.className = 'item-row';
    tr.dataset.id = id;
    tr.innerHTML = `
    <td><input type="text"   name="description[]" placeholder="Design, development, consultation…" value="${esc(desc)}"></td>
    <td><input type="number" name="qty[]"   class="qty-in"   min="0.01" step="any"  value="${esc(qty)}"   placeholder="1"    oninput="calc()"></td>
    <td><input type="number" name="price[]" class="price-in" min="0"    step="0.01" value="${esc(price)}" placeholder="0.00" oninput="calc()"></td>
    <td class="amt">$0.00</td>
    <td><button type="button" class="del-btn" onclick="delRow(this)" title="Remove row">✕</button></td>
  `;
    $('items-body').appendChild(tr);
    if (qty && price) calc();
    updateBadge();
    tr.querySelector('input[name="description[]"]').focus();
}

function delRow(btn) {
    if (document.querySelectorAll('.item-row').length <= 1) return;
    btn.closest('.item-row').remove();
    calc();
    updateBadge();
}

function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
function updateBadge() {
    const n = document.querySelectorAll('.item-row').length;
    $('item-ct').textContent = n;
}

// ── Live Totals ───────────────────────────────────────────────────
function calc() {
    let sub = 0;
    document.querySelectorAll('.item-row').forEach(row => {
        const q = parseFloat(row.querySelector('.qty-in').value) || 0;
        const p = parseFloat(row.querySelector('.price-in').value) || 0;
        const a = q * p;
        sub += a;
        row.querySelector('.amt').textContent = fmt(a);
    });

    const tr = parseFloat($('tax-rate').value) || 0;
    const dr = parseFloat($('disc-rate').value) || 0;
    const ta = sub * tr / 100;
    const da = sub * dr / 100;
    const tot = sub + ta - da;
    const cnt = document.querySelectorAll('.item-row').length;

    $('s-items').textContent = cnt + (cnt === 1 ? ' item' : ' items');
    $('s-sub').textContent = fmt(sub);
    $('s-total').textContent = fmt(tot);

    const taxRow = $('tax-row');
    const discRow = $('disc-row');
    if (tr > 0) {
        taxRow.style.display = '';
        $('tax-label').textContent = `Tax (${tr}%)`;
        $('s-tax').textContent = fmt(ta);
    } else taxRow.style.display = 'none';

    if (dr > 0) {
        discRow.style.display = '';
        $('disc-label').textContent = `Discount (${dr}%)`;
        $('s-disc').textContent = '−' + fmt(da);
    } else discRow.style.display = 'none';
}

// ── Submit Handler ────────────────────────────────────────────────
function onSubmit(e) {
    const btn = $('gen-btn');
    btn.classList.add('busy');
    btn.disabled = true;
    // PDF download triggers page response; re-enable after delay
    setTimeout(() => { btn.classList.remove('busy'); btn.disabled = false; }, 4000);
}

// ── Init ──────────────────────────────────────────────────────────
addRow();   // start with one blank row
