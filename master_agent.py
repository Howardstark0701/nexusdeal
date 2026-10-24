"""
NEXUSDEAL: Master Orchestrator Agent
Assigned: Umair
"""

import os
import uuid
from typing import Dict, Any
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
)
from protocols import DealRequest, DealProposal
from deals_store import record_deal, ACTIVE_DEALS

load_dotenv()

MASTER_SEED = os.getenv("MASTER_AGENT_SEED", "nexusdeal_master_orchestrator_gcet_2026_seed")
CREATOR_AGENT_ADDRESS = os.getenv(
    "CREATOR_AGENT_ADDRESS",
    "agent1q2ae2qru6t8aay0f0wepwqgxsnlcr2ynnhfx4w9udnmgxm5gkdv7qvk0ezx",
)
VAULT_AGENT_ADDRESS = os.getenv(
    "VAULT_AGENT_ADDRESS",
    "agent1qgy29fmge7gqrk04anxr62s2qs54gdv9hfh7y6y585cvvgzsvtvx2fc3et8",
)

master_agent = Agent(
    name="NexusDealMaster",
    seed=MASTER_SEED,
    port=8000,
    mailbox=True,
    publish_agent_details=True,
)

# Register AgentChatProtocol (v0.3.0)
chat_proto = Protocol(spec=chat_protocol_spec)


@chat_proto.on_message(model=ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"📨 ChatAcknowledgement received from {sender} for msg {msg.acknowledged_msg_id}")


@chat_proto.on_message(model=ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    user_prompt = msg.text()
    ctx.logger.info(f"💬 ChatMessage from {sender}: '{user_prompt}'")

    # Acknowledge receipt to the sender
    await ctx.send(
        sender,
        ChatAcknowledgement(acknowledged_msg_id=msg.msg_id),
    )

    query = user_prompt.lower()
    deal_id = f"DEAL-{uuid.uuid4().hex[:8].upper()}"

    # Determine intent & route to appropriate subagents
    is_creator = any(k in query for k in ["creator", "youtube", "cpm", "sponsorship", "video"])
    is_vault = any(k in query for k in ["vault", "collectible", "gtr", "supra", "car", "model", "trade"])
    
    # If neither specifically mentioned or both mentioned, treat as combo drop
    if (is_creator and is_vault) or (not is_creator and not is_vault):
        await dispatch_combo_deal(ctx, deal_id, user_prompt, sender)
    elif is_creator:
        await dispatch_creator_deal(ctx, deal_id, user_prompt, sender)
    elif is_vault:
        await dispatch_vault_deal(ctx, deal_id, user_prompt, sender)


async def dispatch_creator_deal(ctx: Context, deal_id: str, query: str, user_address: str):
    req = DealRequest(
        deal_id=deal_id,
        domain_type="creator",
        user_query=query,
        item_or_creator="TechSprint Daily (50k Avg Views)",
        initial_offer=180.0,
        max_budget=250.0,
        target_video_id="dQw4w9WgXcQ",
    )
    deal_entry = {
        "deal_id": deal_id,
        "type": "creator",
        "title": "Creator Sponsorship Negotiation",
        "user_query": query,
        "status": "IN_NEGOTIATION",
        "subagents": ["NexusCreatorAgent"],
        "proposals": [],
        "escrow_locked": False,
        "total_agreed": 0.0,
    }
    record_deal(deal_id, deal_entry)
    ctx.logger.info(f"🚀 Dispatched Creator DealRequest [{deal_id}] to {CREATOR_AGENT_ADDRESS}")
    await ctx.send(CREATOR_AGENT_ADDRESS, req)


async def dispatch_vault_deal(ctx: Context, deal_id: str, query: str, user_address: str):
    req = DealRequest(
        deal_id=deal_id,
        domain_type="collectibles",
        user_query=query,
        item_or_creator="GTR_CHASE",
        initial_offer=75.0,
        max_budget=100.0,
        trade_in_item="Hot Wheels Skyline R32",
    )
    deal_entry = {
        "deal_id": deal_id,
        "type": "collectibles",
        "title": "Collectibles Vault Asset Lock",
        "user_query": query,
        "status": "IN_NEGOTIATION",
        "subagents": ["NexusVaultAgent"],
        "proposals": [],
        "escrow_locked": False,
        "total_agreed": 0.0,
    }
    record_deal(deal_id, deal_entry)
    ctx.logger.info(f"🚀 Dispatched Vault DealRequest [{deal_id}] to {VAULT_AGENT_ADDRESS}")
    await ctx.send(VAULT_AGENT_ADDRESS, req)


async def dispatch_combo_deal(ctx: Context, deal_id: str, query: str, user_address: str):
    deal_entry = {
        "deal_id": deal_id,
        "type": "combo",
        "title": "Full Drop + Sponsorship Combo",
        "user_query": query,
        "status": "IN_NEGOTIATION",
        "subagents": ["NexusCreatorAgent", "NexusVaultAgent"],
        "proposals": [],
        "escrow_locked": False,
        "total_agreed": 0.0,
    }
    record_deal(deal_id, deal_entry)

    req_creator = DealRequest(
        deal_id=deal_id,
        domain_type="combo",
        user_query=query,
        item_or_creator="TechSprint Daily (50k Avg Views)",
        initial_offer=180.0,
        max_budget=230.0,
        target_video_id="dQw4w9WgXcQ",
    )
    req_vault = DealRequest(
        deal_id=deal_id,
        domain_type="combo",
        user_query=query,
        item_or_creator="GTR_CHASE",
        initial_offer=80.0,
        max_budget=105.0,
        trade_in_item="Hot Wheels Skyline R32",
    )

    ctx.logger.info(f"🚀 Dispatched Combo Deal [{deal_id}] to Creator ({CREATOR_AGENT_ADDRESS}) and Vault ({VAULT_AGENT_ADDRESS})")
    await ctx.send(CREATOR_AGENT_ADDRESS, req_creator)
    await ctx.send(VAULT_AGENT_ADDRESS, req_vault)


@master_agent.on_message(model=DealProposal)
async def handle_deal_proposal(ctx: Context, sender: str, msg: DealProposal):
    ctx.logger.info("==================================================")
    ctx.logger.info(f"🤝 DealProposal Received for Deal [{msg.deal_id}] from {sender}")
    ctx.logger.info(f"Domain: {msg.subagent_domain} | Counterparty: {msg.counterparty_name}")
    ctx.logger.info(f"Agreed Price: ${msg.agreed_price:.2f} | Status: {msg.verification_status}")
    ctx.logger.info(f"Proof: {msg.verification_proof}")
    ctx.logger.info("==================================================")

    deal = ACTIVE_DEALS.get(msg.deal_id, {
        "deal_id": msg.deal_id,
        "type": msg.subagent_domain,
        "title": f"NexusDeal {msg.subagent_domain.title()}",
        "status": "IN_NEGOTIATION",
        "subagents": [],
        "proposals": [],
        "escrow_locked": False,
        "total_agreed": 0.0,
    })

    # Append proposal details
    deal["proposals"].append(msg.dict())
    deal["total_agreed"] = round(sum(p["agreed_price"] for p in deal["proposals"]), 2)

    # Check completion condition
    expected_subagents = 2 if deal.get("type") == "combo" else 1
    if len(deal["proposals"]) >= expected_subagents:
        deal["status"] = "ESCROW_SETTLED_AND_LOCKED"
        deal["escrow_locked"] = True
        ctx.logger.info(f"🔒 ESCROW SETTLED! Total Deal Value: ${deal['total_agreed']:.2f}. All proofs cryptographic & locked.")
    else:
        deal["status"] = "PARTIALLY_SETTLED"

    record_deal(msg.deal_id, deal)


@master_agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info("==================================================")
    ctx.logger.info("👑 NexusDealMaster (Assigned: Umair) Online!")
    ctx.logger.info(f"📍 Agent Address : {master_agent.address}")
    ctx.logger.info(f"🌐 Listening Port : 8000 | Mailbox: True")
    ctx.logger.info(f"Creator Agent Addr: {CREATOR_AGENT_ADDRESS}")
    ctx.logger.info(f"Vault Agent Addr  : {VAULT_AGENT_ADDRESS}")
    ctx.logger.info("==================================================")


# Attach Chat Protocol to Master Agent
master_agent.include(chat_proto)


if __name__ == "__main__":
    master_agent.run()
