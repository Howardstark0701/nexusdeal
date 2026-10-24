"""
NEXUSDEAL SHARED PROTOCOLS
Shared data models ensuring identical cryptographic schema digests across agents.
"""

from typing import List, Optional
from uagents import Model


class DealRequest(Model):
    deal_id: str
    domain_type: str  # "creator" | "collectibles" | "combo"
    user_query: str
    item_or_creator: str
    initial_offer: float
    max_budget: float
    trade_in_item: Optional[str] = None
    target_video_id: Optional[str] = None


class NegotiationRound(Model):
    round_num: int
    actor: str  # "Buyer", "NexusCreatorAgent", "NexusVaultAgent"
    proposed_price: float
    status: str  # "COUNTER", "ACCEPTED", "REJECTED"
    reasoning: str


class DealProposal(Model):
    deal_id: str
    subagent_domain: str  # "creator" | "collectibles"
    counterparty_name: str
    agreed_price: float
    escrow_locked: bool
    verification_status: str
    verification_proof: str
    rounds_log: List[NegotiationRound]
    summary: str
