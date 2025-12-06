from __future__ import annotations

from typing import Any, Dict, List
import os
import time
import requests
from requests.exceptions import RequestException, ReadTimeout
from concurrent.futures import ThreadPoolExecutor

from .base import AddressProvider, ChainNetworkConfig
from ...models.transfer import Transfer

ERC20_TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


class EvmRpcProvider(AddressProvider):
    """Pure RPC provider for EVM chains (no explorer API keys required)."""

    def __init__(self, network: ChainNetworkConfig):
        super().__init__(network)

        self.token_cache: dict[str, dict] = {}

        params = network.params
        self.rpc_url: str = params.get("rpc_url", "")
        if not self.rpc_url:
            raise ValueError("rpc_url is required for EvmRpcProvider")

        # Scan window (how many blocks back from latest we look)
        self.scan_window = params.get("scan_window", 100_000)

        env_window = os.getenv("HEXHOUND_SCAN_WINDOW")
        if env_window:
            try:
                self.scan_window = int(env_window)
            except ValueError:
                pass

        # Max per eth_getLogs call (we will also clamp to provider-safe limit)
        self.max_chunk_size = params.get("log_chunk_size", 10_000)

        # Auto-stop controls (stop after X empty chunks in a row)
        self.auto_stop = params.get("auto_stop", True)
        self.auto_stop_chunks = params.get("auto_stop_chunks", 5)

        env_autostop = os.getenv("HEXHOUND_AUTO_STOP")
        if env_autostop == "disabled":
            self.auto_stop = False

    def _eth_call(self, to: str, data: str) -> str | None:
        try:
            res = self._rpc("eth_call", [{"to": to, "data": data}, "latest"])
            return res
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    #                        LOW-LEVEL RPC WRAPPER                       #
    # ------------------------------------------------------------------ #

    def _rpc(self, method: str, params: list[Any]) -> Any:
        """
        Perform a JSON-RPC request with retry + backoff.

        This shields higher-level code from transient network flakiness or
        provider timeouts, which are common with public RPCs.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HexHound/0.1",
        }

        retries = 5
        delay = 0.5  # seconds

        for attempt in range(retries):
            try:
                resp = requests.post(
                    self.rpc_url,
                    json=payload,
                    headers=headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

                if "error" in data:
                    # Hard error from provider: bubble up for caller to handle
                    raise RuntimeError(
                        f"RPC error calling {method} with params {params}: "
                        f"{data['error']}"
                    )

                return data.get("result", None)

            except (ReadTimeout, RequestException) as exc:
                # Last attempt: re-raise
                if attempt == retries - 1:
                    raise

                # Backoff and retry
                time.sleep(delay)
                delay *= 2

        # Should not be reached, but keeps type checkers happy
        return None

    # ------------------------------------------------------------------ #
    #                     HIGH-LEVEL ADDRESS SCANNING                    #
    # ------------------------------------------------------------------ #

    def get_address_transfers(self, address: str, global_pbar=None) -> List[Transfer]:
        """
        Scan ERC20 Transfer events for a given address using eth_getLogs.

        - Walks backward in time over a scan window.
        - Uses two parallel queries per chunk (outgoing + incoming).
        - Respects a hard 10,000-block per-call provider limit.
        - Updates a shared tqdm progress bar if provided.
        """
        address = address.lower()
        transfers: List[Transfer] = []

        # 1) Latest block
        latest_block_hex = self._rpc("eth_blockNumber", [])
        if latest_block_hex is None:
            # If we cannot even get the latest block, bail out cleanly
            return transfers

        latest_block = int(latest_block_hex, 16)

        # 2) Scan window: [start_block, latest_block]
        window = max(1, self.scan_window)
        start_block = max(0, latest_block - window)

        # Topic encoding for the address: right-padded to 32 bytes
        topic_address = "0x" + address[2:].rjust(64, "0")

        # Public nodes like 1rpc typically enforce 10k block limits
        PROVIDER_LIMIT = 10_000

        # Use the smaller of configured and provider-safe limits
        chunk_size = min(self.max_chunk_size, PROVIDER_LIMIT)

        current_end = latest_block
        no_hit_chunks = 0

        # Small thread pool: 2 workers → outgoing + incoming in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            while current_end >= start_block:
                current_start = max(start_block, current_end - chunk_size + 1)
                scanned = current_end - current_start + 1
                if scanned <= 0:
                    break

                from_hex = hex(current_start)
                to_hex = hex(current_end)

                # --- Narrow queries: outgoing and incoming separately ---
                q_from = {
                    "fromBlock": from_hex,
                    "toBlock": to_hex,
                    "topics": [ERC20_TRANSFER_TOPIC, topic_address],
                }
                q_to = {
                    "fromBlock": from_hex,
                    "toBlock": to_hex,
                    "topics": [ERC20_TRANSFER_TOPIC, None, topic_address],
                }

                # Parallel RPC calls; shield each chunk from killing the scan
                future_from = executor.submit(
                    self._rpc, "eth_getLogs", [q_from])
                future_to = executor.submit(self._rpc, "eth_getLogs", [q_to])

                try:
                    logs_from = future_from.result() or []
                except Exception:
                    logs_from = []

                try:
                    logs_to = future_to.result() or []
                except Exception:
                    logs_to = []

                found_logs = len(logs_from) + len(logs_to)

                # Track empty chunks for optional auto-stop
                if found_logs == 0:
                    no_hit_chunks += 1
                else:
                    no_hit_chunks = 0

                if self.auto_stop and no_hit_chunks >= self.auto_stop_chunks:
                    # Quietly stop scanning further back if no activity
                    break

                # --- Parse logs into Transfer objects ---
                for log in logs_from + logs_to:
                    topics = log.get("topics", [])
                    if len(topics) < 3:
                        continue

                    tx_hash = log.get("transactionHash")
                    data_hex = log.get("data", "0x0")

                    try:
                        value = int(data_hex, 16)
                    except (TypeError, ValueError):
                        value = 0

                    token_addr = log.get("address", "").lower()
                    meta = self.get_token_metadata(token_addr)
                    decimals = meta["decimals"]
                    symbol = meta["symbol"]

                    amount_normalized = value / (10 ** decimals)

                    t = Transfer(
                        chain=self.network.name,
                        tx_hash=tx_hash,
                        from_addr=("0x" + topics[1][-40:]).lower(),
                        to_addr=("0x" + topics[2][-40:]).lower(),
                        amount=amount_normalized,
                        token_symbol=symbol,
                        timestamp=0,
                    )
                    transfers.append(t)

                # --- Update global progress bar (if present) ---
                if global_pbar is not None:
                    # IMPORTANT: use explicit None check, because tqdm.__bool__
                    # raises when total is None.
                    global_pbar.update(scanned)

                # Move to previous chunk
                current_end = current_start - 1

        return transfers

    # ------------------------------------------------------------------ #

    def get_token_metadata(self, token_addr: str) -> dict:
        token_addr = token_addr.lower()

        # --- Cached? ---
        if token_addr in self.token_cache:
            return self.token_cache[token_addr]

        # --- Prepare function selectors ---
        # decimals() → 0x313ce567
        # symbol()   → 0x95d89b41
        call_decimals = "0x313ce567"
        call_symbol = "0x95d89b41"

        decimals = 18
        symbol = "ERC20"

        # --- Attempt decimals() ---
        raw_decimals = self._eth_call(token_addr, call_decimals)
        if raw_decimals and raw_decimals != "0x":
            try:
                decimals = int(raw_decimals, 16)
            except Exception:
                decimals = 18

        # --- Attempt symbol() ---
        raw_symbol = self._eth_call(token_addr, call_symbol)
        if raw_symbol and raw_symbol != "0x":
            try:
                # Remove prefix + decode bytes → UTF-8
                hex_bytes = bytes.fromhex(raw_symbol[2:])
                symbol = hex_bytes.decode(
                    'utf-8', errors='ignore').strip("\x00")
                if symbol == "":
                    symbol = "ERC20"
            except Exception:
                symbol = "ERC20"

        # Save cache
        meta = {"symbol": symbol, "decimals": decimals}
        self.token_cache[token_addr] = meta
        return meta

    def get_tx_details(self, tx_hash: str) -> Dict[str, Any]:
        """
        Fetch raw transaction details via eth_getTransactionByHash.
        """
        return self._rpc("eth_getTransactionByHash", [tx_hash]) or {}
