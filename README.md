# NEXUSDEAL: Multi-Agent Autonomous Negotiation & Escrow Protocol
**Target Stack:** Fetch.ai `uagents>=0.25.5`, `uagents-core`, `AgentChatProtocol` (v0.3.0), FastAPI, Tailwind Dark UI.

---

## 🚀 Teammate Setup Instructions

### 1. Install Dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
The `.env` file is pre-configured with identical seeds and derived agent addresses:
- `MASTER_AGENT_ADDRESS="agent1qwz2fqqgthdu2vnsfld69gq48evmv0ggqzrjpr48djf3j9k2vhedzaxu3kh"`
- `CREATOR_AGENT_ADDRESS="agent1q2ae2qru6t8aay0f0wepwqgxsnlcr2ynnhfx4w9udnmgxm5gkdv7qvk0ezx"`
- `VAULT_AGENT_ADDRESS="agent1qgy29fmge7gqrk04anxr62s2qs54gdv9hfh7y6y585cvvgzsvtvx2fc3et8"`

---

## 🏃 Running Agents by Teammate

### Laptop 1: Master Orchestrator (Umair)
Runs the Master Agent with `AgentChatProtocol 0.3.0` on port 8000:
```bash
python master_agent.py
```

### Laptop 2: Creator Sponsorship Agent (Vivek)
Runs Sub-Agent A on port 8001 with 2-round CPM negotiation & YouTube deliverable verification:
```bash
python creator_agent.py
```

### Laptop 3: Collectibles Vault Agent (Utkarsh)
Runs Sub-Agent B on port 8002 with vault inventory & $25 trade-in credit:
```bash
python collectibles_agent.py
```

---

## 🖥️ Live Dashboard UI
To view the real-time agent status cards and trigger deals with one click:
```bash
python dashboard.py
```
Open **http://localhost:8080** in your browser.
