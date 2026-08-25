# AEGIS-AI // AI Agent Red Team vs Blue Team Security Lab

AEGIS-AI is a closed-loop simulation environment for adversarial AI defense. It tests the resilience of agentic AI services against social engineering, prompt injection, and coercion attacks, and automatically hardens its defenses through a feedback loop.

## Architecture

This project simulates a **Red Team vs Blue Team** adversarial environment.

- **Targets (Tier 1)**: AI-backed services (`SupportChatbot`, `InvoiceAgent`, `MerchantOnboarding`) that can perform sensitive actions (refunds, account unlocks, invoice approvals) via tool calls.
- **Red Team (Attacker)**: A fully autonomous `RedTeamAgent` powered by the OpenRouter OpenAI SDK (using `stealth/ox-alpha`). The attacker dynamically generates bespoke social engineering, prompt injection, and coercion attacks via multi-turn improvisational roleplay. It dynamically reads target responses and adapts its tactics on the fly.
- **Blue Team (Defense)**: A two-layer defense system:
  1. **Guard Rules**: Deterministic, high-speed circuit breakers (regex/keyword matching).
  2. **LLM Judge Agent**: Adaptive, contextual evaluator for ambiguous attacks.
  - **Autonomous Hardening (Feedback Loop)**: Analyzes the raw transcripts of successful breaches and feeds them to a `DefenseArchitectAgent`. The Architect dynamically hallucinates and injects highly specific Python guard rules and Judge prompt amendments to patch the vulnerabilities in real-time.

## Prerequisites

- Python 3.10+
- An OpenRouter API Key for the `stealth/ox-alpha` model ([Get one here](https://openrouter.ai/keys))
- (Optional) PostgreSQL for production scaling (defaults to SQLite for local development).

## Installation

1. **Clone & Install Dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   alembic upgrade head
   ```

3. **Environment Setup**
   Copy `.env.example` to `.env` and insert your OpenRouter API key:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENROUTER_MODEL=stealth/ox-alpha
   ```

4. **Build Frontend (Next.js)**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

## Running the Simulation

Start the FastAPI server (which also serves the compiled Next.js UI):

```bash
python3 run_server.py
```

- **Dashboard**: `http://127.0.0.1:8000`
- **API Docs**: `http://127.0.0.1:8000/docs`

### Dashboard Navigation

1. **Stream**: Watch live attacks and monitor success/block rates in real time.
2. **Red Team**: Configure targets, objectives, strategies, and evasion converters, then launch single or batch attacks.
3. **Blue Team**: View active defenses and trigger the **Auto-Harden Cycle** to patch vulnerabilities based on past breaches.
4. **Threats**: Analyze vulnerability metrics and evasion converter efficacy.
5. **Sandbox**: Manually converse with defended targets to test prompt injection directly.
