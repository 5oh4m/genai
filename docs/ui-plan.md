# AEGIS-AI UI Improvement & Animation Plan

> **Purpose:** This document is the master blueprint for making the AEGIS-AI simulation HUD user-friendly, visually engaging, and informative — comparable in feel to a real payment-network fraud operations center (Mastercard, Visa, Stripe Radar). Every section includes *what* to build, *why* it matters, *where* in the codebase to implement it, and *how* to wire it up.

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Design Principles](#2-design-principles)
3. [Global UX Improvements](#3-global-ux-improvements)
4. [Animation System Architecture](#4-animation-system-architecture)
5. [Priority Animation: Attack Stream Synthesis](#5-priority-animation-attack-stream-synthesis)
6. [Workspace-by-Workspace UI Plan](#6-workspace-by-workspace-ui-plan)
7. [Component Library to Add](#7-component-library-to-add)
8. [Real-World Payment UX Parallels](#8-real-world-payment-ux-parallels)
9. [Implementation Phases](#9-implementation-phases)
10. [File-by-File Change Map](#10-file-by-file-change-map)
11. [CSS Animation Reference](#11-css-animation-reference)
12. [JavaScript Event & State Additions](#12-javascript-event--state-additions)
13. [Accessibility & Mobile](#13-accessibility--mobile)
14. [Success Metrics](#14-success-metrics)

---

## 1. Current State Assessment

### What works well today

| Area | Status |
|------|--------|
| Dark/light theme with CSS tokens | ✅ Solid foundation (`:root.light-mode`) |
| Five workspace tabs with card layout | ✅ Clear information hierarchy |
| Transaction table with filters & search | ✅ Functional triage workflow |
| Canvas charts (confusion matrix, threat bars, ROC line, gauge) | ✅ Theme-aware |
| Transaction Inspector drawer | ✅ Good drill-down pattern |
| Sandbox live scoring | ✅ Interactive what-if |

### Critical UX gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| **No visual feedback during batch generation** | User clicks "Synthesize Attack Stream" and waits with only button text change — feels broken | 🔴 P0 |
| **No stream/flow animation when data arrives** | Missed opportunity to show money moving through a network | 🔴 P0 |
| **Backend returns rich data UI ignores** | Realism report, zero-leakage proof, fraud count never shown after generate | 🔴 P0 |
| **Static Threats tab** | Dead content; no link to live data | 🟠 P1 |
| **No success/error toast system** | Only `alert()` on failure | 🟠 P1 |
| **No skeleton/shimmer loaders** | `.skeleton` CSS exists but unused | 🟠 P1 |
| **No auto-navigation after generate** | User stays on Red Team; must manually switch to Stream | 🟡 P2 |
| **600-row table limit with no pagination** | Large batches feel truncated | 🟡 P2 |
| **Realism card is static copy** | Doesn't bind to `state.realism` from API | 🟡 P2 |
| **Preset chips have no active state** | User can't see which stealth preset is selected | 🟡 P2 |
| **No onboarding / first-visit tour** | New users don't understand Red vs Blue loop | 🟡 P2 |
| **Mobile layout breaks** | Fixed 340px/380px sidebars | 🟢 P3 |

---

## 2. Design Principles

Follow these when implementing any UI change:

1. **Show the pipeline, not just the result.** Real fraud ops centers (Mastercard SOCC, Visa Cyber Intelligence) display *flow* — authorization → scoring → decision → settlement. Mirror that with animated pipelines.

2. **Animate state transitions, not decoration.** Every animation must communicate: loading, success, failure, data arrival, risk escalation, or cycle completion.

3. **Progressive disclosure.** Summary first (HUD counters animate up), detail second (table rows stream in), drill-down third (inspector drawer).

4. **Fail gracefully with context.** Replace `alert()` with inline error banners that explain *what* failed and *what to try*.

5. **Respect reduced motion.** Wrap all animations in `@media (prefers-reduced-motion: reduce)` fallbacks.

6. **Keep the monospace data aesthetic.** Inter for labels, JetBrains Mono for amounts/IDs/probabilities — this matches real SOC dashboards.

---

## 3. Global UX Improvements

### 3.1 Toast Notification System

**Add to:** `frontend/index.html` (container), `frontend/css/style.css`, `frontend/js/app.js`

```html
<!-- Add before closing </body> -->
<div id="toast-container" class="toast-container" aria-live="polite"></div>
```

**Behavior:**
- Success toasts (green left border): "✓ 1,000 transactions synthesized — 80 fraud injected"
- Error toasts (red): "✗ Generation failed — server unreachable"
- Info toasts (blue): "Switched to Stream view"
- Auto-dismiss after 5s; stack up to 3

**Function signature to add in `app.js`:**
```javascript
function showToast(message, type = 'info', duration = 5000) { ... }
```

---

### 3.2 Global Loading Overlay

**When to show:** Any API call taking >300ms (generate, retrain, initial page load).

**Structure:**
```html
<div id="global-loader" class="global-loader" hidden>
  <div class="loader-ring"></div>
  <span id="loader-message">Initializing simulation engine…</span>
</div>
```

**Messages by action:**
| Action | Loader message |
|--------|---------------|
| Page init | "Bootstrapping Blue Team pipeline…" |
| Generate | "Red Team synthesizing adversarial stream…" |
| Retrain | "Blue Team ingesting evasions & retraining…" |
| Sandbox | *(skip — use inline gauge pulse instead)* |

---

### 3.3 Animated HUD Counters

**Current:** `#hud-total-txns`, `#hud-fraud-detected`, `#hud-roc-auc`, `#hud-active-cycle` update instantly.

**Improvement:** Count-up animation over 800ms when values change.

```javascript
function animateCounter(el, from, to, formatter = (v) => v) {
  const start = performance.now();
  const duration = 800;
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
    el.textContent = formatter(from + (to - from) * eased);
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
```

Apply after every `refreshGlobalState()`.

---

### 3.4 First-Visit Onboarding Overlay

**Trigger:** `localStorage.getItem('aegis-onboarded')` is null.

**3-step spotlight tour:**
1. "This is your Live Transaction Stream — real-time triage like a payment network SOC."
2. "Red Team generates adversarial attacks. Blue Team retrains to catch them."
3. "Use Sandbox to test a single transaction before it hits the network."

Dismiss → set `aegis-onboarded = true`.

---

### 3.5 Breadcrumb / Action Trail

Add a slim bar below the nav showing the last major action:

```
Last action: Synthesized 1,000 txns (stealth 0.35) → 73 fraud detected → 12 evaded
```

Store in `state.lastAction` and render in a new `#action-trail` element.

---

## 4. Animation System Architecture

### 4.1 Animation Layers

```
Layer 0 — CSS transitions (hover, theme, tab switch)     ← already exists
Layer 1 — CSS keyframe animations (pulse, shimmer, fade) ← partially exists
Layer 2 — JS-driven DOM animations (counters, toasts)    ← to add
Layer 3 — Canvas animations (chart draw, stream flow)    ← to extend charts.js
Layer 4 — SVG pipeline animations (payment flow viz)     ← new component
```

### 4.2 Shared Animation Tokens (add to `:root` in style.css)

```css
:root {
  --anim-fast:   150ms;
  --anim-normal: 300ms;
  --anim-slow:   600ms;
  --anim-stream: 1200ms;
  --ease-out:    cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### 4.3 Reduced Motion Fallback

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 5. Priority Animation: Attack Stream Synthesis

> **This is the #1 user-requested animation.** When the user clicks **"⚡ Synthesize Attack Stream"** (`#btn-generate-batch`), the UI must show a visible pipeline of money/transactions flowing from Red Team generation through Blue Team scoring into the Stream table.

### 5.1 User Flow (Target Experience)

```
[Click button]
    ↓
[Button enters "generating" state — pulse + disabled]
    ↓
[Stream Pipeline Panel slides open below the button]
    ↓
[Phase 1: "Synthesizing baseline population…"     — progress 0→30%]
[Phase 2: "Injecting adversarial attacks…"         — progress 30→60%]
[Phase 3: "Computing velocity & deviation…"        — progress 60→75%]
[Phase 4: "Blue Team scoring batch…"               — progress 75→95%]
[Phase 5: "Zero-leakage validation…"               — progress 95→100%]
    ↓
[Progress bar completes — flash green]
    ↓
[Animated particle stream flows left-to-right across pipeline SVG]
    ↓
[Toast: "✓ 1,000 transactions synthesized — 80 fraud / 920 normal"]
    ↓
[HUD counters animate up]
    ↓
[Auto-switch to Stream tab (optional, with 1.5s delay)]
    ↓
[Table rows fade in sequentially (stagger 20ms each, max 50 rows animated)]
    ↓
[Pipeline panel collapses after 3s]
```

### 5.2 HTML Structure to Add (Red Team workspace)

Insert below `#btn-generate-batch` in `frontend/index.html`:

```html
<!-- Attack Stream Pipeline (hidden by default) -->
<div id="attack-stream-panel" class="attack-stream-panel" hidden>
  <div class="asp-header">
    <span class="asp-title">⚡ Attack Stream Pipeline</span>
    <span id="asp-phase-label" class="asp-phase">Initializing…</span>
  </div>

  <!-- Progress bar -->
  <div class="asp-progress-track">
    <div id="asp-progress-fill" class="asp-progress-fill"></div>
  </div>
  <div class="asp-progress-meta">
    <span id="asp-progress-pct">0%</span>
    <span id="asp-progress-count">0 / 0 transactions</span>
  </div>

  <!-- SVG pipeline visualization -->
  <svg id="asp-pipeline-svg" class="asp-pipeline-svg" viewBox="0 0 800 80" preserveAspectRatio="xMidYMid meet">
    <!-- Stage nodes -->
    <g class="asp-stage" data-stage="generate">
      <rect x="10" y="20" width="120" height="40" rx="6" class="asp-node"/>
      <text x="70" y="45" class="asp-node-label">Red Team</text>
    </g>
    <g class="asp-stage" data-stage="score">
      <rect x="340" y="20" width="120" height="40" rx="6" class="asp-node"/>
      <text x="400" y="45" class="asp-node-label">Blue Team</text>
    </g>
    <g class="asp-stage" data-stage="stream">
      <rect x="670" y="20" width="120" height="40" rx="6" class="asp-node"/>
      <text x="730" y="45" class="asp-node-label">Stream</text>
    </g>
    <!-- Connecting pipes -->
    <line x1="130" y1="40" x2="340" y2="40" class="asp-pipe"/>
    <line x1="460" y1="40" x2="670" y2="40" class="asp-pipe"/>
    <!-- Animated particles (added by JS) -->
    <g id="asp-particles"></g>
  </svg>

  <!-- Live stats during generation -->
  <div class="asp-stats">
    <div class="asp-stat"><span class="asp-stat-val" id="asp-stat-normal">—</span><span class="asp-stat-lbl">Normal</span></div>
    <div class="asp-stat"><span class="asp-stat-val danger" id="asp-stat-fraud">—</span><span class="asp-stat-lbl">Fraud Injected</span></div>
    <div class="asp-stat"><span class="asp-stat-val" id="asp-stat-stealth">—</span><span class="asp-stat-lbl">Stealth</span></div>
    <div class="asp-stat"><span class="asp-stat-val success" id="asp-stat-leakage">—</span><span class="asp-stat-lbl">Zero Leakage</span></div>
  </div>
</div>
```

### 5.3 CSS for Stream Pipeline (add to style.css)

```css
.attack-stream-panel {
  margin-top: 16px;
  background: var(--bg-2);
  border: 1px solid var(--border-accent);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  animation: fadeInUp var(--anim-normal) var(--ease-out);
  overflow: hidden;
}

.asp-progress-track {
  height: 6px;
  background: var(--bg-3);
  border-radius: 99px;
  margin: 12px 0 6px;
  overflow: hidden;
}

.asp-progress-fill {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--accent), var(--purple));
  border-radius: 99px;
  transition: width 0.4s var(--ease-out);
}

.asp-progress-fill.complete {
  background: linear-gradient(90deg, var(--success), var(--accent));
  box-shadow: 0 0 12px var(--success-glow);
}

/* SVG pipeline */
.asp-pipeline-svg { width: 100%; height: 80px; margin: 12px 0; }
.asp-node { fill: var(--bg-3); stroke: var(--border-1); stroke-width: 1; transition: all var(--anim-normal); }
.asp-node.active { stroke: var(--accent); fill: var(--accent-subtle); filter: drop-shadow(0 0 6px var(--accent-glow)); }
.asp-node.complete { stroke: var(--success); fill: rgba(72,187,120,0.08); }
.asp-node-label { fill: var(--text-secondary); font-family: var(--font-mono); font-size: 10px; text-anchor: middle; }
.asp-pipe { stroke: var(--border-1); stroke-width: 2; stroke-dasharray: 6 4; }
.asp-pipe.flowing { stroke: var(--accent); animation: pipeFlow 1s linear infinite; }

@keyframes pipeFlow {
  to { stroke-dashoffset: -20; }
}

/* Particle dots flowing through pipeline */
.asp-particle {
  fill: var(--accent);
  animation: particleMove var(--anim-stream) linear forwards;
}
.asp-particle.fraud { fill: var(--danger); }
```

### 5.4 JavaScript Logic (modify app.js generate handler)

Replace the current `#btn-generate-batch` click handler with a phased animation controller:

```javascript
const STREAM_PHASES = [
  { label: 'Synthesizing baseline population…',  progress: 30, stage: 'generate' },
  { label: 'Injecting adversarial attacks…',    progress: 60, stage: 'generate' },
  { label: 'Computing velocity & deviation…',   progress: 75, stage: 'generate' },
  { label: 'Blue Team scoring batch…',          progress: 95, stage: 'score'    },
  { label: 'Zero-leakage validation…',          progress: 100, stage: 'stream'   },
];

async function runAttackStreamAnimation(config) {
  const panel = document.getElementById('attack-stream-panel');
  panel.hidden = false;

  // Start simulated phase progression while API runs in parallel
  const apiPromise = Api.generateBatch(config);

  // Run phases on a timer (min 2s total for visual impact even if API is fast)
  const phasePromise = animatePhases(STREAM_PHASES, 400); // 400ms per phase

  const [result] = await Promise.all([apiPromise, phasePromise]);

  // Populate real stats from API response
  document.getElementById('asp-stat-normal').textContent = result.generated_count - result.fraud_count;
  document.getElementById('asp-stat-fraud').textContent = result.fraud_count;
  document.getElementById('asp-stat-stealth').textContent = result.stealth_level.toFixed(2);
  document.getElementById('asp-stat-leakage').textContent = result.zero_leakage ? '✓ PASS' : '✗ FAIL';

  // Launch particle stream animation
  launchParticleStream(result.fraud_count, result.generated_count);

  // Mark complete
  document.getElementById('asp-progress-fill').classList.add('complete');
  showToast(`✓ ${result.generated_count.toLocaleString()} transactions synthesized — ${result.fraud_count} fraud injected`, 'success');

  await refreshGlobalState();
  animateTableRowEntry(); // stagger fade-in on stream table

  // Auto-navigate to Stream after 1.5s
  setTimeout(() => switchTab('stream'), 1500);

  // Collapse panel after 4s
  setTimeout(() => { panel.hidden = true; resetStreamPanel(); }, 4000);

  return result;
}

function animatePhases(phases, msPerPhase) {
  return new Promise(resolve => {
    let i = 0;
    const tick = () => {
      if (i >= phases.length) { resolve(); return; }
      const p = phases[i];
      document.getElementById('asp-phase-label').textContent = p.label;
      document.getElementById('asp-progress-fill').style.width = p.progress + '%';
      document.getElementById('asp-progress-pct').textContent = p.progress + '%';
      highlightPipelineStage(p.stage);
      i++;
      setTimeout(tick, msPerPhase);
    };
    tick();
  });
}

function launchParticleStream(fraudCount, totalCount) {
  const container = document.getElementById('asp-particles');
  container.innerHTML = '';
  const particleCount = Math.min(30, Math.ceil(totalCount / 50));
  const fraudRatio = fraudCount / totalCount;

  for (let i = 0; i < particleCount; i++) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('r', '3');
    circle.setAttribute('cy', '40');
    circle.setAttribute('cx', '10');
    if (Math.random() < fraudRatio) circle.classList.add('fraud');
    circle.style.animationDelay = (i * 80) + 'ms';
    container.appendChild(circle);
    // Animate cx from 10 → 790 via CSS or requestAnimationFrame
  }
}
```

### 5.5 Backend Enhancement (Optional but Recommended)

Modify `POST /api/red-team/generate` in `backend/app.py` to support **Server-Sent Events (SSE)** for true progress streaming:

```
GET /api/red-team/generate/stream?total_transactions=1000&...
```

Events:
```
event: phase  data: {"step":"baseline","progress":10,"count":850}
event: phase  data: {"step":"attacks","progress":40,"count":80}
event: phase  data: {"step":"scoring","progress":80}
event: done   data: {"generated_count":1000,"fraud_count":80,...}
```

This replaces simulated phases with real backend progress. Implement in Phase 3.

---

## 6. Workspace-by-Workspace UI Plan

### 6.1 Stream Workspace (`#workspace-stream`)

| Improvement | Description | Animation |
|-------------|-------------|-----------|
| **Live ticker bar** | Thin scrolling marquee above table showing last 5 high-risk txn IDs | CSS `translateX` infinite scroll |
| **Row entry animation** | New rows fade+slide in from top | `@keyframes rowSlideIn` stagger |
| **Risk pulse on HIGH rows** | Subtle red glow on rows with `risk_tier === 'HIGH'` | `box-shadow` pulse 2s infinite |
| **Evaded row shake** | When filter shows evaded, rows briefly shake on appear | `@keyframes evadedShake` |
| **Empty state illustration** | Replace text-only empty with SVG + "Generate your first attack stream" CTA button linking to Red Team | Static SVG |
| **Pagination** | Show "Showing 600 of 12,400 — Load more" with lazy fetch | Button loading spinner |
| **Column sorting** | Click headers to sort by amount, probability, timestamp | Arrow indicator rotate |
| **Export CSV button** | Download filtered view | Button with download icon animation |
| **Real-time clock** | Show "Last updated: 2s ago" in filter bar | Updates every second |

**Table row stagger animation CSS:**
```css
@keyframes rowSlideIn {
  from { opacity: 0; transform: translateY(-8px); background: var(--accent-subtle); }
  to   { opacity: 1; transform: translateY(0); }
}
.tactical-table tbody tr.row-new td {
  animation: rowSlideIn 0.3s var(--ease-out) both;
}
```

---

### 6.2 Red Team Workspace (`#workspace-red-team`)

| Improvement | Description | Animation |
|-------------|-------------|-----------|
| **Attack Stream Pipeline** | See Section 5 above | Full pipeline animation |
| **Slider value preview** | Show mini preview card below sliders explaining what stealth X means | Fade in on slider change |
| **Preset chip active state** | Highlight selected chip with accent border + scale | `transform: scale(1.05)` |
| **Threat weight donut** | Visual breakdown of 40/35/25 voice/ephemeral/arrest split | Canvas donut chart |
| **Bind realism card to live data** | Wire "ZERO LEAKAGE" and "LOG-NORMAL FIT" to `state.realism` | Values flash green/red on update |
| **Evasion intel typing effect** | Reasoning text types out character-by-character | JS typewriter 30ms/char |
| **Before/after comparison** | After generate, show recall before vs after in evasion deck | Counter animation |

**Preset chip active CSS:**
```css
.preset-chip.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
  transform: scale(1.05);
  font-weight: 700;
}
```

---

### 6.3 Blue Team Workspace (`#workspace-retrain`)

| Improvement | Description | Animation |
|-------------|-------------|-----------|
| **Retrain progress pipeline** | Similar to attack stream — show train → evaluate → deploy phases | Progress bar + SVG |
| **ROC chart draw animation** | Line draws left-to-right on chart render | Canvas path animation in charts.js |
| **Cycle card entrance** | New cycle cards slide in from right | `@keyframes slideInRight` (exists) |
| **Model version badge** | Show "Model v3 — Random Forest 150 trees" | Static badge |
| **Feature importance bars** | After retrain, show top 10 features as horizontal bars | New canvas chart |
| **Defense strength meter** | Overall gauge: "Defense Posture: 73%" based on recall | Arc gauge like sandbox |
| **Retrain button confirmation** | Two-step: click → confirm dialog → execute | Modal with animation |

**Retrain animation phases:**
```
Phase 1: "Collecting adversarial evasions…"        0→25%
Phase 2: "Retraining Random Forest ensemble…"      25→60%
Phase 3: "Evaluating on holdout batch…"            60→85%
Phase 4: "Deploying updated model…"                85→100%
```

---

### 6.4 Threats Workspace (`#workspace-threats`)

| Improvement | Description | Animation |
|-------------|-------------|-----------|
| **Live detection rates** | Pull from `state.metrics.threat_breakdown` per card | Bar fills on tab enter |
| **"View in Stream" link** | Filter stream to that attack subtype | Tab switch + filter apply |
| **Expandable evasion details** | Click evasion item → accordion expand | `max-height` transition |
| **Real-world case study panel** | Add "Real World Parallel" section per threat (see team-improvement.md) | Accordion |
| **Attack timeline visualization** | Show how attack unfolds over time (call → add payee → transfer) | SVG step diagram |
| **Card hover tilt** | Subtle 3D tilt on mouse move | CSS `transform: perspective` |

**Voice Clone timeline SVG (example):**
```
[📞 Call starts] → [👤 Add payee] → [⏱ Wait 8-55s] → [💸 Transfer] → [📱 Call ends]
     concurrent_call=true              new_payee=true       amount deviation
```

---

### 6.5 Sandbox Workspace (`#workspace-sandbox`)

| Improvement | Description | Animation |
|-------------|-------------|-----------|
| **Gauge needle sweep** | On score change, arc animates from old to new value | Canvas arc interpolation |
| **Tripwire fire flash** | When rule fires, row flashes red then settles | `@keyframes tripwireFlash` |
| **Risk tier badge transition** | Badge morphs between LOW/MEDIUM/HIGH with color crossfade | CSS transition |
| **"Compare to average" overlay** | Show how this txn compares to population mean | Small sparkline |
| **Preset scenarios dropdown** | "Voice Clone Attack", "Normal Grocery", "Digital Arrest" — pre-fill all fields | Select + animate fields |
| **Score history mini-chart** | Track last 10 sandbox runs as dots on a line | Canvas |

**Gauge animation in charts.js:**
```javascript
// Store last probability; interpolate over 400ms on each drawRiskGauge call
let lastGaugeProb = 0;
drawRiskGauge(canvasId, probability) {
  const startProb = lastGaugeProb;
  const startTime = performance.now();
  const animate = (now) => {
    const t = Math.min((now - startTime) / 400, 1);
    const current = startProb + (probability - startProb) * t;
    // ... draw arc at `current`
    if (t < 1) requestAnimationFrame(animate);
    else lastGaugeProb = probability;
  };
  requestAnimationFrame(animate);
}
```

---

## 7. Component Library to Add

Build these as reusable modules:

| Component | File | Used In |
|-----------|------|---------|
| `Toast` | `frontend/js/components/toast.js` | Global |
| `ProgressPipeline` | `frontend/js/components/progress-pipeline.js` | Red Team, Blue Team |
| `AnimatedCounter` | `frontend/js/components/counter.js` | HUD, metric boxes |
| `ParticleStream` | `frontend/js/components/particle-stream.js` | Red Team pipeline SVG |
| `SkeletonLoader` | CSS class `.skeleton` (exists) + JS helper | Table, charts, cards |
| `ConfirmDialog` | `frontend/js/components/dialog.js` | Retrain, Generate |
| `TypewriterText` | `frontend/js/components/typewriter.js` | Evasion reasoning |
| `OnboardingTour` | `frontend/js/components/onboarding.js` | First visit |

---

## 8. Real-World Payment UX Parallels

Map each UI element to its real-world equivalent so the simulation *feels* authentic:

| AEGIS-AI Element | Real-World Equivalent (Mastercard / Visa / Banks) |
|------------------|------------------------------------------------|
| Stream table | **Authorization queue** — real-time txn feed from card network switch |
| Risk tier badges (LOW/MED/HIGH) | **Decision Intelligence score bands** — approve / step-up / decline |
| Confusion matrix | **Model performance dashboard** — fraud ops weekly review |
| Transaction Inspector | **Case management drill-down** — analyst investigation view |
| Red Team generate | **Adversarial red team exercise** — internal penetration testing |
| Blue Team retrain | **Model refresh cycle** — quarterly retrain on new fraud patterns |
| Sandbox | **What-if analysis tool** — pre-deployment rule testing (like FICO TRIAD sandbox) |
| HUD counters | **Network-level KPIs** — txn volume, fraud rate, model AUC |
| Zero-leakage card | **Data governance check** — PCI-DSS scope separation |
| Tripwire rules | **Business rules engine** — Experian PowerCurve / FICO Blaze Advisor |
| Concurrent call flag | **Behavioral biometric signal** — phone call during banking session |
| Velocity columns | **Velocity rules** — "N transactions in M minutes" (standard in every issuer) |

**Suggested branding copy updates:**
- Stream tab subtitle: *"Authorization Monitor — Real-Time Triage"*
- Red Team subtitle: *"Adversarial Transaction Factory"*
- Blue Team subtitle: *"Model Retraining & Defense Posture"*
- Sandbox subtitle: *"Pre-Authorization What-If Analysis"*

---

## 9. Implementation Phases

### Phase 1 — Foundation (Week 1)
**Goal:** User never feels lost or stuck waiting.

- [ ] Toast notification system
- [ ] Global loading overlay
- [ ] Animated HUD counters
- [ ] Attack Stream Pipeline panel (Section 5) with simulated phases
- [ ] Bind realism card to `state.realism`
- [ ] Replace `alert()` with toasts
- [ ] Preset chip active state

**Files touched:** `index.html`, `style.css`, `app.js`

---

### Phase 2 — Stream & Feedback (Week 2)
**Goal:** Data arrival feels alive.

- [ ] Table row stagger animation on refresh
- [ ] Auto-navigate to Stream after generate
- [ ] Retrain progress pipeline (mirror of attack stream)
- [ ] ROC chart draw animation
- [ ] Gauge needle sweep in sandbox
- [ ] Tripwire fire flash
- [ ] Action trail bar
- [ ] Empty state with CTA

**Files touched:** `index.html`, `style.css`, `app.js`, `charts.js`

---

### Phase 3 — Depth & Intelligence (Week 3)
**Goal:** Every tab feels connected to live data.

- [ ] Threats tab live detection rates + "View in Stream"
- [ ] Attack timeline SVGs per threat card
- [ ] Feature importance chart after retrain
- [ ] Defense posture gauge
- [ ] Sandbox preset scenarios
- [ ] Pagination / load more for table
- [ ] SSE backend progress streaming (optional)

**Files touched:** All frontend + `backend/app.py`

---

### Phase 4 — Polish & Accessibility (Week 4)
**Goal:** Production-quality feel.

- [ ] Onboarding tour
- [ ] Reduced motion support
- [ ] ARIA labels on tabs, drawer, toasts
- [ ] Focus trap in inspector drawer
- [ ] Mobile responsive breakpoints
- [ ] Export CSV
- [ ] Column sorting
- [ ] Card hover effects on Threats

**Files touched:** All frontend

---

## 10. File-by-File Change Map

| File | Changes |
|------|---------|
| `frontend/index.html` | Add toast container, global loader, attack stream panel, retrain pipeline panel, action trail, onboarding overlay, threat timeline SVGs, sandbox presets dropdown |
| `frontend/css/style.css` | Animation tokens, toast styles, pipeline panel, progress bars, row animations, preset active, tripwire flash, skeleton usage, responsive breakpoints, reduced motion |
| `frontend/js/app.js` | Toast fn, counter animation, stream pipeline controller, retrain pipeline, tab auto-switch, table stagger, action trail, onboarding, preset chip state, realism binding |
| `frontend/js/charts.js` | Gauge interpolation, ROC draw animation, feature importance chart, threat donut, chart draw-on-enter observer |
| `frontend/js/api.js` | Optional SSE stream endpoint, export helper |
| `frontend/js/components/*.js` | New component modules (Phase 1+) |
| `backend/app.py` | Optional SSE progress endpoint, return richer generate response (already partially there) |

---

## 11. CSS Animation Reference

### Existing animations (use these, don't recreate)

| Class/Keyframe | Location | Currently Used |
|----------------|----------|----------------|
| `fadeInUp` | style.css | Workspace panel enter |
| `pulseDot` | style.css | LIVE badge |
| `glowPulse` | style.css | Brand hex |
| `slideInRight` | style.css | Inspector drawer |
| `shimmer` | style.css | `.skeleton` — **activate this** |
| `scanline` | style.css | **unused — use for Stream ticker** |

### New animations to add

| Keyframe | Purpose | Duration |
|----------|---------|----------|
| `rowSlideIn` | Table row entry | 300ms |
| `pipeFlow` | Pipeline pipe dashes | 1s loop |
| `tripwireFlash` | Sandbox rule fire | 600ms once |
| `counterPop` | HUD number change | 200ms |
| `toastSlideIn` | Toast enter from right | 300ms |
| `toastFadeOut` | Toast dismiss | 200ms |
| `gaugeNeedle` | Sandbox gauge sweep | 400ms |
| `evadedShake` | Evaded row attention | 500ms once |
| `phaseComplete` | Pipeline stage flash | 400ms once |
| `typewriterBlink` | Cursor blink in typewriter | 1s loop |

---

## 12. JavaScript Event & State Additions

### New state properties (add to `state` object in app.js)

```javascript
const state = {
  // ... existing ...
  isGenerating: false,
  isRetraining: false,
  lastAction: null,          // { type, timestamp, summary }
  lastGenerateResult: null,  // API response from generate
  activePresetStealth: 0.35, // track selected preset chip
  sandboxHistory: [],        // last 10 sandbox scores
  onboarded: false,
};
```

### New event flows

| Event | Handler | Animation triggered |
|-------|---------|-------------------|
| `#btn-generate-batch` click | `runAttackStreamAnimation()` | Full pipeline (Section 5) |
| `#btn-trigger-retrain` click | `runRetrainAnimation()` | Retrain pipeline |
| Tab switch to `threats` | `onThreatsTabEnter()` | Detection rate bars fill |
| Tab switch to `stream` | `onStreamTabEnter()` | Charts redraw with animation |
| Sandbox input change | existing debounce + `pulseGauge()` | Gauge sweep |
| `refreshGlobalState()` complete | `animateHUDCounters()` | Counter count-up |
| First visit | `showOnboarding()` | Spotlight tour |

---

## 13. Accessibility & Mobile

### Accessibility checklist

- [ ] All buttons have `aria-label` where icon-only
- [ ] Toast container has `aria-live="polite"`
- [ ] Tab nav uses `role="tablist"`, tabs use `role="tab"`, panels use `role="tabpanel"`
- [ ] Inspector drawer traps focus and returns focus on close
- [ ] Progress bars have `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- [ ] Color is never the only indicator (pair with text/icons)
- [ ] All animations respect `prefers-reduced-motion`

### Mobile breakpoints to add

```css
@media (max-width: 1024px) {
  .stream-layout,
  .arena-layout,
  .retrain-layout,
  .sandbox-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  .nav-tabs { overflow-x: auto; }
  .hud-stat { display: none; } /* show only on wider screens */
  .hud-stat:first-of-type { display: flex; } /* keep txn count */
}
```

---

## 14. Success Metrics

Track these to know the UI improvements are working:

| Metric | How to measure | Target |
|--------|---------------|--------|
| Time to first interaction | From page load to first button click | < 5s |
| Generate completion awareness | User navigates to Stream within 10s of generate | > 80% |
| Sandbox engagement | Avg sandbox simulations per session | > 3 |
| Error recovery | User retries after error toast | > 50% |
| Session duration | Time on site per visit | > 5 min |
| Full cycle completion | User runs generate → retrain → check stream | > 30% of sessions |

---

## Quick-Start: Implement the #1 Priority Today

If you only implement one thing, do **Section 5 — Attack Stream Pipeline**:

1. Add the HTML block below `#btn-generate-batch` in `index.html`
2. Add the CSS from Section 5.3 to `style.css`
3. Replace the generate click handler in `app.js` with `runAttackStreamAnimation()`
4. Test: click "Synthesize Attack Stream" → see progress bar + pipeline + toast → auto-switch to Stream

This single feature transforms the app from "static form" to "living simulation engine."

---

*Last updated: 2026-08-23 | AEGIS-AI UI Plan v1.0*
