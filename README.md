# 🐺 HexHound

HexHound is a blockchain forensics toolkit for tracing tainted funds across wallets in real time.  
It provides both:

- A **powerful CLI** (with a Metasploit-style interactive shell)
- A **local Flask API + React/Tailwind UI**
- **API-key-free EVM tracing** using pure RPC calls
- A pluggable architecture for multi-chain support (Bitcoin, Tron, Solana, etc.)

HexHound is designed for investigators, incident responders, analysts, and victims of crypto fraud who need to track fund movement *as it happens*.

---

## ✨ Features

### 🔍 Taint Tracing Engine
- Trace ETH & ERC-20 flows from any wallet or transaction hash  
- Build a multi-hop taint graph (user-configurable depth)  
- Follows funds through arbitrarily deep chains of transfers  
- Extracts ERC-20 `Transfer` events from on-chain logs (no explorer APIs)

### 🛰 Sniff Mode (Live Monitoring)
- Continuously scan new blocks for activity touching tracked addresses  
- Update a live taint graph as funds move  
- Ideal for scam recovery and forensic investigations

### 🐺 Interactive Shell (Metasploit-style)

Run:

```bash
hexhound
```

You’ll get:

```
 _   _          _   _
| | | | ___  __| | | |__
| |_| |/ _ \/ _` | | '_ \
|  _  |  __/ (_| | | | | |
|_| |_|\___|\__,_| |_| |_|

            H E X H O U N D

HexHound v0.1.0 — type 'help' to list commands.
HexHound >
```

Supported commands include:

```
add eth-mainnet 0xabc...
set depth 4
run trace
sniff on
ui
list
version
```

---

## 🖥 UI Dashboard

- Next-gen React + Tailwind interface  
- Displays taint graphs (placeholder now, full graph view coming next)
- Local backend served via Flask

Start UI:

```bash
hexhound ui
```

Default: <http://localhost:8765>

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

## 🚀 Installation (Development)

### 1. Install Python dependencies

```bash
poetry install
```

### 2. Install UI dependencies

```bash
cd ui
npm install
npm run build
cd ..
```

Copy build output into the Python package:

```bash
rm -rf hexhound/ui
mkdir -p hexhound/ui
cp -r ui/dist/* hexhound/ui/
```

---

## 🧪 Usage

### CLI (non-interactive)

```bash
hexhound trace 0xWallet --depth 3
```

### Interactive Shell

```bash
hexhound
```

### Launch UI

```bash
hexhound ui --port 8765
```

---

## 🔧 Configuration

HexHound uses pure RPC.  
Default RPC endpoint:

```
https://cloudflare-eth.com
```

Override via environment variable:

```bash
export HEXHOUND_RPC_ETH_MAINNET="https://your-node-endpoint"
```

---

## 📦 Running Tests

```bash
poetry run pytest
```

---

## 🔄 CI/CD

GitHub Actions workflow includes:

- Setup Python  
- Poetry install  
- Run test suite  

---

## 🛣 Roadmap

### v0.2 – Native ETH tracing + timestamps  
### v0.3 – Sniff mode (live updates)  
### v0.4 – Graph rendering in UI  
### v0.5 – Bitcoin UTXO tracing  
### v0.6 – Tron & Solana connectors  
### v1.0 – Case management + exportable reports  

---

## 👤 License

MIT License.

---

## 🤝 Contributing

PRs welcome!
