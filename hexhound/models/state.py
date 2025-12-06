from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .transfer import Transfer


@dataclass
class HexHoundState:
    tracked_targets: List[dict] = field(default_factory=list)
    transfers: List[Transfer] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
