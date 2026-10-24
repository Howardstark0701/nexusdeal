"""
NEXUSDEAL: Shared Real-Time In-Memory & File-Backed Deals Store
Synchronizes active deals between Master Agent and Dashboard Server.
"""

import json
import os
from typing import Dict, Any, List

DEALS_FILE = os.path.join(os.path.dirname(__file__), "deals.json")
ACTIVE_DEALS: Dict[str, Any] = {}


def load_deals() -> Dict[str, Any]:
    global ACTIVE_DEALS
    if os.path.exists(DEALS_FILE):
        try:
            with open(DEALS_FILE, "r") as f:
                data = json.load(f)
                ACTIVE_DEALS.update(data)
        except Exception:
            pass
    return ACTIVE_DEALS


def record_deal(deal_id: str, deal_data: dict):
    global ACTIVE_DEALS
    ACTIVE_DEALS[deal_id] = deal_data
    try:
        with open(DEALS_FILE, "w") as f:
            json.dump(ACTIVE_DEALS, f, indent=2)
    except Exception:
        pass


def get_all_deals() -> List[dict]:
    load_deals()
    return list(ACTIVE_DEALS.values())
