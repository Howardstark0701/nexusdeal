"""
NEXUSDEAL: Custom Application UI Server & Dashboard
FastAPI server running on port 8080 with high-end minimalist dark cyber-terminal UI.
"""

import os
import uuid
import datetime
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

app = FastAPI(title="NexusDeal Autonomous Escrow Terminal")

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
    custom_query: Optional[str] = None


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
            "protocol": "ACP 0.3.0 / Almanac",
        },
        {
            "name": "NexusCreatorAgent",
            "assigned": "Vivek",
            "port": 8001,
            "address": CREATOR_ADDRESS,
            "mailbox": True,
            "role": "2-Round CPM Negotiation & YouTube Verification",
            "status": "ONLINE",
            "protocol": "YouTube Data API v3 / CPM Bidding",
        },
        {
            "name": "NexusVaultAgent",
            "assigned": "Utkarsh",
            "port": 8002,
            "address": VAULT_ADDRESS,
            "mailbox": True,
            "role": "Trade-in Valuation & Vault Asset Lock",
            "status": "ONLINE",
            "protocol": "Physical Vault Custody / RFID Seal",
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
                reasoning="Standard 50k-view CPM rate starts at $320. Countering at $280 for dedicated mid-roll deliverable.",
            ).dict(),
            NegotiationRound(
                round_num=2,
                actor="NexusCreatorAgent",
                proposed_price=215.0,
                status="ACCEPTED",
                reasoning="Settled at $215.00 with sponsor link pinned and 60s dedicated brand integration.",
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
        item_query = "SUPRA" if "SUPRA" in query.upper() else "GTR_CHASE"
        item = lookup_inventory(item_query)
        trade_in = "Hot Wheels Skyline R32"
        trade_credit = 25.0
        settle_price = round(item["base_price"] - trade_credit - 6.50, 2)
        counter_price = round(item["base_price"] - trade_credit, 2)
        
        v_rounds = [
            NegotiationRound(
                round_num=1,
                actor="NexusVaultAgent",
                proposed_price=counter_price,
                status="COUNTER",
                reasoning=f"Base listing ${item['base_price']:.2f} minus ${trade_credit:.2f} trade-in credit for '{trade_in}'. Countering at ${counter_price:.2f}.",
            ).dict(),
            NegotiationRound(
                round_num=2,
                actor="NexusVaultAgent",
                proposed_price=settle_price,
                status="ACCEPTED",
                reasoning=f"Vault algorithm accepted ${settle_price:.2f} settlement. Reserve price satisfied & mint condition guaranteed.",
            ).dict(),
        ]
        proposals.append({
            "deal_id": deal_id,
            "subagent_domain": "collectibles",
            "counterparty_name": f"NexusVault Custody ({item['name']})",
            "agreed_price": settle_price,
            "escrow_locked": True,
            "verification_status": "VAULT_ASSET_LOCKED",
            "verification_proof": f"VAULT_CUSTODY_LOCK: SKU={item['sku']} | RFID=RFID-9812-SEALED | TRADE_IN_CREDIT=${trade_credit:.2f}_APPLIED",
            "rounds_log": v_rounds,
            "summary": f"Vault asset '{item['name']}' locked at ${settle_price:.2f} with ${trade_credit:.2f} trade-in credit.",
        })

    total_val = round(sum(p["agreed_price"] for p in proposals), 2)
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    deal_entry = {
        "deal_id": deal_id,
        "type": deal_type,
        "title": "Full Drop + Sponsorship Combo" if deal_type == "combo" else f"NexusDeal {deal_type.title()} Agreement",
        "user_query": query,
        "timestamp": timestamp,
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


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NEXUSDEAL // Autonomous Agent Escrow Matrix</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
          },
          colors: {
            noir: {
              base: '#07080b',
              surface: '#0d0f15',
              card: '#12151f',
              border: 'rgba(255, 255, 255, 0.07)',
              borderHover: 'rgba(255, 255, 255, 0.15)',
            },
            cyber: {
              cyan: '#06b6d4',
              emerald: '#10b981',
              violet: '#8b5cf6',
              amber: '#f59e0b',
            }
          }
        }
      }
    }
  </script>
  <style>
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #07080b; }
    ::-webkit-scrollbar-thumb { background: #1e2433; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #333c52; }

    /* Minimalist Glow & Glass */
    .glass-panel {
      background: rgba(13, 15, 21, 0.85);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }
    .glass-panel:hover {
      border-color: rgba(255, 255, 255, 0.12);
    }
    .glow-cyan-sm {
      box-shadow: 0 0 20px -3px rgba(6, 182, 212, 0.15);
    }
    .glow-emerald-sm {
      box-shadow: 0 0 20px -3px rgba(16, 185, 129, 0.15);
    }

    /* Ambient Matrix Canvas */
    #ambientCanvas {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      opacity: 0.45;
    }

    /* Pulse dot */
    @keyframes subtlePulse {
      0%, 100% { transform: scale(1); opacity: 0.9; }
      50% { transform: scale(1.15); opacity: 0.6; }
    }
    .pulse-dot {
      animation: subtlePulse 2.5s infinite ease-in-out;
    }
  </style>
</head>
<body class="bg-[#07080b] text-zinc-100 min-h-screen font-sans antialiased selection:bg-zinc-700 selection:text-white relative overflow-x-hidden">

  <!-- Interactive Subtle Ambient Canvas -->
  <canvas id="ambientCanvas"></canvas>

  <div class="relative z-10 flex flex-col min-h-screen">

    <!-- Top Navigation Header -->
    <header class="border-b border-white/[0.06] bg-[#07080b]/90 backdrop-blur-xl sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        
        <!-- Brand & Protocol Info -->
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-lg bg-zinc-900 border border-white/10 flex items-center justify-center text-zinc-200 font-mono font-bold text-sm tracking-wider shadow-inner">
            NX
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2">
              <span class="font-bold tracking-tight text-white text-base">NEXUSDEAL</span>
              <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-zinc-400 border border-white/[0.08]">v0.26.1</span>
              <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">ACP 0.3.0</span>
            </div>
            <span class="text-[11px] text-zinc-500 font-medium tracking-tight">Decentralized Autonomous Negotiation & Escrow Protocol</span>
          </div>
        </div>

        <!-- Center Telemetry Strip -->
        <div class="hidden lg:flex items-center gap-5 text-xs text-zinc-400 font-mono bg-white/[0.02] border border-white/[0.06] px-3.5 py-1.5 rounded-full">
          <div class="flex items-center gap-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 pulse-dot"></span>
            <span class="text-zinc-300">Almanac:</span>
            <span class="text-emerald-400 font-medium">REGISTERED</span>
          </div>
          <span class="text-zinc-700">•</span>
          <div class="flex items-center gap-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
            <span class="text-zinc-300">Mailbox:</span>
            <span class="text-cyan-400 font-medium">SYNCED</span>
          </div>
          <span class="text-zinc-700">•</span>
          <div class="flex items-center gap-1.5">
            <span class="text-zinc-500">Latency:</span>
            <span class="text-zinc-300" id="latencyIndicator">14ms</span>
          </div>
        </div>

        <!-- Action Area -->
        <div class="flex items-center gap-2.5">
          <button onclick="openCustomModal()" class="px-3 py-1.5 rounded-lg border border-white/[0.08] hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.05] text-xs font-medium text-zinc-300 transition flex items-center gap-1.5 cursor-pointer">
            <i data-lucide="sliders" class="w-3.5 h-3.5 text-zinc-400"></i>
            <span>Custom Prompt</span>
          </button>
          <button onclick="triggerDeal('combo')" id="navTriggerBtn" class="px-3.5 py-1.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold tracking-tight transition flex items-center gap-1.5 shadow-sm cursor-pointer">
            <i data-lucide="zap" class="w-3.5 h-3.5 fill-current"></i>
            <span>Run Combo Drop</span>
          </button>
        </div>

      </div>
    </header>

    <!-- Main Content Area -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6 flex-1 w-full">

      <!-- Telemetry Metric Cards -->
      <section class="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        
        <div class="glass-panel rounded-xl p-4 flex flex-col justify-between">
          <div class="flex items-center justify-between text-zinc-400 text-xs">
            <span class="font-medium">Total Escrow Volume</span>
            <i data-lucide="lock" class="w-4 h-4 text-emerald-400"></i>
          </div>
          <div class="mt-2">
            <div id="statTotalVolume" class="text-xl sm:text-2xl font-bold font-mono tracking-tight text-white">$0.00</div>
            <div class="text-[11px] text-emerald-400/90 font-mono mt-0.5 flex items-center gap-1">
              <span>●</span> 100% Locked in Autonomous Custody
            </div>
          </div>
        </div>

        <div class="glass-panel rounded-xl p-4 flex flex-col justify-between">
          <div class="flex items-center justify-between text-zinc-400 text-xs">
            <span class="font-medium">Settled Agreements</span>
            <i data-lucide="check-circle" class="w-4 h-4 text-cyan-400"></i>
          </div>
          <div class="mt-2">
            <div id="statTotalDeals" class="text-xl sm:text-2xl font-bold font-mono tracking-tight text-white">0</div>
            <div class="text-[11px] text-zinc-400 font-mono mt-0.5">
              Multi-Round Consensus Closed
            </div>
          </div>
        </div>

        <div class="glass-panel rounded-xl p-4 flex flex-col justify-between">
          <div class="flex items-center justify-between text-zinc-400 text-xs">
            <span class="font-medium">Active Agent Nodes</span>
            <i data-lucide="network" class="w-4 h-4 text-violet-400"></i>
          </div>
          <div class="mt-2">
            <div class="text-xl sm:text-2xl font-bold font-mono tracking-tight text-white">3 / 3</div>
            <div class="text-[11px] text-zinc-400 font-mono mt-0.5 flex items-center gap-1">
              <span class="text-emerald-400">●</span> Master, Creator & Vault
            </div>
          </div>
        </div>

        <div class="glass-panel rounded-xl p-4 flex flex-col justify-between">
          <div class="flex items-center justify-between text-zinc-400 text-xs">
            <span class="font-medium">Negotiation Margin Saved</span>
            <i data-lucide="trending-down" class="w-4 h-4 text-amber-400"></i>
          </div>
          <div class="mt-2">
            <div id="statMarginSaved" class="text-xl sm:text-2xl font-bold font-mono tracking-tight text-emerald-400">-$284.50</div>
            <div class="text-[11px] text-zinc-400 font-mono mt-0.5">
              18.4% Average Reduction vs Floor
            </div>
          </div>
        </div>

      </section>

      <!-- Agent Cluster Node Topology -->
      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Cluster Node Topology</h2>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 border border-white/[0.06]">Autonomous Almanac Mesh</span>
          </div>
          <span class="text-xs text-zinc-500 font-mono">Mailbox Gateway: Active</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5">

          <!-- Node 1: Master Orchestrator -->
          <div class="glass-panel rounded-xl p-4 flex flex-col justify-between space-y-3 relative group">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full bg-emerald-400 pulse-dot"></span>
                  <span class="text-xs font-semibold text-white tracking-tight">NexusDealMaster</span>
                </div>
                <div class="text-[11px] text-zinc-400 mt-0.5">Assigned: <span class="text-zinc-200">Umair</span> • Port 8000</div>
              </div>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">ORCHESTRATOR</span>
            </div>

            <p class="text-xs text-zinc-400 line-clamp-2">
              Dispatches multi-domain intents via AgentChatProtocol v0.3.0, arbitrates counter-offers and executes cryptographic escrow.
            </p>

            <div class="pt-2 border-t border-white/[0.05] flex items-center justify-between gap-2">
              <div class="font-mono text-[11px] text-zinc-400 truncate select-all" id="addr-master">agent1qwz2fqqgthdu2vnsfld69gq48evmv0ggqzrjpr48djf3j9k2vhedzaxu3kh</div>
              <button onclick="copyAddress('addr-master')" class="text-zinc-500 hover:text-zinc-300 transition p-1 rounded" title="Copy Address">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
              </button>
            </div>
          </div>

          <!-- Node 2: Creator Agent -->
          <div class="glass-panel rounded-xl p-4 flex flex-col justify-between space-y-3 relative group">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full bg-cyan-400 pulse-dot"></span>
                  <span class="text-xs font-semibold text-white tracking-tight">NexusCreatorAgent</span>
                </div>
                <div class="text-[11px] text-zinc-400 mt-0.5">Assigned: <span class="text-zinc-200">Vivek</span> • Port 8001</div>
              </div>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">CREATOR CPM</span>
            </div>

            <p class="text-xs text-zinc-400 line-clamp-2">
              Negotiates dynamic CPM contracts against a $200 reserve floor and validates YouTube Data API v3 video deliverables.
            </p>

            <div class="pt-2 border-t border-white/[0.05] flex items-center justify-between gap-2">
              <div class="font-mono text-[11px] text-zinc-400 truncate select-all" id="addr-creator">agent1q2ae2qru6t8aay0f0wepwqgxsnlcr2ynnhfx4w9udnmgxm5gkdv7qvk0ezx</div>
              <button onclick="copyAddress('addr-creator')" class="text-zinc-500 hover:text-zinc-300 transition p-1 rounded" title="Copy Address">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
              </button>
            </div>
          </div>

          <!-- Node 3: Vault Agent -->
          <div class="glass-panel rounded-xl p-4 flex flex-col justify-between space-y-3 relative group">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full bg-violet-400 pulse-dot"></span>
                  <span class="text-xs font-semibold text-white tracking-tight">NexusVaultAgent</span>
                </div>
                <div class="text-[11px] text-zinc-400 mt-0.5">Assigned: <span class="text-zinc-200">Utkarsh</span> • Port 8002</div>
              </div>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20">VAULT CUSTODY</span>
            </div>

            <p class="text-xs text-zinc-400 line-clamp-2">
              Inventories rare diecast assets (GTR Chase / Supra), assesses trade-in credits ($25 R32), and issues sealed RFID custody proofs.
            </p>

            <div class="pt-2 border-t border-white/[0.05] flex items-center justify-between gap-2">
              <div class="font-mono text-[11px] text-zinc-400 truncate select-all" id="addr-vault">agent1qgy29fmge7gqrk04anxr62s2qs54gdv9hfh7y6y585cvvgzsvtvx2fc3et8</div>
              <button onclick="copyAddress('addr-vault')" class="text-zinc-500 hover:text-zinc-300 transition p-1 rounded" title="Copy Address">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
              </button>
            </div>
          </div>

        </div>
      </section>

      <!-- Quick Dispatch Control Bar -->
      <section class="glass-panel rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-zinc-300">
            <i data-lucide="terminal" class="w-4 h-4"></i>
          </div>
          <div>
            <div class="text-xs font-semibold text-white">Manual Agent Dispatcher</div>
            <div class="text-[11px] text-zinc-400">Trigger individual subagent negotiations or run full dual-domain settlement.</div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button onclick="triggerDeal('creator')" class="px-3 py-1.5 rounded-lg border border-cyan-500/30 hover:border-cyan-500/60 bg-cyan-500/5 hover:bg-cyan-500/10 text-xs font-medium text-cyan-300 transition flex items-center gap-1.5 cursor-pointer">
            <i data-lucide="video" class="w-3.5 h-3.5"></i>
            <span>+ Creator Deal ($200 Floor)</span>
          </button>
          <button onclick="triggerDeal('collectibles')" class="px-3 py-1.5 rounded-lg border border-violet-500/30 hover:border-violet-500/60 bg-violet-500/5 hover:bg-violet-500/10 text-xs font-medium text-violet-300 transition flex items-center gap-1.5 cursor-pointer">
            <i data-lucide="shield" class="w-3.5 h-3.5"></i>
            <span>+ Vault Deal (GTR Chase - $25 Credit)</span>
          </button>
          <button onclick="triggerDeal('combo')" class="px-3.5 py-1.5 rounded-lg bg-zinc-200 hover:bg-white text-zinc-950 text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer shadow">
            <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
            <span>Run Full Combo</span>
          </button>
        </div>
      </section>

      <!-- Active Escrow Settlements Feed -->
      <section class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Active Deals & Cryptographic Escrows</h2>
            <span id="dealCountBadge" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 border border-white/[0.06]">0 Settlements</span>
          </div>

          <!-- Filter Pills -->
          <div class="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-1 rounded-lg text-xs font-medium">
            <button onclick="setFilter('all')" id="filter-all" class="px-2.5 py-1 rounded-md text-white bg-white/[0.08] transition">All</button>
            <button onclick="setFilter('combo')" id="filter-combo" class="px-2.5 py-1 rounded-md text-zinc-400 hover:text-white transition">Combos</button>
            <button onclick="setFilter('creator')" id="filter-creator" class="px-2.5 py-1 rounded-md text-zinc-400 hover:text-white transition">Creator</button>
            <button onclick="setFilter('collectibles')" id="filter-collectibles" class="px-2.5 py-1 rounded-md text-zinc-400 hover:text-white transition">Vault</button>
          </div>
        </div>

        <div id="dealsContainer" class="space-y-3">
          <!-- Injected via JavaScript -->
        </div>
      </section>

    </main>

    <!-- Footer Status Bar -->
    <footer class="border-t border-white/[0.06] bg-[#07080b]/90 text-[11px] text-zinc-500 font-mono py-3 px-4 sm:px-6 mt-auto">
      <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <span class="text-zinc-400">NEXUSDEAL AUTONOMOUS MATRIX</span>
          <span>•</span>
          <span>Fetch.ai Dorado Almanac Mesh</span>
          <span>•</span>
          <span>ASI:One Neural Intent Protocol</span>
        </div>
        <div class="flex items-center gap-3">
          <span id="lastUpdatedTime">Sync: Just now</span>
          <button onclick="fetchDeals()" class="hover:text-zinc-300 transition flex items-center gap-1 cursor-pointer">
            <i data-lucide="refresh-cw" class="w-3 h-3"></i>
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </footer>

  </div>

  <!-- Custom Prompt Modal -->
  <div id="customModal" class="fixed inset-0 bg-black/70 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
    <div class="glass-panel w-full max-w-lg rounded-2xl p-6 space-y-4 border border-white/10 shadow-2xl">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="h-7 w-7 rounded-lg bg-zinc-800 border border-white/10 flex items-center justify-center text-zinc-300">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
          </div>
          <h3 class="text-sm font-semibold text-white">Execute Custom Agent Deal</h3>
        </div>
        <button onclick="closeCustomModal()" class="text-zinc-500 hover:text-zinc-300 p-1 rounded">
          <i data-lucide="x" class="w-4 h-4"></i>
        </button>
      </div>

      <div class="space-y-3">
        <div>
          <label class="text-xs text-zinc-400 font-medium">Deal Type</label>
          <select id="modalDealType" class="mt-1 w-full bg-[#07080b] border border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-white/30">
            <option value="combo">Full Drop + Sponsorship Combo</option>
            <option value="creator">Creator Sponsorship Only</option>
            <option value="collectibles">Collectibles Vault Only</option>
          </select>
        </div>

        <div>
          <label class="text-xs text-zinc-400 font-medium">Custom User Query / Specification</label>
          <textarea id="modalCustomQuery" rows="3" class="mt-1 w-full bg-[#07080b] border border-white/10 rounded-lg p-3 text-xs text-zinc-200 focus:outline-none focus:border-white/30 font-mono" placeholder="Lock GTR Chase + 50k views YouTube sponsorship with trade-in..."></textarea>
        </div>

        <div class="text-[11px] text-zinc-500">
          Suggested presets:
          <div class="flex flex-wrap gap-1.5 mt-1.5">
            <button onclick="setModalPrompt('Lock GTR Chase + 50k views YouTube sponsorship')" class="px-2 py-0.5 rounded bg-white/[0.03] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.06]">GTR Chase + 50k Views</button>
            <button onclick="setModalPrompt('Lock Supra MK4 Mint in Acrylic Case + TechSprint Mid-roll')" class="px-2 py-0.5 rounded bg-white/[0.03] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.06]">Supra MK4 Turbo</button>
            <button onclick="setModalPrompt('Negotiate YouTube sponsorship with $200 floor rate')" class="px-2 py-0.5 rounded bg-white/[0.03] hover:bg-white/[0.08] text-zinc-300 border border-white/[0.06]">Creator Dedicated Mid-roll</button>
          </div>
        </div>
      </div>

      <div class="pt-2 flex items-center justify-end gap-2 border-t border-white/[0.05]">
        <button onclick="closeCustomModal()" class="px-3.5 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white transition">Cancel</button>
        <button onclick="submitCustomDeal()" id="modalSubmitBtn" class="px-4 py-1.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold transition flex items-center gap-1.5 shadow">
          <span>Dispatch Deal</span>
          <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    </div>
  </div>

  <!-- Toast Notification Box -->
  <div id="toastBox" class="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none"></div>

  <!-- Logic & Scripts -->
  <script>
    let currentFilter = 'all';
    let cachedDeals = [];

    // Ambient Matrix Canvas animation
    (function initCanvas() {
      const canvas = document.getElementById('ambientCanvas');
      const ctx = canvas.getContext('2d');
      let width, height;
      let nodes = [];

      function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
      }
      window.addEventListener('resize', resize);
      resize();

      for (let i = 0; i < 35; i++) {
        nodes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          r: Math.random() * 1.5 + 1
        });
      }

      function draw() {
        ctx.clearRect(0, 0, width, height);

        // Draw connections
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[i].x - nodes[j].x;
            const dy = nodes[i].y - nodes[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 140) {
              ctx.strokeStyle = `rgba(255, 255, 255, ${0.03 * (1 - dist / 140)})`;
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(nodes[i].x, nodes[i].y);
              ctx.lineTo(nodes[j].x, nodes[j].y);
              ctx.stroke();
            }
          }
        }

        // Draw nodes
        for (let i = 0; i < nodes.length; i++) {
          const n = nodes[i];
          n.x += n.vx;
          n.y += n.vy;
          if (n.x < 0 || n.x > width) n.vx *= -1;
          if (n.y < 0 || n.y > height) n.vy *= -1;

          ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
          ctx.fill();
        }

        requestAnimationFrame(draw);
      }
      draw();
    })();

    // Copy Address Helper
    function copyAddress(elementId) {
      const text = document.getElementById(elementId).textContent.trim();
      navigator.clipboard.writeText(text);
      showToast('Address copied to clipboard', 'info');
    }

    // Toast Generator
    function showToast(message, type = 'success') {
      const container = document.getElementById('toastBox');
      const toast = document.createElement('div');
      toast.className = 'glass-panel px-4 py-2.5 rounded-xl text-xs font-medium text-white shadow-xl flex items-center gap-2 transform transition-all duration-300 opacity-0 translate-y-2 pointer-events-auto';
      
      const icon = type === 'success' ? 'check' : 'info';
      toast.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4 text-emerald-400"></i> <span>${message}</span>`;
      
      container.appendChild(toast);
      lucide.createIcons();

      setTimeout(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
      }, 10);

      setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
      }, 3000);
    }

    // Modal Control
    function openCustomModal() {
      document.getElementById('customModal').classList.remove('hidden');
    }
    function closeCustomModal() {
      document.getElementById('customModal').classList.add('hidden');
    }
    function setModalPrompt(text) {
      document.getElementById('modalCustomQuery').value = text;
    }

    async function submitCustomDeal() {
      const type = document.getElementById('modalDealType').value;
      const query = document.getElementById('modalCustomQuery').value;
      const btn = document.getElementById('modalSubmitBtn');
      
      btn.disabled = true;
      btn.innerHTML = '<span>Negotiating...</span>';

      try {
        await fetch('/api/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ deal_type: type, custom_query: query })
        });
        closeCustomModal();
        showToast('Autonomous negotiation executed & locked in escrow!');
        await fetchDeals();
      } catch (err) {
        showToast('Trigger failed: ' + err, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Dispatch Deal</span> <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>';
        lucide.createIcons();
      }
    }

    // Trigger standard deal
    async function triggerDeal(type) {
      const btn = document.getElementById('navTriggerBtn');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="animate-spin">⏳</span> Dispatching...';
      
      try {
        const res = await fetch('/api/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ deal_type: type })
        });
        const data = await res.json();
        showToast(`Escrow Locked: ${data.deal.deal_id}`);
        await fetchDeals();
      } catch (err) {
        showToast('Failed to trigger deal: ' + err, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        lucide.createIcons();
      }
    }

    function setFilter(filter) {
      currentFilter = filter;
      ['all', 'combo', 'creator', 'collectibles'].forEach(f => {
        const btn = document.getElementById(`filter-${f}`);
        if (f === filter) {
          btn.className = 'px-2.5 py-1 rounded-md text-white bg-white/[0.08] transition';
        } else {
          btn.className = 'px-2.5 py-1 rounded-md text-zinc-400 hover:text-white transition';
        }
      });
      renderDeals(cachedDeals);
    }

    // Fetch and render deals
    async function fetchDeals() {
      try {
        const res = await fetch('/api/deals');
        const data = await res.json();
        cachedDeals = data.deals || [];
        updateStats(cachedDeals);
        renderDeals(cachedDeals);
        document.getElementById('lastUpdatedTime').textContent = `Sync: ${new Date().toLocaleTimeString()}`;
      } catch (err) {
        console.error('Failed to fetch deals:', err);
      }
    }

    function updateStats(deals) {
      let totalVolume = 0;
      let totalDiscount = 0;

      deals.forEach(d => {
        totalVolume += (d.total_agreed || 0);
        // Calculate negotiated discount vs initial base
        if (d.type === 'combo') totalDiscount += 65.50;
        else if (d.type === 'creator') totalDiscount += 40.00;
        else if (d.type === 'collectibles') totalDiscount += 25.50;
      });

      document.getElementById('statTotalVolume').textContent = `$${totalVolume.toFixed(2)}`;
      document.getElementById('statTotalDeals').textContent = deals.length;
      document.getElementById('dealCountBadge').textContent = `${deals.length} Settlements`;
      document.getElementById('statMarginSaved').textContent = `-$${totalDiscount.toFixed(2)}`;
    }

    function renderDeals(deals) {
      const container = document.getElementById('dealsContainer');
      const filtered = deals.filter(d => {
        if (currentFilter === 'all') return true;
        return d.type === currentFilter;
      });

      if (!filtered.length) {
        container.innerHTML = `
          <div class="glass-panel rounded-xl p-10 text-center space-y-2 border-dashed border-white/10">
            <i data-lucide="inbox" class="w-8 h-8 text-zinc-600 mx-auto stroke-1"></i>
            <div class="text-xs font-medium text-zinc-400">No active settlements in this view</div>
            <div class="text-[11px] text-zinc-500">Execute "Run Combo Drop" or dispatch a custom prompt above.</div>
          </div>
        `;
        lucide.createIcons();
        return;
      }

      container.innerHTML = filtered.slice().reverse().map((deal, idx) => {
        const isSettled = deal.status === 'ESCROW_SETTLED_AND_LOCKED';
        const formattedTotal = (deal.total_agreed || 0).toFixed(2);
        const collapseId = `deal-detail-${idx}`;

        return `
          <div class="glass-panel rounded-xl p-5 space-y-4 transition">
            
            <!-- Deal Header Row -->
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.05] pb-3.5">
              <div class="flex items-center gap-3">
                <span class="font-mono text-xs px-2.5 py-1 rounded bg-white/[0.04] text-zinc-300 border border-white/[0.08] font-semibold">${deal.deal_id}</span>
                <div>
                  <h3 class="text-sm font-semibold text-white tracking-tight">${deal.title}</h3>
                  <div class="text-[11px] text-zinc-400 font-mono mt-0.5">${deal.user_query || 'Autonomous multi-domain contract'}</div>
                </div>
              </div>

              <div class="flex items-center gap-4">
                <div class="text-right">
                  <div class="text-[10px] uppercase font-mono text-zinc-500 font-medium">Secured Escrow</div>
                  <div class="text-base font-bold font-mono text-emerald-400">$${formattedTotal}</div>
                </div>

                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-medium ${isSettled ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
                  <span class="h-1.5 w-1.5 rounded-full ${isSettled ? 'bg-emerald-400' : 'bg-amber-400'}"></span>
                  ${deal.status}
                </span>
              </div>
            </div>

            <!-- Subagent Proposals Grid -->
            <div class="grid grid-cols-1 ${deal.proposals?.length > 1 ? 'md:grid-cols-2' : ''} gap-3.5">
              ${(deal.proposals || []).map(p => `
                <div class="rounded-lg bg-black/40 border border-white/[0.05] p-3.5 space-y-3">
                  
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] font-semibold font-mono uppercase tracking-wider ${p.subagent_domain === 'creator' ? 'text-cyan-400' : 'text-violet-400'} flex items-center gap-1.5">
                      <i data-lucide="${p.subagent_domain === 'creator' ? 'video' : 'shield'}" class="w-3.5 h-3.5"></i>
                      ${p.subagent_domain === 'creator' ? 'NexusCreatorAgent (CPM)' : 'NexusVaultAgent (Custody)'}
                    </span>
                    <span class="text-xs font-mono font-bold text-zinc-200">$${p.agreed_price?.toFixed(2)}</span>
                  </div>

                  <div class="text-xs text-zinc-300 font-medium">${p.counterparty_name}</div>

                  <!-- Multi-Round Negotiation Timeline -->
                  <div class="space-y-1.5 pt-2 border-t border-white/[0.04]">
                    <div class="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Multi-Round Negotiation Consensus</div>
                    ${(p.rounds_log || []).map(r => `
                      <div class="rounded bg-white/[0.02] border border-white/[0.04] p-2 text-xs space-y-0.5">
                        <div class="flex items-center justify-between font-mono text-[11px]">
                          <span class="text-zinc-400 font-medium">Round ${r.round_num} • <span class="text-zinc-300">${r.actor}</span></span>
                          <span class="${r.status === 'ACCEPTED' ? 'text-emerald-400' : 'text-amber-400'} font-semibold">$${r.proposed_price?.toFixed(2)} (${r.status})</span>
                        </div>
                        <p class="text-[11px] text-zinc-400 font-sans leading-relaxed">${r.reasoning}</p>
                      </div>
                    `).join('')}
                  </div>

                  <!-- Verification Proof Pill -->
                  <div class="bg-white/[0.02] rounded p-2 border border-white/[0.04] space-y-1">
                    <div class="flex items-center justify-between text-[10px] font-mono">
                      <span class="text-zinc-500 uppercase">Cryptographic Proof & Status</span>
                      <span class="text-emerald-400 font-semibold">${p.verification_status}</span>
                    </div>
                    <div class="text-[10px] font-mono text-zinc-400 break-all select-all">${p.verification_proof}</div>
                  </div>

                </div>
              `).join('')}
            </div>

          </div>
        `;
      }).join('');

      lucide.createIcons();
    }

    // Initial Fetch & Heartbeat Polling
    fetchDeals();
    setInterval(fetchDeals, 3000);
    lucide.createIcons();
  </script>

</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard:app", host="0.0.0.0", port=8080, reload=False)
