"use client";

import { useEffect, useState } from "react";
import { fetchMetrics } from "@/lib/api";

export default function ThreatsPage() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetchMetrics().then(setMetrics).catch(console.error);
  }, []);

  if (!metrics) return <div className="workspace-panel active">Loading threat intel...</div>;

  return (
    <div className="workspace-panel active">
      <h1 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '20px' }}>Threat Intelligence</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="card">
          <div className="card-title">Vulnerability by Category</div>
          <table style={{ width: '100%', fontSize: '0.9rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '8px' }}>Category</th>
                <th style={{ padding: '8px' }}>Total</th>
                <th style={{ padding: '8px' }}>Breaches</th>
                <th style={{ padding: '8px' }}>Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics.category_breakdown || {}).map(([cat, data]: [string, any]) => (
                <tr key={cat} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '8px', textTransform: 'capitalize' }}>{cat.replace('_', ' ')}</td>
                  <td style={{ padding: '8px' }}>{data.total}</td>
                  <td style={{ padding: '8px', color: data.successes > 0 ? 'var(--danger-color)' : 'inherit' }}>{data.successes}</td>
                  <td style={{ padding: '8px' }}>{(data.success_rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-title">Vulnerability by Target</div>
          <table style={{ width: '100%', fontSize: '0.9rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '8px' }}>Target</th>
                <th style={{ padding: '8px' }}>Total</th>
                <th style={{ padding: '8px' }}>Breaches</th>
                <th style={{ padding: '8px' }}>Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics.target_breakdown || {}).map(([tgt, data]: [string, any]) => (
                <tr key={tgt} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '8px' }}>{tgt}</td>
                  <td style={{ padding: '8px' }}>{data.total}</td>
                  <td style={{ padding: '8px', color: data.successes > 0 ? 'var(--danger-color)' : 'inherit' }}>{data.successes}</td>
                  <td style={{ padding: '8px' }}>{(data.success_rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="card-title">Evasion Converter Efficacy</div>
          <table style={{ width: '100%', fontSize: '0.9rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '8px' }}>Converter Technique</th>
                <th style={{ padding: '8px' }}>Attempts</th>
                <th style={{ padding: '8px' }}>Successes</th>
                <th style={{ padding: '8px' }}>Efficacy Rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics.converter_breakdown || {}).map(([conv, data]: [string, any]) => (
                <tr key={conv} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '8px', textTransform: 'capitalize' }}>{conv.replace('_', ' ')}</td>
                  <td style={{ padding: '8px' }}>{data.total}</td>
                  <td style={{ padding: '8px' }}>{data.successes}</td>
                  <td style={{ padding: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '100px', height: '6px', backgroundColor: 'var(--bg-color)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${data.success_rate * 100}%`, backgroundColor: data.success_rate > 0.3 ? 'var(--danger-color)' : 'var(--accent-color)' }}></div>
                      </div>
                      {(data.success_rate * 100).toFixed(1)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
