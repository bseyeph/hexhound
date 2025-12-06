from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from tqdm import tqdm

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


# ---------------------------------------------------------------------------
# Token symbol normalization / flagging
# ---------------------------------------------------------------------------

def normalize_symbol(raw: str) -> Tuple[str, List[str]]:
    """
    Normalize a raw token symbol into a cleaner display form and
    return (clean_symbol, flags).

    We do NOT throw away the raw symbol; this is purely for UX + heuristic hints.
    """
    flags: List[str] = []

    if raw is None:
        return "UNKNOWN", ["missing_symbol"]

    # Basic trim
    s = str(raw).strip()
    if not s:
        return "UNKNOWN", ["empty_symbol"]

    lower = s.lower()

    # Heuristic flags
    if any(word in lower for word in ("visit", "website", "claim", "reward", "bonus", "airdrop", "yield")):
        flags.append("phishing_text")

    if "http://" in lower or "https://" in lower or ".io" in lower or ".com" in lower:
        flags.append("url_like")

    if len(s) > 20:
        flags.append("overlong_symbol")

    if " " in s and len(s) > 10:
        flags.append("suspicious_spaces")

    if any(ord(ch) > 127 for ch in s):
        flags.append("non_ascii")

    # Choose a clean display symbol
    clean = s
    if "phishing_text" in flags or "url_like" in flags:
        # Collapse obvious scam-banner symbols into a generic label
        clean = "SCAM-TOKEN"
    elif len(s) > 16:
        clean = s[:16] + "…"

    return clean, flags


def format_amount(amount: float) -> str:
    """
    Compact human formatting: 1234 -> '1.234K', 1_000_000 -> '1.000M', etc.
    """
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.3f}B"
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.3f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.3f}K"
    return f"{amount:.2f}"


# ---------------------------------------------------------------------------
# Main trace
# ---------------------------------------------------------------------------

def trace_target(target: str, depth: int = 3, chain: str = "eth-mainnet") -> TaintGraph:
    network = _get_evm_network(chain)
    connector = EvmConnector(network)

    global_pbar = tqdm(
        desc="HexHound Total Scan Progress",
        unit="blocks",
        dynamic_ncols=True,
        total=None,
        mininterval=0.25,
    )

    visited = set()
    queue = [(target, 1)]
    all_edges: List[Transfer] = []
    nodes: Dict[str, dict] = {}

    root_lower = target.lower()

    while queue:
        address, current_depth = queue.pop(0)

        if address in visited:
            continue
        visited.add(address)

        tqdm.write(f"[Depth {current_depth}] scanning {address}")

        transfers = connector.provider.get_address_transfers(
            address,
            global_pbar=global_pbar,
        )

        # record transfers
        for t in transfers:
            all_edges.append(t)
            nodes[t.from_addr] = {}
            nodes[t.to_addr] = {}

        # expand to next depth
        if current_depth < depth:
            children = {t.from_addr for t in transfers} | {
                t.to_addr for t in transfers}
            for child in children:
                if child not in visited:
                    queue.append((child, current_depth + 1))

    # Build token-aware, normalized summary
    summary = summarize_transfers_token_aware(all_edges, root_lower)

    tqdm.write("\n=== Token-Aware Trace Summary ===\n")

    tqdm.write(f"Unique addresses involved: {summary['unique_addresses']}\n")

    tqdm.write("Inbound totals:")
    for sym_info in summary["inbound_totals"]:
        clean = sym_info["clean_symbol"]
        raw = sym_info["raw_symbol"]
        amt = sym_info["amount"]
        flags = sym_info["flags"]
        display = clean
        if flags:
            display += f"  (raw: {raw})"
        tqdm.write(f"  ← {format_amount(amt):>7}  {display}")

    tqdm.write("\nOutbound totals:")
    for sym_info in summary["outbound_totals"]:
        clean = sym_info["clean_symbol"]
        raw = sym_info["raw_symbol"]
        amt = sym_info["amount"]
        flags = sym_info["flags"]
        display = clean
        if flags:
            display += f"  (raw: {raw})"
        tqdm.write(f"  → {format_amount(amt):>7}  {display}")

    tqdm.write("\nTop inbound sources by token:")
    for token_entry in summary["top_inbound_by_token"]:
        clean = token_entry["clean_symbol"]
        raw = token_entry["raw_symbol"]
        flags = token_entry["flags"]
        header = clean
        if flags:
            header += f"  (raw: {raw})"
        tqdm.write(f"   {header}:")
        for addr, amt in token_entry["top_sources"]:
            tqdm.write(f"     {addr} — {format_amount(amt):>7}  {clean}")

    tqdm.write("\nTop outbound destinations by token:")
    for token_entry in summary["top_outbound_by_token"]:
        clean = token_entry["clean_symbol"]
        raw = token_entry["raw_symbol"]
        flags = token_entry["flags"]
        header = clean
        if flags:
            header += f"  (raw: {raw})"
        tqdm.write(f"   {header}:")
        for addr, amt in token_entry["top_dests"]:
            tqdm.write(f"     {addr} → {format_amount(amt):>7}  {clean}")

    # New: list token anomalies / suspicious symbols explicitly
    if summary["anomalous_tokens"]:
        tqdm.write("\nToken anomalies / suspicious symbols:")
        for entry in summary["anomalous_tokens"]:
            clean = entry["clean_symbol"]
            raw = entry["raw_symbol"]
            flags = ", ".join(entry["flags"])
            tqdm.write(f"  {clean}  (raw: {raw}) — flags: {flags}")

    global_pbar.close()
    return TaintGraph(nodes=nodes, edges=all_edges)


# ---------------------------------------------------------------------------
# Token-aware summary
# ---------------------------------------------------------------------------

def summarize_transfers_token_aware(transfers: List[Transfer], root: str) -> Dict[str, Any]:
    """
    Build a token-aware summary while preserving raw symbols and
    attaching normalization/flags.
    """
    # address -> token -> amount
    inbound_by_addr_token: Dict[str, Dict[str, float]
                                ] = defaultdict(lambda: defaultdict(float))
    outbound_by_addr_token: Dict[str, Dict[str, float]] = defaultdict(
        lambda: defaultdict(float))

    # token symbol -> { 'clean_symbol', 'flags' }
    token_meta: Dict[str, Dict[str, Any]] = {}

    for t in transfers:
        raw_symbol = t.token_symbol or "UNKNOWN"
        if raw_symbol not in token_meta:
            clean, flags = normalize_symbol(raw_symbol)
            token_meta[raw_symbol] = {
                "clean_symbol": clean,
                "flags": flags,
            }

        amt = t.amount or 0.0

        outbound_by_addr_token[t.from_addr][raw_symbol] += amt
        inbound_by_addr_token[t.to_addr][raw_symbol] += amt

    # Root-level inbound / outbound totals grouped by raw symbol
    inbound_root = inbound_by_addr_token.get(root, {})
    outbound_root = outbound_by_addr_token.get(root, {})

    def totals_list(symbol_map: Dict[str, float]):
        entries = []
        for raw_symbol, amount in symbol_map.items():
            meta = token_meta.get(
                raw_symbol, {"clean_symbol": raw_symbol, "flags": []})
            entries.append({
                "raw_symbol": raw_symbol,
                "clean_symbol": meta["clean_symbol"],
                "flags": meta["flags"],
                "amount": amount,
            })
        # Sort largest amounts first
        entries.sort(key=lambda e: e["amount"], reverse=True)
        return entries

    inbound_totals = totals_list(inbound_root)
    outbound_totals = totals_list(outbound_root)

    # Top inbound / outbound by token across the whole graph
    top_inbound_by_token = []
    top_outbound_by_token = []

    for raw_symbol, meta in token_meta.items():
        # inbound: who sends this token to root / generally?
        inbound_agg: Dict[str, float] = defaultdict(float)
        outbound_agg: Dict[str, float] = defaultdict(float)

        for addr, tokens in inbound_by_addr_token.items():
            amt = tokens.get(raw_symbol, 0.0)
            if amt > 0:
                inbound_agg[addr] += amt

        for addr, tokens in outbound_by_addr_token.items():
            amt = tokens.get(raw_symbol, 0.0)
            if amt > 0:
                outbound_agg[addr] += amt

        if inbound_agg:
            sources = sorted(inbound_agg.items(),
                             key=lambda x: x[1], reverse=True)[:5]
            top_inbound_by_token.append({
                "raw_symbol": raw_symbol,
                "clean_symbol": meta["clean_symbol"],
                "flags": meta["flags"],
                "top_sources": sources,
            })

        if outbound_agg:
            dests = sorted(outbound_agg.items(),
                           key=lambda x: x[1], reverse=True)[:5]
            top_outbound_by_token.append({
                "raw_symbol": raw_symbol,
                "clean_symbol": meta["clean_symbol"],
                "flags": meta["flags"],
                "top_dests": dests,
            })

    # Sort token sections by total amount seen overall
    def token_total_amount(raw_symbol: str) -> float:
        total = 0.0
        for tokens in inbound_by_addr_token.values():
            total += tokens.get(raw_symbol, 0.0)
        for tokens in outbound_by_addr_token.values():
            total += tokens.get(raw_symbol, 0.0)
        return total

    top_inbound_by_token.sort(
        key=lambda e: token_total_amount(e["raw_symbol"]),
        reverse=True,
    )
    top_outbound_by_token.sort(
        key=lambda e: token_total_amount(e["raw_symbol"]),
        reverse=True,
    )

    # Collect anomalous / suspicious tokens (any with flags)
    anomalous_tokens = []
    for raw_symbol, meta in token_meta.items():
        if meta["flags"]:
            anomalous_tokens.append({
                "raw_symbol": raw_symbol,
                "clean_symbol": meta["clean_symbol"],
                "flags": meta["flags"],
            })

    # Unique addresses
    unique_addresses = len({t.from_addr for t in transfers} | {
                           t.to_addr for t in transfers})

    return {
        "unique_addresses": unique_addresses,
        "inbound_totals": inbound_totals,
        "outbound_totals": outbound_totals,
        "top_inbound_by_token": top_inbound_by_token,
        "top_outbound_by_token": top_outbound_by_token,
        "anomalous_tokens": anomalous_tokens,
    }
