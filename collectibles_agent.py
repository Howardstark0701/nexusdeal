"""
NEXUSDEAL: Sub-Agent B - Collectibles Vault Agent
Assigned: Utkarsh
"""

import os
from dotenv import load_dotenv
from uagents import Agent, Context
from protocols import DealRequest, DealProposal, NegotiationRound

load_dotenv()

VAULT_SEED = os.getenv("VAULT_AGENT_SEED", "nexusdeal_collectibles_vault_gcet_2026_seed")

vault_agent = Agent(
    name="NexusVaultAgent",
    seed=VAULT_SEED,
    port=8002,
    mailbox=True,
    publish_agent_details=True,
)

# Mock Vault Inventory
VAULT_INVENTORY = {
    "GTR_CHASE": {
        "name": "Nissan Skyline GT-R R34 (Chase Spec)",
        "base_price": 110.0,
        "reserve_price": 85.0,
        "sku": "VAULT-SKU-GTR-CHASE-7721",
    },
    "SUPRA_MK4": {
        "name": "Toyota Supra MK4 Turbo (Mint in Acrylic Case)",
        "base_price": 95.0,
        "reserve_price": 70.0,
        "sku": "VAULT-SKU-SUPRA-MK4-9042",
    },
}


def lookup_inventory(query: str):
    q = query.upper()
    if "SUPRA" in q:
        return VAULT_INVENTORY["SUPRA_MK4"]
    # Default to GTR_CHASE or exact match
    for k, v in VAULT_INVENTORY.items():
        if k in q:
            return v
    return VAULT_INVENTORY["GTR_CHASE"]


@vault_agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info("==================================================")
    ctx.logger.info(">> NexusVaultAgent (Assigned: Utkarsh) Online!")
    ctx.logger.info(f"[*] Agent Address : {vault_agent.address}")
    ctx.logger.info(f"[*] Listening Port : 8002 | Mailbox: True")
    ctx.logger.info("==================================================")


@vault_agent.on_message(model=DealRequest)
async def handle_deal_request(ctx: Context, sender: str, msg: DealRequest):
    ctx.logger.info(f"[IN] Received DealRequest [{msg.deal_id}] from {sender}")
    ctx.logger.info(f"[ITEM] Item: {msg.item_or_creator} | Initial: ${msg.initial_offer} | Trade-in: {msg.trade_in_item}")

    item = lookup_inventory(msg.item_or_creator)
    trade_in_discount = 25.0 if msg.trade_in_item and msg.trade_in_item.strip() else 0.0
    effective_reserve = max(20.0, item["reserve_price"] - trade_in_discount)
    effective_base = max(effective_reserve, item["base_price"] - trade_in_discount)

    rounds_log: list[NegotiationRound] = []

    # Round 1: Counter initial offer with inventory base price taking trade-in into account
    r1_reason = f"Base listing is ${item['base_price']:.2f}."
    if trade_in_discount > 0:
        r1_reason += f" Applied $25.00 trade-in credit for '{msg.trade_in_item}'."
    r1_reason += f" Countering at ${effective_base:.2f}."

    rounds_log.append(
        NegotiationRound(
            round_num=1,
            actor="NexusVaultAgent",
            proposed_price=round(effective_base, 2),
            status="COUNTER",
            reasoning=r1_reason,
        )
    )

    # Round 2: Final settlement against reserve price
    if msg.max_budget < effective_reserve:
        final_price = effective_reserve
        r2_status = "COUNTER"
        r2_reason = f"Floor reserve price after trade-in credit is locked at ${effective_reserve:.2f}."
    else:
        # Settle competitively between buyer max budget and reserve
        target_settle = (effective_reserve + min(msg.max_budget, effective_base)) / 2.0
        final_price = round(max(effective_reserve, target_settle), 2)
        r2_status = "ACCEPTED"
        r2_reason = f"Vault algorithm accepted ${final_price:.2f} settlement. Reserve met & trade-in verified."

    rounds_log.append(
        NegotiationRound(
            round_num=2,
            actor="NexusVaultAgent",
            proposed_price=final_price,
            status=r2_status,
            reasoning=r2_reason,
        )
    )

    # Generate Vault SKU proof & asset lock
    verification_proof = (
        f"VAULT_CUSTODY_LOCK: SKU={item['sku']} | RFID=RFID-9812-SEALED | "
        f"TRADE_IN_CREDIT={'$25_APPLIED' if trade_in_discount > 0 else 'NONE'} | "
        f"ESCROW_CONDITION=CUSTODY_VERIFIED"
    )
    ctx.logger.info(f"[LOCK] Vault Asset Locked: {verification_proof}")

    proposal = DealProposal(
        deal_id=msg.deal_id,
        subagent_domain="collectibles",
        counterparty_name=f"NexusVault Custody ({item['name']})",
        agreed_price=final_price,
        escrow_locked=True,
        verification_status="VAULT_ASSET_LOCKED",
        verification_proof=verification_proof,
        rounds_log=rounds_log,
        summary=f"Vault asset '{item['name']}' locked at ${final_price:.2f} (Trade-in credit: ${trade_in_discount:.2f}). Escrow confirmed.",
    )

    ctx.logger.info(f"[OUT] Sending DealProposal [{msg.deal_id}] back to Master: agreed=${final_price}")
    await ctx.send(sender, proposal)


if __name__ == "__main__":
    vault_agent.run()
