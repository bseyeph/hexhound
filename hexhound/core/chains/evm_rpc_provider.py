from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import requests

from .base import AddressProvider, ChainNetworkConfig
from ...models.transfer import Transfer


ERC20_TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


@dataclass
class EvmRpcProvider(AddressProvider):
    """Pure RPC provider for EVM chains (no explorer API keys required)."""

    def __post_init__(self):
        params = self.network.params
        self.rpc_url: str = params.get("rpc_url", "")
        if not self.rpc_url:
            raise ValueError("rpc_url is required for EvmRpcProvider")

    def _rpc(self, method: str, params: list[Any]) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        resp = requests.post(self.rpc_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC error: {data['error']}")
        return data.get("result")

    def get_address_transfers(self, address: str) -> List[Transfer]:
        address = address.lower()
        transfers: List[Transfer] = []

        topic_address = "0x" + address[2:].rjust(64, "0")

        logs_from = self._rpc(
            "eth_getLogs",
            [
                {
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "topics": [ERC20_TRANSFER_TOPIC, topic_address],
                }
            ],
        ) or []

        logs_to = self._rpc(
            "eth_getLogs",
            [
                {
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "topics": [ERC20_TRANSFER_TOPIC, None, topic_address],
                }
            ],
        ) or []

        for log in logs_from + logs_to:
            tx_hash = log["transactionHash"]
            topics = log["topics"]
            data_hex = log.get("data", "0x0")
            try:
                value = int(data_hex, 16)
            except ValueError:
                value = 0

            if len(topics) < 3:
                continue

            from_addr = "0x" + topics[1][-40:]
            to_addr = "0x" + topics[2][-40:]

            transfers.append(
                Transfer(
                    chain=self.network.name,
                    tx_hash=tx_hash,
                    from_addr=from_addr.lower(),
                    to_addr=to_addr.lower(),
                    amount=value / (10**6),  # assume 6 decimals (e.g. USDT)
                    token_symbol="ERC20",
                    timestamp=0,
                )
            )

        return transfers

    def get_tx_details(self, tx_hash: str) -> Dict[str, Any]:
        result = self._rpc("eth_getTransactionByHash", [tx_hash])
        return result or {}
