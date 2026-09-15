"""Runtime configuration. All network I/O targets Bitcoin Testnet4."""
from __future__ import annotations
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRETS_DIR = Path(os.getenv("BTC_LAB_SECRETS_DIR", PROJECT_ROOT / ".secrets"))
WALLET_PATH = SECRETS_DIR / "wallet.json"
ESPLORA_URL = os.getenv("BTC_LAB_ESPLORA_URL", "https://mempool.space/testnet4/api").rstrip("/")
# python-bitcoinlib 0.12.2 has no distinct Testnet4 parameter set. Legacy
# Testnet4 P2PKH/P2SH addresses and WIFs intentionally reuse Testnet3 prefixes,
# so local address/script serialization remains on its "testnet" parameters.
BITCOINLIB_NETWORK = "testnet"
NETWORK = "testnet4"
DEFAULT_FEE_RATE = int(os.getenv("BTC_LAB_FEE_RATE", "2"))
DUST_LIMIT = 546
REQUEST_TIMEOUT = float(os.getenv("BTC_LAB_HTTP_TIMEOUT", "20"))
POLL_SECONDS = float(os.getenv("BTC_LAB_POLL_SECONDS", "15"))
if DEFAULT_FEE_RATE < 1:
    raise ValueError("BTC_LAB_FEE_RATE must be at least 1 sat/vB")
