/**
 * AEGIS-AI Client API Layer
 * Handles async communication with the FastAPI backend.
 */

const API_BASE = window.location.origin;

export const Api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getState() {
    const res = await fetch(`${API_BASE}/api/state`);
    if (!res.ok) throw new Error('Failed to fetch system state');
    return res.json();
  },

  async generateBatch(params) {
    const res = await fetch(`${API_BASE}/api/red-team/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Generation failed');
    return res.json();
  },

  async trainPipeline() {
    const res = await fetch(`${API_BASE}/api/blue-team/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Training failed');
    return res.json();
  },

  async activeRetrain(params) {
    const res = await fetch(`${API_BASE}/api/blue-team/retrain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Active retraining failed');
    return res.json();
  },

  async simulateSingle(transactionData) {
    const res = await fetch(`${API_BASE}/api/sandbox/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(transactionData),
    });
    if (!res.ok) throw new Error('Single simulation failed');
    return res.json();
  },
};
