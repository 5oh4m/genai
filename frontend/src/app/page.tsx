"use client";

import { useEffect, useState } from "react";
import { WS_URL, fetchMetrics } from "@/lib/api";

export default function StreamPage() {
  const [attempts, setAttempts] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [wsStatus, setWsStatus] = useState("Connecting...");

  useEffect(() => {
    // Initial load of metrics
    fetchMetrics().then(setMetrics).catch(console.error);

    // WebSocket connection
    let ws: WebSocket;
    let pingInterval: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        setWsStatus("Connected (Live)");
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "attack_result") {
          setAttempts(prev => [msg.data, ...prev].slice(0, 50));
          // Refresh metrics on new attack
          fetchMetrics().then(setMetrics).catch(console.error);
        } else if (msg.type === "defense_hardened") {
          // Could add a toast notification here
          console.log("Defense hardened!", msg.data);
        }
      };

      ws.onclose = () => {
        setWsStatus("Disconnected (Retrying...)");
        clearInterval(pingInterval);
        setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (pingInterval) clearInterval(pingInterval);
    };
  }, []);

  return (
    <div className="workspace-panel active">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Live Simulation Stream</h1>
        <div style={{ fontSize: '0.85rem', color: wsStatus.includes('Live') ? 'var(--success-color)' : 'var(--warning-color)' }}>
          {wsStatus}
        </div>
      </div>

      {metrics && (
        <div className="metric-grid">
          <div className="metric-card">
            <span className="metric-label">Total Attacks</span>
            <span className="metric-val">{metrics.total_attempts}</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">Defense Block Rate</span>
            <span className={`metric-val ${metrics.block_rate < 0.5 ? 'danger' : 'success'}`}>
              {(metrics.block_rate * 100).toFixed(1)}%
            </span>
          </div>
          <div className="metric-card">
            <span className="metric-label">Successful Breaches</span>
            <span className={`metric-val ${metrics.successful_attacks > 0 ? 'danger' : ''}`}>
              {metrics.successful_attacks}
            </span>
          </div>
        </div>
      )}

      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div className="card-title">Real-Time Event Stream</div>
        
        {attempts.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            No recent attacks. Go to Red Team to launch an attack.
          </div>
        ) : (
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {attempts.map(attempt => (
              <div key={attempt.id} style={{ 
                padding: '12px', 
                backgroundColor: 'var(--bg-color)', 
                borderRadius: '6px',
                borderLeft: `4px solid ${attempt.success ? 'var(--danger-color)' : 'var(--success-color)'}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <strong>{attempt.objective_category}</strong> vs <strong>{attempt.target_name}</strong>
                  <span className={`verdict-badge ${attempt.success ? 'verdict-block' : 'verdict-allow'}`} style={{
                    backgroundColor: attempt.success ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                    color: attempt.success ? 'var(--danger-color)' : 'var(--success-color)',
                    border: 'none'
                  }}>
                    {attempt.success ? 'BREACHED' : 'DEFENDED'}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Strategy: {attempt.strategy} | Converter: {attempt.converter_used}
                </div>
                <div style={{ fontSize: '0.85rem', padding: '8px', backgroundColor: 'var(--panel-bg)', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                  <strong>Blue Team Verdict:</strong> {attempt.blue_team_verdict.toUpperCase()}<br/>
                  <span style={{ color: 'var(--text-muted)' }}>{attempt.blue_team_reasoning}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
