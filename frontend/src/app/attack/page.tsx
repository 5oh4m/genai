"use client";

import { useState } from "react";
import { runAttack, runBatchAttack } from "@/lib/api";

export default function AttackPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [target, setTarget] = useState("support_chatbot");
  const [objective, setObjective] = useState("impersonation");
  const [strategy, setStrategy] = useState("single_turn");
  const [converter, setConverter] = useState("none");
  const [batchMode, setBatchMode] = useState(false);

  const handleLaunch = async () => {
    setLoading(true);
    setResult(null);
    try {
      const config = { target, objective, strategy, converter };
      const res = batchMode 
        ? await runBatchAttack({ num_attempts: 5, targets: [target], objectives: [objective], strategies: [strategy], converters: [converter] })
        : await runAttack(config);
      setResult(res);
    } catch (e) {
      console.error(e);
      setResult({ error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workspace-panel active">
      <h1 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '20px' }}>Red Team Attack Engine</h1>

      <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
        <div className="card" style={{ flex: 1 }}>
          <div className="card-title">Attack Configuration</div>
          
          <div className="form-group">
            <label>Target Service</label>
            <select className="form-control" value={target} onChange={e => setTarget(e.target.value)}>
              <option value="support_chatbot">Support Chatbot</option>
              <option value="invoice_agent">Invoice Agent</option>
              <option value="merchant_onboarding">Merchant Onboarding</option>
            </select>
          </div>

          <div className="form-group">
            <label>Objective</label>
            <select className="form-control" value={objective} onChange={e => setObjective(e.target.value)}>
              <option value="impersonation">Impersonation / Voice Clone</option>
              <option value="injected_instruction">Injected Instruction</option>
              <option value="coercion">Coercion / Authority Pressure</option>
            </select>
          </div>

          <div className="form-group">
            <label>Strategy</label>
            <select className="form-control" value={strategy} onChange={e => setStrategy(e.target.value)}>
              <option value="single_turn">Single Turn (Direct)</option>
              <option value="multi_turn_escalation">Multi-turn Escalation</option>
            </select>
          </div>

          <div className="form-group">
            <label>Evasion Converter</label>
            <select className="form-control" value={converter} onChange={e => setConverter(e.target.value)}>
              <option value="none">None (Plain Text)</option>
              <option value="base64">Base64 Encode</option>
              <option value="roleplay">Roleplay Wrap</option>
              <option value="paraphrase">Casual Paraphrase</option>
              <option value="unicode_substitution">Unicode Lookalikes</option>
            </select>
          </div>

          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center' }}>
            <input type="checkbox" id="batch" checked={batchMode} onChange={e => setBatchMode(e.target.checked)} />
            <label htmlFor="batch" style={{ margin: 0, cursor: 'pointer' }}>Run as Batch (5 attempts)</label>
          </div>

          <button 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '10px' }}
            onClick={handleLaunch}
            disabled={loading}
          >
            {loading ? "Executing Attack..." : "Launch Attack"}
          </button>
        </div>

        <div className="card" style={{ flex: 2, minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-title">Attack Results</div>
          {result ? (
            <div style={{ overflowY: 'auto', flex: 1, backgroundColor: 'var(--bg-color)', padding: '15px', borderRadius: '6px', fontSize: '0.85rem' }}>
              {batchMode ? (
                <div>
                  <h3>Batch Completed: {result.total_attempts} attempts</h3>
                  <pre>{JSON.stringify(result.metrics, null, 2)}</pre>
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <h3 style={{ color: result.success ? 'var(--danger-color)' : 'var(--success-color)' }}>
                      {result.success ? "ATTACK SUCCESSFUL" : "ATTACK BLOCKED"}
                    </h3>
                    <span className="verdict-badge verdict-block">{result.blue_team_verdict}</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '15px' }}>{result.blue_team_reasoning}</p>
                  
                  <h4>Transcript</h4>
                  <div className="transcript-box" style={{ marginTop: '10px', maxHeight: '300px' }}>
                    {result.full_transcript?.map((msg: any, i: number) => (
                      <div key={i} className={`msg ${msg.role}`}>
                        <div className="msg-bubble">{msg.content || JSON.stringify(msg.tool_calls)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              Configure and launch an attack to see results.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
