"use client";

import { useEffect, useState } from "react";
import { fetchDefenseStatus, hardenDefense } from "@/lib/api";

export default function DefensePage() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [hardenResult, setHardenResult] = useState<any>(null);

  useEffect(() => {
    fetchDefenseStatus().then(setStatus).catch(console.error);
  }, []);

  const handleHarden = async () => {
    setLoading(true);
    try {
      const res = await hardenDefense();
      setHardenResult(res);
      const newStatus = await fetchDefenseStatus();
      setStatus(newStatus);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workspace-panel active">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Blue Team Command Center</h1>
        <button 
          className="btn btn-primary" 
          onClick={handleHarden} 
          disabled={loading || !status?.feedback_logged}
        >
          {loading ? "Analyzing..." : "Trigger Auto-Harden Cycle"}
        </button>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <span className="metric-label">Guard Rules Active</span>
          <span className="metric-val">{status?.guard_rules?.total || 0}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">LLM Judge</span>
          <span className={`metric-val ${status?.judge_active ? 'success' : 'danger'}`}>
            {status?.judge_active ? "ONLINE" : "OFFLINE"}
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Hardening Rounds</span>
          <span className="metric-val">{status?.hardening_rounds || 0}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Pending Feedback</span>
          <span className="metric-val warn">{status?.feedback_logged || 0}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '20px' }}>
        <div className="card" style={{ flex: 1 }}>
          <div className="card-title">Current Guard Rules (L1 Defense)</div>
          <div style={{ backgroundColor: 'var(--bg-color)', padding: '15px', borderRadius: '6px', fontSize: '0.85rem', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)' }}>
            {status?.guard_rules ? JSON.stringify(status.guard_rules, null, 2) : "Loading rules..."}
          </div>
        </div>
        
        <div className="card" style={{ flex: 1 }}>
          <div className="card-title">Hardening Activity</div>
          {hardenResult ? (
            <div style={{ fontSize: '0.85rem' }}>
              <div style={{ padding: '10px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--success-color)', borderRadius: '6px', marginBottom: '15px' }}>
                <strong style={{ color: 'var(--success-color)' }}>Defense Round {hardenResult.round} Complete</strong>
              </div>
              
              <h4 style={{ marginBottom: '8px' }}>Analysis:</h4>
              <ul style={{ marginBottom: '15px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
                <li>Evaluated {hardenResult.analysis.total_logged} attempts</li>
                <li>Identified weaknesses in: {Object.keys(hardenResult.analysis.by_category || {}).join(', ')}</li>
              </ul>

              <h4 style={{ marginBottom: '8px' }}>Actions Applied:</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {hardenResult.actions_applied.map((action: any, i: number) => (
                  <div key={i} style={{ padding: '10px', backgroundColor: 'var(--bg-color)', borderRadius: '6px', borderLeft: '3px solid var(--accent-color)' }}>
                    <strong>{action.action_type.toUpperCase()}</strong>: {action.description}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Run attacks to generate feedback, then trigger a hardening cycle to auto-amend rules or prompts based on weaknesses.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
