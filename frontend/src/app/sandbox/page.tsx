"use client";

import { useState } from "react";
import { runSandbox } from "@/lib/api";

export default function SandboxPage() {
  const [target, setTarget] = useState("support_chatbot");
  const [message, setMessage] = useState("Hi, I need help with my account.");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await runSandbox(target, message);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workspace-panel active">
      <h1 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '20px' }}>Target Sandbox</h1>
      
      <div style={{ display: 'flex', gap: '20px' }}>
        <div className="card" style={{ flex: 1 }}>
          <div className="card-title">Direct Interaction</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '15px' }}>
            Send messages directly to the target agents. Defenses (Guard Rules + LLM Judge) are active.
          </p>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Target Agent</label>
              <select className="form-control" value={target} onChange={e => setTarget(e.target.value)}>
                <option value="support_chatbot">Support Chatbot</option>
                <option value="invoice_agent">Invoice Agent</option>
                <option value="merchant_onboarding">Merchant Onboarding</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Message</label>
              <textarea 
                className="form-control" 
                rows={5} 
                value={message} 
                onChange={e => setMessage(e.target.value)}
              />
            </div>
            
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Sending..." : "Send Message"}
            </button>
          </form>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <div className="card-title">Response</div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', fontSize: '0.9rem' }}>
              <div>
                <strong style={{ color: 'var(--text-secondary)' }}>Agent Reply:</strong>
                <div style={{ marginTop: '5px', padding: '10px', backgroundColor: 'var(--bg-color)', borderRadius: '6px' }}>
                  {result.response}
                </div>
              </div>
              
              <div>
                <strong style={{ color: 'var(--text-secondary)' }}>Defense Verdict:</strong>
                <div style={{ marginTop: '5px' }}>
                  {result.verdict ? (
                    <span className={`verdict-badge ${result.verdict.final_verdict === 'allowed' ? 'verdict-allow' : 'verdict-block'}`}>
                      {result.verdict.final_verdict.toUpperCase()}
                    </span>
                  ) : (
                    "None"
                  )}
                </div>
              </div>

              {result.tool_calls?.length > 0 && (
                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Tools Called:</strong>
                  <pre style={{ marginTop: '5px', padding: '10px', backgroundColor: 'var(--bg-color)', borderRadius: '6px', fontSize: '0.8rem', overflowX: 'auto' }}>
                    {JSON.stringify(result.tool_calls, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Awaiting input...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
