/**
 * AEGIS-AI Master Frontend Orchestrator & State Management
 * Minimalist simulation-driven UI — Dark/Light Mode support
 */

import { Api } from './api.js';
import { Charts } from './charts.js';

// ============================================================
// Global Client State
// ============================================================
const state = {
  transactions: [],
  filteredTransactions: [],
  selectedTransaction: null,
  activeFilter: 'all',
  searchQuery: '',
  summary: {},
  metrics: {},
  realism: {},
  tunerEval: null,
  tunerRecommendation: null,
  retrainHistory: [],
  currentTab: 'stream',
  darkMode: true,
};

// ============================================================
// Initialization
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
  setupThemeToggle();
  setupNavigation();
  setupEventListeners();
  setupSandboxListeners();
  await refreshGlobalState();
  triggerSandboxSimulation();
});

// ============================================================
// Theme Toggle
// ============================================================
function setupThemeToggle() {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;

  // Restore saved theme
  const saved = localStorage.getItem('aegis-theme');
  if (saved === 'light') {
    document.body.classList.add('light-mode');
    state.darkMode = false;
    btn.textContent = '☀️';
  }

  btn.addEventListener('click', () => {
    state.darkMode = !state.darkMode;
    document.body.classList.toggle('light-mode', !state.darkMode);
    btn.textContent = state.darkMode ? '🌙' : '☀️';
    localStorage.setItem('aegis-theme', state.darkMode ? 'dark' : 'light');

    // Re-draw canvas charts with new theme
    Charts.drawConfusionMatrix('chart-confusion-matrix', state.metrics?.confusion_matrix);
    Charts.drawThreatBreakdown('chart-threat-breakdown', state.metrics?.threat_breakdown);
    Charts.drawRetrainTrajectory('chart-retrain-trajectory', state.retrainHistory);
    if (state.currentTab === 'sandbox') {
      Charts.drawRiskGauge('chart-sandbox-gauge', parseGaugeProb());
    }
  });
}

function parseGaugeProb() {
  const txt = document.getElementById('sb-prob-val')?.textContent || '0%';
  return parseFloat(txt) / 100;
}

// ============================================================
// Navigation & Tab Switching
// ============================================================
function setupNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const target = tab.dataset.tab;
      state.currentTab = target;

      document.querySelectorAll('.workspace-panel').forEach(p => p.classList.remove('active'));
      const panel = document.getElementById(`workspace-${target}`);
      if (panel) panel.classList.add('active');

      // Redraw charts on tab switch
      if (target === 'retrain') {
        Charts.drawRetrainTrajectory('chart-retrain-trajectory', state.retrainHistory);
      }
      if (target === 'stream') {
        Charts.drawConfusionMatrix('chart-confusion-matrix', state.metrics?.confusion_matrix);
        Charts.drawThreatBreakdown('chart-threat-breakdown', state.metrics?.threat_breakdown);
      }
    });
  });
}

// ============================================================
// Global State Refresh
// ============================================================
async function refreshGlobalState() {
  try {
    const data = await Api.getState();
    state.summary = data.summary || {};
    state.metrics = data.metrics || {};
    state.realism = data.realism || {};
    state.tunerEval = data.tuner_eval;
    state.tunerRecommendation = data.tuner_recommendation;
    state.retrainHistory = data.retrain_history || [];
    state.transactions = data.transactions || [];

    updateGlobalHUD();
    applyTableFilters();
    updateRetrainStudio();
    updateEvasionDeck();

    Charts.drawConfusionMatrix('chart-confusion-matrix', state.metrics?.confusion_matrix);
    Charts.drawThreatBreakdown('chart-threat-breakdown', state.metrics?.threat_breakdown);
    Charts.drawRetrainTrajectory('chart-retrain-trajectory', state.retrainHistory);
  } catch (err) {
    console.error('Error refreshing state:', err);
  }
}

function updateGlobalHUD() {
  const s = state.summary;
  const m = state.metrics?.summary || {};

  setText('hud-total-txns', (s.total_transactions || 0).toLocaleString());
  setText('hud-fraud-detected', (s.predicted_fraud_count || 0).toLocaleString());
  setText('hud-roc-auc', m.roc_auc !== undefined ? m.roc_auc.toFixed(3) : '—');
  setText('hud-active-cycle', `#${state.retrainHistory.length || 1}`);

  // Side deck KPIs
  setText('side-kpi-total', (s.total_transactions || 0).toLocaleString());
  setText('side-kpi-high-risk', (s.high_risk_count || 0).toLocaleString());
  setText('side-kpi-rules-fired', (s.rules_fired_count || 0).toLocaleString());
  setText('side-kpi-evaded',
    state.tunerEval?.overall_evasion_rate !== undefined
      ? `${(state.tunerEval.overall_evasion_rate * 100).toFixed(1)}%`
      : '—');

  // Retrain studio latest metrics
  const latest = state.retrainHistory.at(-1)?.metrics;
  if (latest) {
    setText('retrain-roc',       (latest.roc_auc   || 0).toFixed(3));
    setText('retrain-recall',    (latest.recall    || 0).toFixed(3));
    setText('retrain-precision', (latest.precision || 0).toFixed(3));
    setText('retrain-f1',        (latest.f1_score  || 0).toFixed(3));
  }
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ============================================================
// Triage Table Rendering & Filtering
// ============================================================
function applyTableFilters() {
  const query  = state.searchQuery.toLowerCase();
  const filter = state.activeFilter;

  state.filteredTransactions = state.transactions.filter(t => {
    const matchSearch = !query ||
      t.transaction_id.toLowerCase().includes(query) ||
      t.sender_id.toLowerCase().includes(query) ||
      t.receiver_id.toLowerCase().includes(query) ||
      t.channel.toLowerCase().includes(query);

    if (!matchSearch) return false;

    if (filter === 'all')    return true;
    if (filter === 'high')   return t.risk_tier === 'HIGH';
    if (filter === 'medium') return t.risk_tier === 'MEDIUM';
    if (filter === 'low')    return t.risk_tier === 'LOW';
    if (filter === 'rules')  return t.fired_rules && t.fired_rules !== 'none';
    if (filter === 'evaded') return t.ground_truth_label !== 0 && t.predicted_label === 0;
    return true;
  });

  renderTableRows();
}

function renderTableRows() {
  const tbody = document.getElementById('tactical-table-body');
  if (!tbody) return;

  if (state.filteredTransactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:36px; color:var(--text-muted); font-family:var(--font-mono); font-size:12px;">No transactions match the current filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.filteredTransactions.map(t => {
    const tierClass = t.risk_tier === 'HIGH' ? 'high' : t.risk_tier === 'MEDIUM' ? 'medium' : 'low';
    const hasRules  = t.fired_rules && t.fired_rules !== 'none';
    const isCritical = hasRules && t.fired_rules.includes('HOSTAGE_CALL');
    const isEvaded  = t.ground_truth_label !== 0 && t.predicted_label === 0;
    const isSelected = state.selectedTransaction?.transaction_id === t.transaction_id;

    let ruleDisplay = '<span style="color:var(--text-muted);">—</span>';
    if (hasRules) {
      const firstRule = t.fired_rules.split(';')[0].trim();
      ruleDisplay = `<span class="rule-chip ${isCritical ? 'critical' : ''}">${firstRule}</span>`;
    }

    const probColor = t.fraud_probability >= 0.7 ? 'var(--danger)'
                    : t.fraud_probability >= 0.3 ? 'var(--warn)'
                    : 'var(--success)';

    return `
      <tr data-id="${t.transaction_id}"
          class="${isEvaded ? 'row-evaded' : ''} ${isSelected ? 'selected' : ''}">
        <td>
          ${t.transaction_id}
          ${isEvaded ? '<span class="evaded-tag">EVADED</span>' : ''}
        </td>
        <td style="color:var(--text-secondary);">${t.timestamp?.split(' ')[1] || t.timestamp}</td>
        <td style="color:var(--text-secondary);">${t.channel}</td>
        <td style="color:var(--text-secondary);">${t.sender_id} → ${t.receiver_id}</td>
        <td style="text-align:right; font-weight:600; color:var(--text-primary);">
          $${parseFloat(t.amount).toFixed(2)}
        </td>
        <td><span class="badge-tier ${tierClass}">${t.risk_tier}</span></td>
        <td style="font-weight:700; color:${probColor};">
          ${(t.fraud_probability * 100).toFixed(1)}%
        </td>
        <td>${ruleDisplay}</td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', () => {
      const txn = state.transactions.find(x => x.transaction_id === row.dataset.id);
      if (txn) openTransactionInspector(txn);
    });
  });
}

// ============================================================
// Transaction Inspector Modal
// ============================================================
function openTransactionInspector(txn) {
  state.selectedTransaction = txn;
  renderTableRows(); // refresh selected highlight

  const modal = document.getElementById('inspector-modal');
  modal.classList.add('open');

  setText('drawer-txn-id',         txn.transaction_id);
  setText('dna-amount',            `$${parseFloat(txn.amount).toFixed(2)}`);
  setText('dna-channel',           txn.channel);
  setText('dna-sender-age',        `${txn.sender_account_age_days} days`);
  setText('dna-receiver-age',      `${txn.receiver_account_age_days} days`);
  setText('dna-session-dwell',     `${txn.session_duration_sec}s`);
  setText('dna-time-since-payee',  `${txn.time_since_payee_added_sec}s`);
  setText('dna-velocity-1h',       `${txn.velocity_1h} txns`);
  setText('dna-amount-dev',        `${txn.amount_deviation_score} σ`);

  const callEl = document.getElementById('dna-concurrent-call');
  if (callEl) {
    callEl.textContent = txn.concurrent_call_active ? 'ACTIVE' : 'NO';
    callEl.style.color = txn.concurrent_call_active ? 'var(--danger)' : 'var(--text-primary)';
  }

  // Scoring
  setText('drawer-final-prob', `${(txn.fraud_probability * 100).toFixed(1)}%`);
  setText('drawer-ml-prob',    `${(txn.ml_probability * 100).toFixed(1)}%`);
  setText('drawer-rule-score', `${(txn.rule_score * 100).toFixed(1)}%`);

  // Rules
  const rulesEl = document.getElementById('drawer-rules-list');
  if (rulesEl) {
    if (txn.fired_rules && txn.fired_rules !== 'none') {
      rulesEl.innerHTML = txn.fired_rules.split(';').map(r => `
        <div class="rule-tag">
          <span>⚡</span> ${r.trim()}
        </div>
      `).join('');
    } else {
      rulesEl.innerHTML = `<p style="font-size:12px; color:var(--text-secondary); font-family:var(--font-mono);">No heuristic tripwires fired — normal telemetry envelope.</p>`;
    }
  }

  // Oracle
  const isFraud = txn.ground_truth_label !== 0;
  const oracleLabel = document.getElementById('oracle-actual-label');
  if (oracleLabel) {
    oracleLabel.textContent = isFraud ? 'FRAUDULENT ATTACK' : 'BENIGN / NORMAL';
    oracleLabel.style.color = isFraud ? 'var(--danger)' : 'var(--success)';
  }
  setText('oracle-attack-subtype', txn.attack_subtype   || 'none');
  setText('oracle-stealth',        txn.stealth_level !== undefined ? `${(txn.stealth_level * 100).toFixed(0)}%` : '—');
  setText('oracle-evasion-tech',   txn.evasion_technique || 'none');
}

function closeTransactionInspector() {
  document.getElementById('inspector-modal')?.classList.remove('open');
}

// ============================================================
// Retrain Studio Update
// ============================================================
function updateRetrainStudio() {
  const listEl = document.getElementById('cycle-history-list');
  if (!listEl) return;

  if (!state.retrainHistory.length) {
    listEl.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted); font-family:var(--font-mono); font-size:12px;">No cycles yet.</div>`;
    return;
  }

  listEl.innerHTML = state.retrainHistory.map(item => `
    <div class="cycle-card">
      <div class="cycle-card-left">
        <span class="cycle-num">Cycle #${item.cycle}</span>
        <span class="cycle-type">${item.type}</span>
        <span class="cycle-meta-row">
          ${item.timestamp} · ${item.samples.toLocaleString()} samples
        </span>
      </div>
      <div class="cycle-metrics">
        <div class="cycle-metric">
          <div class="val text-accent">${(item.metrics.roc_auc || 0).toFixed(3)}</div>
          <div class="lbl">ROC-AUC</div>
        </div>
        <div class="cycle-metric">
          <div class="val text-success">${(item.metrics.recall || 0).toFixed(3)}</div>
          <div class="lbl">Recall</div>
        </div>
        <div class="cycle-metric">
          <div class="val text-warn">${(item.metrics.precision || 0).toFixed(3)}</div>
          <div class="lbl">Precision</div>
        </div>
      </div>
    </div>
  `).join('');
}

// ============================================================
// Evasion Deck Update
// ============================================================
function updateEvasionDeck() {
  if (!state.tunerRecommendation) return;
  const rec = state.tunerRecommendation;
  setText('evasion-rec-stealth',   `${(rec.recommended_stealth * 100).toFixed(0)}%`);
  setText('evasion-rec-strategy',  rec.adaptation_strategy.toUpperCase().replace(/_/g, ' '));
  setText('evasion-rec-reasoning', rec.reasoning);
}

// ============================================================
// Event Listeners
// ============================================================
function setupEventListeners() {
  // Filter pills
  document.querySelectorAll('.pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeFilter = btn.dataset.filter;
      applyTableFilters();
    });
  });

  // Search
  document.getElementById('search-input')?.addEventListener('input', e => {
    state.searchQuery = e.target.value;
    applyTableFilters();
  });

  // Close inspector
  document.getElementById('close-inspector-btn')?.addEventListener('click', closeTransactionInspector);
  document.getElementById('inspector-modal')?.addEventListener('click', e => {
    if (e.target === document.getElementById('inspector-modal')) closeTransactionInspector();
  });

  // Keyboard escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeTransactionInspector();
  });

  // Red team sliders
  const stealthSlider = document.getElementById('slider-stealth');
  const countSlider   = document.getElementById('slider-count');
  const ratioSlider   = document.getElementById('slider-ratio');

  stealthSlider?.addEventListener('input', e => {
    document.getElementById('val-stealth').textContent = parseFloat(e.target.value).toFixed(2);
  });
  countSlider?.addEventListener('input', e => {
    document.getElementById('val-count').textContent = parseInt(e.target.value).toLocaleString();
  });
  ratioSlider?.addEventListener('input', e => {
    document.getElementById('val-ratio').textContent = `${(parseFloat(e.target.value) * 100).toFixed(0)}%`;
  });

  // Preset stealth chips
  document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const stealth = parseFloat(chip.dataset.stealth);
      if (stealthSlider) {
        stealthSlider.value = stealth;
        document.getElementById('val-stealth').textContent = stealth.toFixed(2);
      }
    });
  });

  // Generate batch
  const genBtn = document.getElementById('btn-generate-batch');
  genBtn?.addEventListener('click', async () => {
    genBtn.disabled = true;
    genBtn.innerHTML = '⟳ Generating attack stream…';
    try {
      await Api.generateBatch({
        total_transactions:       parseInt(countSlider?.value   || 1000),
        fraud_ratio:              parseFloat(ratioSlider?.value || 0.08),
        stealth_level:            parseFloat(stealthSlider?.value || 0.35),
        seed:                     Math.floor(Math.random() * 99999),
        voice_clone_weight:       0.40,
        ephemeral_merchant_weight:0.35,
        digital_arrest_weight:    0.25,
      });
      await refreshGlobalState();
    } catch (err) {
      alert('Generation failed: ' + err.message);
    } finally {
      genBtn.disabled = false;
      genBtn.innerHTML = '⚡ Synthesize Attack Stream';
    }
  });

  // Retrain
  const retrainBtn = document.getElementById('btn-trigger-retrain');
  retrainBtn?.addEventListener('click', async () => {
    retrainBtn.disabled = true;
    retrainBtn.innerHTML = '⟳ Ingesting evasions & retraining…';
    try {
      await Api.activeRetrain({
        adversarial_samples: 500,
        stealth_level: state.tunerRecommendation?.recommended_stealth || 0.75,
        fraud_ratio:   0.20,
      });
      await refreshGlobalState();
    } catch (err) {
      alert('Retraining failed: ' + err.message);
    } finally {
      retrainBtn.disabled = false;
      retrainBtn.innerHTML = '🛡 Execute Adversarial Retraining Cycle';
    }
  });
}

// ============================================================
// Sandbox Reactive Simulation
// ============================================================
function setupSandboxListeners() {
  const inputs = [
    'sb-amount', 'sb-session-dwell', 'sb-time-since-payee',
    'sb-amount-dev', 'sb-velocity-1h', 'sb-receiver-age',
    'sb-channel', 'sb-concurrent-call', 'sb-new-payee', 'sb-device-type',
  ];

  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      const valEl = document.getElementById(`val-${id}`);
      if (valEl) {
        if (id === 'sb-amount')     valEl.textContent = `$${parseFloat(el.value).toFixed(2)}`;
        else if (id === 'sb-amount-dev') valEl.textContent = `${parseFloat(el.value).toFixed(1)} σ`;
        else valEl.textContent = el.value;
      }
      triggerSandboxSimulation();
    });
  });
}

let sandboxTimeout = null;
function triggerSandboxSimulation() {
  clearTimeout(sandboxTimeout);
  sandboxTimeout = setTimeout(async () => {
    try {
      const data = {
        amount:                   parseFloat(document.getElementById('sb-amount')?.value || 500),
        channel:                  document.getElementById('sb-channel')?.value || 'UPI',
        sender_account_age_days:  120,
        receiver_account_age_days:parseInt(document.getElementById('sb-receiver-age')?.value || 2),
        device_type:              document.getElementById('sb-device-type')?.value || 'Android',
        session_duration_sec:     parseInt(document.getElementById('sb-session-dwell')?.value || 95),
        time_since_payee_added_sec:parseInt(document.getElementById('sb-time-since-payee')?.value || 35),
        concurrent_call_active:   document.getElementById('sb-concurrent-call')?.checked || false,
        ip_country:               'US',
        ip_change_flag:           false,
        login_to_transaction_gap_sec: 25,
        velocity_1h:              parseInt(document.getElementById('sb-velocity-1h')?.value || 0),
        velocity_24h:             3,
        amount_deviation_score:   parseFloat(document.getElementById('sb-amount-dev')?.value || 0.0),
        new_payee_flag:           document.getElementById('sb-new-payee')?.checked || true,
        receiver_id:              'MULE_SIM_999',
      };

      const res = await Api.simulateSingle(data);
      const prob = res.final_fraud_probability;

      const probColor = prob >= 0.70 ? 'var(--danger)'
                       : prob >= 0.30 ? 'var(--warn)'
                       : 'var(--success)';

      const probEl = document.getElementById('sb-prob-val');
      if (probEl) {
        probEl.textContent  = `${(prob * 100).toFixed(1)}%`;
        probEl.style.color  = probColor;
      }

      const tierBadge = document.getElementById('sb-tier-badge');
      if (tierBadge) {
        tierBadge.textContent  = `TIER: ${res.risk_tier}`;
        tierBadge.className    = `badge-tier ${res.risk_tier.toLowerCase()}`;
      }

      const critEl = document.getElementById('sb-critical-override');
      if (critEl) {
        critEl.textContent = res.is_critical_override ? '⚡ CRITICAL OVERRIDE ACTIVE' : '—';
        critEl.style.color = res.is_critical_override ? 'var(--danger)' : 'var(--text-muted)';
      }

      setText('sb-ml-prob',    `${(res.ml_probability * 100).toFixed(1)}%`);
      setText('sb-rule-score', `${(res.rule_score * 100).toFixed(1)}%`);

      Charts.drawRiskGauge('chart-sandbox-gauge', prob);

      // Tripwires
      const tripwireDefs = [
        { key: 'RULE_INSTANT_TRANSFER_NEW_PAYEE',   name: 'Instant Transfer to New Payee (<60s)' },
        { key: 'RULE_HOSTAGE_CALL_COERCION',        name: 'Hostage / Coercion Active Call' },
        { key: 'RULE_PROLONGED_SESSION_DWELL',      name: 'Abnormal Session Dwell (>1800s)' },
        { key: 'RULE_FRESH_MERCHANT_BURST',         name: 'Fresh Ephemeral Merchant (<5 days)' },
        { key: 'RULE_EXTREME_AMOUNT_DEVIATION',     name: 'Extreme Amount Deviation (>3.5σ)' },
        { key: 'RULE_VELOCITY_SURGE',               name: 'Velocity Burst Surge' },
      ];

      const listEl = document.getElementById('sb-tripwires-list');
      if (listEl) {
        listEl.innerHTML = tripwireDefs.map(rule => {
          const fired = res.fired_rules.includes(rule.key);
          return `
            <div class="tripwire-row ${fired ? 'fired' : ''}">
              <span>${rule.name}</span>
              <span class="tripwire-status">${fired ? '⚡ TRIGGERED' : '✓ SAFE'}</span>
            </div>
          `;
        }).join('');
      }

    } catch (err) {
      console.error('Sandbox simulation error:', err);
    }
  }, 100);
}
