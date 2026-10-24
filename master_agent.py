"""
NEXUSDEAL: Master Orchestrator Agent
Assigned: Umair
"""

import os
import uuid
from datetime import datetime, timezone
from uagents import Agent, Context, Model, Protocol
from dotenv import load_dotenv
from protocols import DealRequest, DealProposal

load_dotenv()

# Universal Chat Protocol with strict uagents-core compliance & fallback
try:
    from uagents_core.contrib.protocols.chat import (
        chat_protocol_spec,
        ChatMessage,
        ChatAcknowledgement,
        TextContent,
    )
    chat_proto = Protocol(spec=chat_protocol_spec)
except Exception:
    class TextContent(Model):
        type: str = "text"
        text: str

    class ChatMessage(Model):
        timestamp: str
        msg_id: str
        content: list[TextContent]

    class ChatAcknowledgement(Model):
        timestamp: str
        acknowledged_msg_id: str

    chat_proto = Protocol(name="AgentChatProtocol", version="0.3.0")


def extract_text(msg: ChatMessage) -> str:
    if hasattr(msg, "text") and callable(msg.text):
        return msg.text()
    if hasattr(msg, "content") and msg.content:
        return msg.content[0].text
    return "Execute full combo package with video delivery & collectible custody"


MASTER_PORT = int(os.getenv("MASTER_AGENT_PORT", "8000"))

# NOTE: When mailbox=True is used, do NOT specify local 127.0.0.1 endpoint
# as that would register a localhost IP on the Almanac and break cross-machine discovery on college Wi-Fi.
master = Agent(
    name="NexusDealMaster",
    seed=os.getenv("MASTER_AGENT_SEED", "nexusdeal_master_orchestrator_gcet_2026_seed"),
    port=MASTER_PORT,
    mailbox=True,
    publish_agent_details=True,
)

ACTIVE_DEALS = {}

CREATOR_ADDR = os.getenv("CREATOR_AGENT_ADDRESS", "agent1q2ae2qru6t8aay0f0wepwqgxsnlcr2ynnhfx4w9udnmgxm5gkdv7qvk0ezx")
VAULT_ADDR = os.getenv("VAULT_AGENT_ADDRESS", "agent1qgy29fmge7gqrk04anxr62s2qs54gdv9hfh7y6y585cvvgzsvtvx2fc3et8")


@master.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("==================================================")
    ctx.logger.info("--- UMAIR'S MASTER ORCHESTRATOR ONLINE ---")
    ctx.logger.info(f"📍 Master Address : {master.address}")
    ctx.logger.info(f"🔗 Linked Creator Agent (Vivek)   : {CREATOR_ADDR}")
    ctx.logger.info(f"🔗 Linked Vault Agent (Utkarsh)    : {VAULT_ADDR}")
    ctx.logger.info(f"🌐 Listening Port: {MASTER_PORT} | Mailbox: True")
    ctx.logger.info("==================================================")
    
    # Auto-trigger a startup test ping so logs immediately show activity
    deal_id = f"deal_{os.urandom(2).hex()}"
    ctx.logger.info(f"Dispatching initial sync deal [{deal_id}] to Vault & Creator agents...")
    
    await ctx.send(VAULT_ADDR, DealRequest(
        deal_id=deal_id,
        domain_type="collectibles",
        user_query="Lock Mint Kaido House GT-R Chase",
        item_or_creator="Mint Kaido House GT-R Chase",
        initial_offer=85.0,
        max_budget=120.0,
        trade_in_item="Duplicate Supra"
    ))
    
    await ctx.send(CREATOR_ADDR, DealRequest(
        deal_id=deal_id,
        domain_type="creator",
        user_query="Sponsor TechWithTimMock video",
        item_or_creator="TechWithTimMock",
        initial_offer=180.0,
        max_budget=250.0,
        target_video_id="dQw4w9WgXcQ"
    ))


@master.on_message(model=DealProposal)
async def handle_proposal(ctx: Context, sender: str, msg: DealProposal):
    # FIXED: Access correct DealProposal attributes (agreed_price, verification_status, escrow_locked)
    # instead of nonexistent proposed_price or status
    ctx.logger.info(f"✅ Master received DealProposal for [{msg.deal_id}] from {sender}")
    ctx.logger.info(
        f"   Domain: {msg.subagent_domain} | Status: {msg.verification_status} | "
        f"Agreed Price: ${msg.agreed_price:.2f} | Escrow Locked: {msg.escrow_locked}"
    )
    ctx.logger.info(f"   Proof: {msg.verification_proof}")
    
    deal_dict = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
    ACTIVE_DEALS[msg.deal_id] = deal_dict

    # Sync with dashboard real-time deals_store
    try:
        from deals_store import record_deal
        deal_entry = {
            "deal_id": msg.deal_id,
            "type": msg.subagent_domain,
            "title": f"Negotiated {msg.subagent_domain.title()} Agreement",
            "user_query": msg.summary,
            "status": "ESCROW_SETTLED_AND_LOCKED" if msg.escrow_locked else "IN_NEGOTIATION",
            "subagents": [msg.subagent_domain],
            "proposals": [deal_dict],
            "escrow_locked": msg.escrow_locked,
            "total_agreed": msg.agreed_price,
        }
        record_deal(msg.deal_id, deal_entry)
        ctx.logger.info(f"💾 Synced [{msg.deal_id}] to Dashboard Deals Store")
    except Exception as e:
        ctx.logger.warning(f"Could not sync with deals_store: {e}")


@chat_proto.on_message(model=ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"📨 ChatAcknowledgement received from {sender} for msg {msg.acknowledged_msg_id}")


@chat_proto.on_message(model=ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    iso_now = datetime.now(timezone.utc).isoformat()
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=iso_now,
        acknowledged_msg_id=msg.msg_id
    ))
    
    user_text = extract_text(msg)
    ctx.logger.info(f"💬 Chat Prompt received from {sender}: {user_text}")
    deal_id = f"deal_{os.urandom(2).hex()}"
    
    await ctx.send(VAULT_ADDR, DealRequest(
        deal_id=deal_id,
        domain_type="collectibles",
        user_query=user_text,
        item_or_creator="Mint Kaido House GT-R Chase",
        initial_offer=85.0,
        max_budget=120.0,
        trade_in_item="Duplicate Supra"
    ))
    await ctx.send(CREATOR_ADDR, DealRequest(
        deal_id=deal_id,
        domain_type="creator",
        user_query=user_text,
        item_or_creator="Tech Creator",
        initial_offer=180.0,
        max_budget=250.0,
        target_video_id="dQw4w9WgXcQ"
    ))

    reply = TextContent(text=f"NexusDeal Master dispatched deal [{deal_id}] to Creator & Vault agents.")
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.now(timezone.utc).isoformat(),
        msg_id=str(uuid.uuid4()),
        content=[reply]
    ))


master.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    master.run()
