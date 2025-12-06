# 🐺 HexHound — Blockchain Forensics & Scam Investigation Toolkit

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img src="https://github.com/bseyeph/hexhound/actions/workflows/ci.yml/badge.svg" />
  <img src="https://img.shields.io/badge/status-alpha-orange" />
  <img src="https://img.shields.io/badge/packaging-poetry-blue" />
  <img src="https://img.shields.io/badge/frontend-react-61DAFB?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/styling-tailwindcss-38bdf8?logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/backend-flask-000000?logo=flask&logoColor=white" />
</p>

HexHound is a **high-performance blockchain forensics engine** built for investigators, analysts, and victims of crypto fraud. It performs **taint tracing**, **live monitoring**, and **token-aware analysis** using pure RPC calls — **no API keys and no rate-limited explorer dependencies**.

HexHound is designed for:

- Scam / fraud recovery responders  
- Internal incident response teams  
- OSINT & DFIR analysts  
- Law enforcement digital investigators  
- Victims seeking transparent tracking of stolen funds  

---

## ✨ Key Capabilities

### 🔍 Taint Tracing Engine (High-Speed, Multi-Hop)
- Trace ETH & ERC-20 flows from any wallet  
- Multi-hop taint traversal (user-defined depth)  
- **Adaptive chunking** for extremely fast log scanning  
- **Parallel RPC execution** for high throughput  
- Graph-style output (nodes + edges)  
- Timestamps coming soon  

### 🧪 Token-Aware Forensics (New)
- Treats each token independently (USDT, stablecoin variants, phishing tokens, dust tokens, etc.)  
- **Symbol normalization** and **scam-token flagging**  
- Detects:
  - Unicode-obfuscated symbols  
  - Tokens containing phishing text  
  - Overlong scam-banner names  
  - URL-like symbols  
- Produces a clean, analyst-friendly report with inbound/outbound totals and top senders/receivers.

### 🛰 Sniff Mode (Live Monitoring)
- Watches the chain for updates to tracked wallets  
- Emits new transfers in real time  

### 🐺 Interactive Shell
A Metasploit-style UI:

```
hexhound
```

```
add eth-mainnet 0xabc...
set depth 4
run trace
sniff on
ui
list
version
```

### 🖥 Local UI Dashboard
- React + Tailwind  
- Flask backend  
- Interactive graph view (coming soon)

---

## 🧱 Project Structure

```
hexhound/
 ├── cli.py
 ├── cli_shell.py
 ├── core/
 │    ├── chains/
 │    ├── taint_engine.py
 ├── models/
 ├── server/
 ├── utils/
 ├── ui/
 └── README.md
```

---

## 🚀 Installation

### Install Python dependencies
```bash
poetry install
```

### Build UI
```bash
cd ui
npm install
npm run build
cd ..
```

Copy build output:
```bash
rm -rf hexhound/ui
mkdir -p hexhound/ui
cp -r ui/dist/* hexhound/ui/
```

---

## 🧪 Usage

### Trace a wallet
```bash
hexhound trace 0xWallet --depth 3
```

### Interactive shell
```bash
hexhound
```

### Launch UI
```bash
hexhound ui --port 8765
```

---

## 🔧 Configuration

Default RPC:
```
https://cloudflare-eth.com
```

Override:
```bash
export HEXHOUND_RPC_ETH_MAINNET="https://your-node-endpoint"
```

---

## 📦 Tests
```bash
poetry run pytest
```

---

## 🛣 Roadmap

### v0.2 — timestamps  
### v0.3 — full sniff mode  
### v0.4 — graph rendering UI  
### v0.5 — Bitcoin UTXO  
### v0.6 — Tron & Solana  
### v1.0 — case management + reports  

---

## License
MIT License.
