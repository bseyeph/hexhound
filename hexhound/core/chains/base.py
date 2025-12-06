from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

from ...models.transfer import Transfer


@dataclass
class ChainNetworkConfig:
    name: str
    chain_type: str
    params: Dict[str, Any]


class AddressProvider(ABC):
    def __init__(self, network: ChainNetworkConfig):
        self.network = network

    @abstractmethod
    def get_address_transfers(self, address: str) -> List[Transfer]:
        raise NotImplementedError

    @abstractmethod
    def get_tx_details(self, tx_hash: str) -> Dict[str, Any]:
        raise NotImplementedError


class ChainConnector(ABC):
    def __init__(self, network: ChainNetworkConfig, provider: AddressProvider):
        self.network = network
        self.provider = provider

    @abstractmethod
    def trace_from_address(self, address: str, depth: int = 3) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def trace_from_tx(self, tx_hash: str, depth: int = 3) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def sniff_new_activity(
        self, tainted_addresses: Iterable[str], from_block: int | None = None
    ) -> Dict[str, Any]:
        raise NotImplementedError
