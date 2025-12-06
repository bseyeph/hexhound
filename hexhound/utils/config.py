from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(os.environ.get("HEXHOUND_HOME", Path.home() / ".hexhound"))
APP_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = APP_DIR / "state.json"
CONFIG_FILE = APP_DIR / "config.toml"

DEFAULT_RPC_ENDPOINTS = {
    "eth-mainnet": "https://cloudflare-eth.com",
    "eth": "https://cloudflare-eth.com",
}


def get_rpc_url_for_chain(chain: str) -> str:
    env_key = f"HEXHOUND_RPC_{chain.replace('-', '_').upper()}"
    env_val = os.environ.get(env_key)
    if env_val:
        return env_val
    return DEFAULT_RPC_ENDPOINTS.get(chain, DEFAULT_RPC_ENDPOINTS["eth-mainnet"])
