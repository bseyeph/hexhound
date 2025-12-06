from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any

from .chains.base import ChainNetworkConfig
from .chains.evm import EvmConnector
from ..models.transfer import Transfer
from ..utils.config import get_rpc_url_for_chain


@dataclass
class TaintGraph:
    nodes: Dict[str, dict]
    edges: List[Transfer]


def _get_evm_network(chain: str) -> ChainNetworkConfig:
    if chain not in ("eth-mainnet", "eth"):
        raise ValueError(f"Unsupported EVM network: {chain}")

    rpc_url = get_rpc_url_for_chain(chain)
    params: Dict[str, Any] = {"rpc_url": rpc_url}
    return ChainNetworkConfig(
        name="eth-mainnet",
        chain_type="evm",
        params=params,
    )


def trace_target(target: str, depth: int = 3, chain: str = "eth-mainnet") -> TaintGraph:
    network = _get_evm_network(chain)
    connector = EvmConnector(network)

    if target.startswith("0x") and len(target) == 66:
        raw = connector.trace_from_tx(target, depth=depth)
    else:
        raw = connector.trace_from_address(target, depth=depth)

    nodes = raw.get("nodes", {})
    edges_raw = raw.get("edges", [])

    edges: List[Transfer] = []
    for e in edges_raw:
        if isinstance(e, Transfer):
            edges.append(e)

    return TaintGraph(nodes=nodes, edges=edges)
