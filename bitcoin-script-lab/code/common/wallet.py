"""Testnet key generation and local persistence."""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from .bitcoin_compat import prepare_python_bitcoinlib
prepare_python_bitcoinlib()
import bitcoin  # noqa: E402
from bitcoin.core.script import CScript, OP_2, OP_CHECKMULTISIG  # noqa: E402
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress, P2SHBitcoinAddress  # noqa: E402
from .config import BITCOINLIB_NETWORK, NETWORK, WALLET_PATH
bitcoin.SelectParams(BITCOINLIB_NETWORK)

def _new_secret() -> CBitcoinSecret:
    return CBitcoinSecret.from_secret_bytes(os.urandom(32), compressed=True)

def _key_record(secret: CBitcoinSecret) -> dict[str, str]:
    public_key = bytes(secret.pub)
    return {"wif": str(secret), "public_key": public_key.hex(), "address": str(P2PKHBitcoinAddress.from_pubkey(public_key))}

def generate_p2pkh_record() -> dict[str, Any]:
    return {"network": NETWORK, "kind": "p2pkh", "key": _key_record(_new_secret())}

def generate_multisig_record() -> dict[str, Any]:
    keys = [_new_secret(), _new_secret()]
    redeem_script = CScript([OP_2, bytes(keys[0].pub), bytes(keys[1].pub), OP_2, OP_CHECKMULTISIG])
    return {"network": NETWORK, "kind": "p2sh-2of2", "keys": [_key_record(key) for key in keys], "redeem_script": bytes(redeem_script).hex(), "address": str(P2SHBitcoinAddress.from_redeemScript(redeem_script))}

def load_wallet(path: Path = WALLET_PATH) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "network": NETWORK}
    data = json.loads(path.read_text(encoding="utf-8"))
    # Testnet3 and Testnet4 share legacy address/WIF version bytes. Existing
    # unfunded keys can therefore be migrated without replacing private keys.
    if data.get("network") == "testnet":
        data["network"] = NETWORK
        for task in (data.get("task1"), data.get("task2")):
            if isinstance(task, dict):
                task["network"] = NETWORK
        save_wallet(data, path)
    if data.get("network") != NETWORK:
        raise ValueError(f"Wallet network must be {NETWORK!r}")
    return data

def save_wallet(data: dict[str, Any], path: Path = WALLET_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix="wallet-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        try:
            os.chmod(temp_name, 0o600)
        except OSError:
            pass
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

def ensure_p2pkh(*, replace: bool = False) -> dict[str, Any]:
    wallet = load_wallet()
    if replace or "task1" not in wallet:
        wallet["task1"] = generate_p2pkh_record()
        save_wallet(wallet)
    return wallet["task1"]

def ensure_multisig(*, replace: bool = False) -> dict[str, Any]:
    wallet = load_wallet()
    if replace or "task2" not in wallet:
        wallet["task2"] = generate_multisig_record()
        save_wallet(wallet)
    return wallet["task2"]
