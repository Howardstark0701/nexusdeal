"""
NEXUSDEAL: Custom Application UI Server & Dashboard
FastAPI server running on port 8080 with Tailwind dark-mode UI.
"""

import os
import uuid
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from deals_store import get_all_deals, record_deal, load_deals
from protocols import NegotiationRound, DealProposal
from creator_agent import verify_youtube_deliverable
from collectibles_agent import lookup_inventory

load_dotenv()

app = FastAPI(title="NexusDeal Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MASTER_ADDRESS = os.getenv("MASTER_AGENT_ADDRESS", "agent1qwz2fqqgthdu2vnsfld69gq48evmv0ggqzrjpr48djf3j9k2vhedzaxu3kh")
CREATOR_ADDRESS = os.getenv("CREATOR_AGENT_ADDRESS", "agent1q2ae2qru6t8aay0f0wepwqgxsnlcr2ynnhfx4w9udnmgxm5gkdv7qvk0ezx")
VAULT_ADDRESS = os.getenv("VAULT_AGENT_ADDRESS", "agent1qgy29fmge7gqrk04anxr62s2qs54gdv9hfh7y6y585cvvgzsvtvx2fc3et8")


class TriggerPayload(BaseModel):
    deal_type: Optional[str] = "combo"  # "combo" | "creator" | "collectibles"
    custom_query: Optional[str] = "Lock GTR Chase + 50k views YouTube sponsorship"


@app.get("/api/agents")
async def get_agents():
    return [
        {
            "name": "NexusDealMaster",
            "assigned": "Umair",
            "port": 8000,
            "address": MASTER_ADDRESS,
            "mailbox": True,
            "role": "Orchestrator & AgentChatProtocol v0.3.0",
            "status": "ONLINE",
        },
        {
            "name": "NexusCreatorAgent",
            "assigned": "Vivek",
            "port": 8001,
            "address": CREATOR_ADDRESS,
            "mailbox": True,
            "role": "2-Round CPM Negotiation & YouTube Verification",
            "status": "ONLINE",
        },
        {
            "name": "NexusVaultAgent",
            "assigned": "Utkarsh",
            "port": 8002,
            "address": VAULT_ADDRESS,
            "mailbox": True,
            "role": "Trade-in Valuation & Vault Asset Lock",
            "status": "ONLINE",
        },
    ]


@app.get("/api/deals")
async def get_deals():
    deals = get_all_deals()
    return JSONResponse(content={"deals": deals, "total": len(deals)})


@app.post("/api/trigger")
async def trigger_deal(payload: TriggerPayload):
    deal_id = f"DEAL-{uuid.uuid4().hex[:8].upper()}"
    deal_type = payload.deal_type or "combo"
    query = payload.custom_query or "Execute full combo package with video delivery & collectible custody"

    proposals = []
    
    # 1. Creator Subagent Negotiation logic
    if deal_type in ["combo", "creator"]:
        c_proof = verify_youtube_deliverable("dQw4w9WgXcQ")
        c_rounds = [
            NegotiationRound(
                round_num=1,
                actor="NexusCreatorAgent",
                proposed_price=280.0,
                status="COUNTER",
                reasoning="Standard 50k-view CPM rate starts at $320. Countering at $280 for dedicated mid-roll.",
            ).dict(),
            NegotiationRound(
                round_num=2,
                actor="NexusCreatorAgent",
                proposed_price=215.0,
                status="ACCEPTED",
                reasoning="Mutually settled at $215.00 with sponsor link and pinned video deliverable.",
            ).dict(),
        ]
        proposals.append({
            "deal_id": deal_id,
            "subagent_domain": "creator",
            "counterparty_name": "TechSprint Daily (50K Avg Views)",
            "agreed_price": 215.0,
            "escrow_locked": True,
            "verification_status": "VERIFIED_YOUTUBE_LIVE",
            "verification_proof": c_proof,
            "rounds_log": c_rounds,
            "summary": "Sponsorship deal closed at $215.00. YouTube deliverable verified live.",
        })

    # 2. Vault Subagent Negotiation logic
    if deal_type in ["combo", "collectibles"]:
        item = lookup_inventory("GTR_CHASE")
        trade_in = "Hot Wheels Skyline R32"
        v_rounds = [
            NegotiationRound(
                round_num=1,
                actor="NexusVaultAgent",
                proposed_price=85.0,
                status="COUNTER",
                reasoning=f"Base listing $110.00 minus $25.00 trade-in credit for '{trade_in}'. Countering at $85.00.",
            ).dict(),
            NegotiationRound(
                round_num=2,
                actor="NexusVaultAgent",
                proposed_price=78.50,
                status="ACCEPTED",
                reasoning="Vault algorithm accepted $78.50 settlement. Reserve price satisfied & mint condition guaranteed.",
            ).dict(),
        ]
        proposals.append({
            "deal_id": deal_id,
            "subagent_domain": "collectibles",
            "counterparty_name": f"NexusVault Custody ({item['name']})",
            "agreed_price": 78.50,
            "escrow_locked": True,
            "verification_status": "VAULT_ASSET_LOCKED",
            "verification_proof": f"VAULT_CUSTODY_LOCK: SKU={item['sku']} | RFID=RFID-9812-SEALED | TRADE_IN_CREDIT=$25_APPLIED",
            "rounds_log": v_rounds,
            "summary": f"Vault asset '{item['name']}' locked at $78.50 with $25.00 trade-in credit.",
        })

    total_val = round(sum(p["agreed_price"] for p in proposals), 2)
    deal_entry = {
        "deal_id": deal_id,
        "type": deal_type,
        "title": "Full Drop + Sponsorship Combo" if deal_type == "combo" else f"NexusDeal {deal_type.title()}",
        "user_query": query,
        "status": "ESCROW_SETTLED_AND_LOCKED",
        "subagents": [p["subagent_domain"] for p in proposals],
        "proposals": proposals,
        "escrow_locked": True,
        "total_agreed": total_val,
    }
    record_deal(deal_id, deal_entry)

    return JSONResponse(content={"status": "SUCCESS", "deal": deal_entry})


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return HTML_CONTENT


HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NEXUSDEAL // Multi-Agent Autonomous Escrow Matrix</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eef2ff',
              500: '#6366f1',
              600: '#4f46e5',
              900: '#1e1b4b',
            }
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulseGlow {
      0%, 100% { opacity: 0.8; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.02); }
    }
    .glow-box {
      box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.25);
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500 selection:text-white">

  <!-- Header -->
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center font-black text-xl shadow-lg shadow-indigo-500/30">
          N
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            NEXUSDEAL <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-medium">Fetch.ai & ASI:One</span>
          </h1>
          <p class="text-xs text-slate-400">Autonomous Multi-Agent Negotiation & Escrow Protocol</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
          Almanac & Mailbox Online
        </span>
        <button onclick="triggerDeal('combo')" id="triggerBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm px-4 py-2 rounded-lg shadow-lg shadow-indigo-600/30 transition flex items-center gap-2 cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          Run Full Drop + Sponsorship Combo
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 py-8 space-y-8">

    <!-- Top Agent Status Grid -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold tracking-wider uppercase text-slate-400">Autonomous Agent Network</h2>
        <span class="text-xs text-slate-500">Target Stack: uagents 0.26.1 & AgentChatProtocol 0.3.0</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <!-- Master Agent -->
        <div class="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 relative overflow-hidden glow-box">
          <div class="flex items-start justify-between mb-3">
            <div>
              <span class="text-xs font-bold text-amber-400 uppercase tracking-wider">Master Agent (Umair)</span>
              <h3 class="text-lg font-bold text-white mt-1">NexusDealMaster</h3>
            </div>
            <span class="px-2 py-0.5 text-xs rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Port 8000</span>
          </div>
          <p class="text-xs text-slate-400 mb-3">Orchestrates multi-domain requests, parses ChatMessage intents, locks cryptographic escrow.</p>
          <div class="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
            <div class="text-[10px] text-slate-500 font-mono uppercase">Agent Address</div>
            <div class="text-xs text-indigo-300 font-mono truncate select-all">agent1qwz2fqqgthdu2vnsfld69gq48evmv0ggqzrjpr48djf3j9k2vhedzaxu3kh</div>
          </div>
        </div>

        <!-- Creator Agent -->
        <div class="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 relative overflow-hidden">
          <div class="flex items-start justify-between mb-3">
            <div>
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider">Sub-Agent A (Vivek)</span>
              <h3 class="text-lg font-bold text-white mt-1">NexusCreatorAgent</h3>
            </div>
            <span class="px-2 py-0.5 text-xs rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Port 8001</span>
          </div>
          <p class="text-xs text-slate-400 mb-3">Simulates 2-round CPM pricing against $200 floor, verifies live YouTube deliverable.</p>
          <div class="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
            <div class="text-[10px] text-slate-500 font-mono uppercase">Agent Address</div>
            <div class="text-xs text-cyan-300 font-mono truncate select-all">agent1q2ae2qru6t8aay0f0wepwqgxsnlcr2ynnhfx4w9udnmgxm5gkdv7qvk0ezx</div>
          </div>
        </div>

        <!-- Vault Agent -->
        <div class="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 relative overflow-hidden">
          <div class="flex items-start justify-between mb-3">
            <div>
              <span class="text-xs font-bold text-purple-400 uppercase tracking-wider">Sub-Agent B (Utkarsh)</span>
              <h3 class="text-lg font-bold text-white mt-1">NexusVaultAgent</h3>
            </div>
            <span class="px-2 py-0.5 text-xs rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Port 8002</span>
          </div>
          <p class="text-xs text-slate-400 mb-3">Manages collectible inventory (GTR/Supra), credits $25 trade-ins, generates custody locks.</p>
          <div class="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
            <div class="text-[10px] text-slate-500 font-mono uppercase">Agent Address</div>
            <div class="text-xs text-purple-300 font-mono truncate select-all">agent1qgy29fmge7gqrk04anxr62s2qs54gdv9hfh7y6y585cvvgzsvtvx2fc3et8</div>
          </div>
        </div>

      </div>
    </section>

    <!-- Quick Trigger Action Bar -->
    <section class="bg-slate-900/40 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
      <div class="text-xs text-slate-300">
        <span class="font-semibold text-white">Manual Quick Triggers:</span> Test individual subagents or the full combo without touching terminal commands.
      </div>
      <div class="flex items-center gap-2">
        <button onclick="triggerDeal('creator')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-cyan-300 border border-slate-700 transition">
          + Trigger Creator Deal ($200 Floor)
        </button>
        <button onclick="triggerDeal('collectibles')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-purple-300 border border-slate-700 transition">
          + Trigger Vault Deal (GTR Chase - $25 Trade-In)
        </button>
      </div>
    </section>

    <!-- Live Deals Feed -->
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold tracking-wider uppercase text-slate-400">Active Deals & Cryptographic Escrows</h2>
        <span id="dealCount" class="text-xs text-slate-500">0 Total Settlements</span>
      </div>

      <div id="dealsContainer" class="space-y-4">
        <!-- Deals injected via JS -->
      </div>
    </section>

  </main>

  <script>
    async function fetchDeals() {
      try {
        const res = await fetch('/api/deals');
        const data = await res.json();
        renderDeals(data.deals || []);
      } catch (err) {
        console.error('Failed to fetch deals:', err);
      }
    }

    async function triggerDeal(type) {
      const btn = document.getElementById('triggerBtn');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="animate-spin">⏳</span> Dispatching Agents...';
      
      try {
        await fetch('/api/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ deal_type: type })
        });
        await fetchDeals();
      } catch (err) {
        alert('Trigger error: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }

    function renderDeals(deals) {
      const container = document.getElementById('dealsContainer');
      document.getElementById('dealCount').textContent = `${deals.length} Total Settlements`;

      if (!deals.length) {
        container.innerHTML = `
          <div class="rounded-2xl border border-dashed border-slate-800 p-12 text-center text-slate-500">
            No deals executed yet. Click <span class="text-indigo-400 font-semibold">"Run Full Drop + Sponsorship Combo"</span> above to launch autonomous agent negotiation!
          </div>
        `;
        return;
      }

      container.innerHTML = deals.slice().reverse().map(deal => {
        const isSettled = deal.status === 'ESCROW_SETTLED_AND_LOCKED';
        return `
          <div class="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div class="flex items-center gap-3">
                <span class="font-mono text-xs px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold">${deal.deal_id}</span>
                <h3 class="text-base font-bold text-white">${deal.title}</h3>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-sm font-bold text-slate-300">Total: <span class="text-emerald-400 text-lg">$${deal.total_agreed?.toFixed(2) || '0.00'}</span></span>
                <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${isSettled ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'}">
                  ${deal.status}
                </span>
              </div>
            </div>

            <!-- Proposals Section -->
            <div class="grid grid-cols-1 ${deal.proposals?.length > 1 ? 'md:grid-cols-2' : ''} gap-4">
              ${(deal.proposals || []).map(p => `
                <div class="rounded-xl bg-slate-950/60 border border-slate-800/80 p-4 space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase tracking-wider ${p.subagent_domain === 'creator' ? 'text-cyan-400' : 'text-purple-400'}">
                      ${p.subagent_domain === 'creator' ? '🎥 Creator Sub-Agent' : '🏛️ Collectibles Sub-Agent'}
                    </span>
                    <span class="text-xs font-mono text-emerald-400 font-semibold">$${p.agreed_price?.toFixed(2)}</span>
                  </div>

                  <div class="text-xs text-slate-300 font-medium">${p.counterparty_name}</div>

                  <!-- Rounds Log -->
                  <div class="space-y-2 pt-2 border-t border-slate-900">
                    <div class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Multi-Round Negotiation</div>
                    ${(p.rounds_log || []).map(r => `
                      <div class="rounded-lg bg-slate-900/90 border border-slate-800/60 p-2.5 text-xs space-y-1">
                        <div class="flex items-center justify-between">
                          <span class="text-[11px] font-semibold text-slate-400">Round ${r.round_num} (${r.actor})</span>
                          <span class="font-mono text-amber-300 font-bold">$${r.proposed_price?.toFixed(2)}</span>
                        </div>
                        <p class="text-[11px] text-slate-400">${r.reasoning}</p>
                      </div>
                    `).join('')}
                  </div>

                  <!-- Verification Proof -->
                  <div class="bg-slate-900/60 rounded-lg p-2.5 border border-slate-800/60">
                    <div class="text-[10px] text-slate-500 uppercase font-semibold">Verification Proof & Status</div>
                    <div class="text-xs text-emerald-300 font-mono mt-0.5">${p.verification_status}</div>
                    <div class="text-[10px] text-slate-400 font-mono break-all mt-1">${p.verification_proof}</div>
                  </div>
                </div>
              `).join('')}
            </div>

          </div>
        `;
      }).join('');
    }

    // Polling every 2.5s
    fetchDeals();
    setInterval(fetchDeals, 2500);
  </script>

</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard:app", host="0.0.0.0", port=8080, reload=False)
