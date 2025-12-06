from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, List, Any

from .base import ChainConnector, AddressProvider, ChainNetworkConfig
from .evm_rpc_provider import EvmRpcProvider
from ...models.transfer import Transfer


class EvmConnector(ChainConnector):
    """EVM connector using a pure-RPC provider by default (no API keys)."""

    def __init__(self, network: ChainNetworkConfig, provider: AddressProvider | None = None):
        if provider is None:
            provider = EvmRpcProvider(network)
        super().__init__(network, provider)

    def trace_from_address(self, address: str, depth: int = 3) -> Dict[str, Any]:
        address = address.lower()

        # caching transfers per address
        if not hasattr(self, "_cache"):
            self._cache = {}

        def get_transfers(addr: str):
            if addr in self._cache:
                return self._cache[addr]
            txs = self.provider.get_address_transfers(addr)
            self._cache[addr] = txs
            return txs

        tainted = {address}
        nodes = {address: {"tainted": True, "chain": self.network.name}}
        edges: List[Transfer] = []

        queue: Deque[tuple[str, int]] = deque([(address, 0)])
        visited = set()

        while queue:
            current, level = queue.popleft()

            if level >= depth:
                continue
            if current in visited:
                continue
            visited.add(current)

            transfers = get_transfers(current)

            # NEW: stop deeper traversal if no activity
            if level == 0 and not transfers:
                break  # no need to explore deeper levels at all

            if not transfers:
                continue  # skip deeper hops for empty nodes

            for t in transfers:
                if t.from_addr != current:
                    continue

                edges.append(t)

                if t.to_addr not in nodes:
                    nodes[t.to_addr] = {"tainted": True, "chain": self.network.name}

                if t.to_addr not in tainted:
                    tainted.add(t.to_addr)
                    queue.append((t.to_addr, level + 1))

        return {"nodes": nodes, "edges": edges}


    def trace_from_tx(self, tx_hash: str, depth: int = 3) -> Dict[str, Any]:
        raw_tx = self.provider.get_tx_details(tx_hash)
        to_addr = raw_tx.get("to")
        if not to_addr:
            raise ValueError("Could not determine 'to' address for the given tx.")
        return self.trace_from_address(to_addr, depth=depth)

    def sniff_new_activity(
        self, tainted_addresses: Iterable[str], from_block: int | None = None
    ) -> Dict[str, Any]:
        return {"nodes": {}, "edges": []}
