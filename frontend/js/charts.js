/**
 * AEGIS-AI Canvas Visualization Engine
 * Reads CSS variables so charts adapt to dark/light mode automatically.
 */

// Polyfill for browsers without CanvasRenderingContext2D.roundRect
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, radii) {
    const r = Array.isArray(radii) ? radii[0] : (typeof radii === 'number' ? radii : 0);
    this.beginPath();
    this.moveTo(x + r, y);
    this.lineTo(x + w - r, y);
    this.quadraticCurveTo(x + w, y, x + w, y + r);
    this.lineTo(x + w, y + h - r);
    this.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    this.lineTo(x + r, y + h);
    this.quadraticCurveTo(x, y + h, x, y + h - r);
    this.lineTo(x, y + r);
    this.quadraticCurveTo(x, y, x + r, y);
    this.closePath();
    return this;
  };
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export const Charts = {

  // ----------------------------------------------------------------
  // Confusion Matrix (2x2 heatmap)
  // ----------------------------------------------------------------
  drawConfusionMatrix(canvasId, matrix) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!matrix) return;

    const { true_positives: tp = 0, false_positives: fp = 0,
            true_negatives: tn = 0, false_negatives: fn = 0 } = matrix;

    const pad = 28;
    const cellW = (W - pad * 2) / 2;
    const cellH = (H - pad * 2) / 2;

    const accent  = cssVar('--accent');
    const danger  = cssVar('--danger');
    const success = cssVar('--success');
    const warn    = cssVar('--warn');
    const textPri = cssVar('--text-primary');
    const textMut = cssVar('--text-muted');
    const border  = cssVar('--border-0');

    const cells = [
      { label: 'TN',         val: tn, x: pad,        y: pad,        bg: 'rgba(72,187,120,0.12)',  stroke: success },
      { label: 'FP',         val: fp, x: pad + cellW, y: pad,       bg: 'rgba(237,137,54,0.12)',  stroke: warn    },
      { label: 'FN (Evaded)',val: fn, x: pad,         y: pad+cellH, bg: 'rgba(245,101,101,0.18)', stroke: danger  },
      { label: 'TP (Caught)',val: tp, x: pad + cellW, y: pad+cellH, bg: 'rgba(99,179,237,0.18)',  stroke: accent  },
    ];

    cells.forEach(c => {
      const r = 4;
      const x = c.x + 2, y = c.y + 2, w = cellW - 4, h = cellH - 4;

      ctx.fillStyle = c.bg;
      ctx.beginPath();
      ctx.roundRect(x, y, w, h, r);
      ctx.fill();

      ctx.strokeStyle = c.stroke;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(x, y, w, h, r);
      ctx.stroke();

      ctx.fillStyle = textPri;
      ctx.font = `bold 15px ${cssVar('--font-mono') || 'monospace'}`;
      ctx.textAlign = 'center';
      ctx.fillText(c.val.toLocaleString(), c.x + cellW / 2, c.y + cellH / 2 + 2);

      ctx.fillStyle = textMut;
      ctx.font = `9px monospace`;
      ctx.fillText(c.label, c.x + cellW / 2, c.y + cellH / 2 + 16);
    });

    // Axis labels
    ctx.fillStyle = textMut;
    ctx.font = '8px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('PRED NORMAL', pad + cellW / 2, pad - 8);
    ctx.fillText('PRED FRAUD',  pad + cellW * 1.5, pad - 8);
  },

  // ----------------------------------------------------------------
  // Threat Detection Breakdown (horizontal bars)
  // ----------------------------------------------------------------
  drawThreatBreakdown(canvasId, threatBreakdown) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !threatBreakdown) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const threats = Object.keys(threatBreakdown);
    if (!threats.length) return;

    const accent  = cssVar('--accent');
    const danger  = cssVar('--danger');
    const textPri = cssVar('--text-primary');
    const textMut = cssVar('--text-muted');

    const rowH   = (H - 16) / threats.length;
    const barX   = 140;
    const maxBarW = W - barX - 50;

    threats.forEach((th, idx) => {
      const data = threatBreakdown[th];
      const det  = data.detection_rate || 0;
      const eva  = data.evasion_rate   || 0;
      const y    = 10 + idx * rowH;

      const displayName =
        th === 'voice_clone_app'    ? 'Voice Clone' :
        th === 'ephemeral_merchant' ? 'Ephemeral'   :
        th === 'digital_arrest'     ? 'Dig. Arrest' : th;

      ctx.fillStyle = textPri;
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(displayName, 6, y + 14);

      // Track
      ctx.fillStyle = cssVar('--border-0');
      ctx.beginPath();
      ctx.roundRect(barX, y + 3, maxBarW, 14, 3);
      ctx.fill();

      // Caught
      if (det > 0) {
        ctx.fillStyle = accent;
        ctx.beginPath();
        ctx.roundRect(barX, y + 3, maxBarW * det, 14, [3,0,0,3]);
        ctx.fill();
      }

      // Evaded
      if (eva > 0) {
        ctx.fillStyle = danger;
        ctx.beginPath();
        ctx.roundRect(barX + maxBarW * det, y + 3, maxBarW * eva, 14, 0);
        ctx.fill();
      }

      ctx.fillStyle = textMut;
      ctx.font = '9px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(`${(det * 100).toFixed(0)}%`, barX + maxBarW + 5, y + 14);
    });
  },

  // ----------------------------------------------------------------
  // Retrain Trajectory (ROC-AUC line chart)
  // ----------------------------------------------------------------
  drawRetrainTrajectory(canvasId, history) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!history || !history.length) return;

    const accent  = cssVar('--accent');
    const textMut = cssVar('--text-muted');
    const bg0     = cssVar('--bg-0');

    const pad = 32;
    const pW  = W - pad * 2;
    const pH  = H - pad * 2;

    // Grid
    ctx.strokeStyle = cssVar('--border-0');
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad + (pH / 4) * i;
      ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(W - pad, y); ctx.stroke();
      ctx.fillStyle = textMut;
      ctx.font = '9px monospace';
      ctx.textAlign = 'right';
      ctx.fillText((1.0 - i * 0.25).toFixed(2), pad - 6, y + 3);
    }

    if (history.length === 1) {
      const y = pad + pH * (1.0 - (history[0].metrics?.roc_auc || 0.85));
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc(W / 2, y, 6, 0, Math.PI * 2);
      ctx.fill();
      return;
    }

    const points = history.map((h, idx) => ({
      x: pad + (pW / (history.length - 1)) * idx,
      y: pad + pH * (1.0 - Math.min(1, Math.max(0, h.metrics?.roc_auc || 0.5))),
      cycle: h.cycle,
    }));

    // Gradient fill under line
    const grad = ctx.createLinearGradient(0, pad, 0, pad + pH);
    grad.addColorStop(0, 'rgba(99,179,237,0.18)');
    grad.addColorStop(1, 'rgba(99,179,237,0)');
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points.at(-1).x, pad + pH);
    ctx.lineTo(points[0].x, pad + pH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.strokeStyle = accent;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.moveTo(points[0].x, points[0].y);
    points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
    ctx.stroke();

    // Dots + labels
    points.forEach(p => {
      ctx.fillStyle = bg0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
      ctx.stroke();

      ctx.fillStyle = textMut;
      ctx.font = '9px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`C${p.cycle}`, p.x, H - 8);
    });
  },

  // ----------------------------------------------------------------
  // Risk Gauge (arc meter)
  // ----------------------------------------------------------------
  drawRiskGauge(canvasId, probability) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const cx = W / 2;
    const cy = H / 2 + 14;
    const r  = 76;

    const color =
      probability >= 0.70 ? cssVar('--danger') :
      probability >= 0.30 ? cssVar('--warn')   :
                            cssVar('--success');

    // Track
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI * 0.8, Math.PI * 2.2, false);
    ctx.strokeStyle = cssVar('--bg-3');
    ctx.lineWidth = 10;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Value arc
    const start = Math.PI * 0.8;
    const end   = start + Math.PI * 1.4 * Math.min(1, Math.max(0, probability));
    ctx.beginPath();
    ctx.arc(cx, cy, r, start, end, false);
    ctx.strokeStyle = color;
    ctx.lineWidth = 10;
    ctx.lineCap = 'round';
    ctx.shadowColor = color;
    ctx.shadowBlur = 12;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Tick marks
    for (let i = 0; i <= 10; i++) {
      const angle = Math.PI * 0.8 + (Math.PI * 1.4 * i / 10);
      const tickLen = i % 5 === 0 ? 10 : 5;
      const x1 = cx + (r - 6) * Math.cos(angle);
      const y1 = cy + (r - 6) * Math.sin(angle);
      const x2 = cx + (r - 6 - tickLen) * Math.cos(angle);
      const y2 = cy + (r - 6 - tickLen) * Math.sin(angle);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = cssVar('--border-1');
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  },
};
