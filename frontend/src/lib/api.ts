export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/ws/stream";

export async function fetchHealth() {
  const res = await fetch(`${API_URL}/api/health`);
  return res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_URL}/api/metrics/overview`);
  return res.json();
}

export async function fetchDefenseStatus() {
  const res = await fetch(`${API_URL}/api/defense/status`);
  return res.json();
}

export async function runAttack(config: any) {
  const res = await fetch(`${API_URL}/api/attack/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  return res.json();
}

export async function runBatchAttack(config: any) {
  const res = await fetch(`${API_URL}/api/attack/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  return res.json();
}

export async function hardenDefense() {
  const res = await fetch(`${API_URL}/api/defense/harden`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ auto: true }),
  });
  return res.json();
}

export async function runSandbox(target: str, message: str) {
  const res = await fetch(`${API_URL}/api/sandbox/prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target, message }),
  });
  return res.json();
}
