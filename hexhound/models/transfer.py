from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transfer:
    chain: str
    tx_hash: str
    from_addr: str
    to_addr: str
    amount: float
    token_symbol: str
    timestamp: int
