"""Esplora and Bitcoin Core Testnet4 clients."""
from __future__ import annotations
import time
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit
import requests
from .config import ESPLORA_URL, POLL_SECONDS, REQUEST_TIMEOUT
from .models import UTXO

class NetworkError(RuntimeError):
    pass

class EsploraClient:
    def __init__(self, base_url: str = ESPLORA_URL, timeout: float = REQUEST_TIMEOUT) -> None:
        if not base_url.lower().startswith("https://"):
            raise ValueError("Esplora URL must use HTTPS")
        self.base_url, self.timeout = base_url.rstrip("/"), timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "bitcoin-script-lab/1.0"

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        try:
            response = self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise NetworkError(f"Testnet4 API request failed: {exc}") from exc
        if not response.ok:
            raise NetworkError(f"Testnet4 API returned HTTP {response.status_code}: {response.text.strip()[:500]}")
        return response

    def get_utxos(self, address: str, *, confirmed_only: bool = True) -> list[UTXO]:
        rows = self._request("GET", f"/address/{address}/utxo").json()
        utxos = [UTXO(row["txid"], int(row["vout"]), int(row["value"]), bool(row.get("status", {}).get("confirmed", False)), row.get("status", {}).get("block_height")) for row in rows]
        if confirmed_only:
            utxos = [item for item in utxos if item.confirmed]
        return sorted(utxos, key=lambda item: item.value, reverse=True)

    def get_transaction(self, txid: str) -> dict[str, Any]:
        return self._request("GET", f"/tx/{txid}").json()

    def broadcast(self, raw_hex: str) -> str:
        return self._request("POST", "/tx", data=raw_hex, headers={"Content-Type": "text/plain"}).text.strip()

    def transaction_status(self, txid: str) -> dict[str, Any]:
        return self._request("GET", f"/tx/{txid}/status").json()

    def wait_for_confirmation(self, txid: str, *, timeout: float = 900, poll_seconds: float = POLL_SECONDS) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.transaction_status(txid)
            if status.get("confirmed"):
                return status
            time.sleep(poll_seconds)
        raise TimeoutError(f"Transaction {txid} was not confirmed within {timeout:g} seconds")


def get_utxos(address: str) -> list[dict[str, Any]]:
    """Compatibility wrapper for the simple helper API in the lab plan."""
    return [{"txid": item.txid, "vout": item.vout, "value": item.value, "status": {"confirmed": item.confirmed, "block_height": item.block_height}} for item in EsploraClient().get_utxos(address)]


def broadcast_tx(raw_tx_hex: str) -> str:
    return EsploraClient().broadcast(raw_tx_hex)


def wait_for_confirmation(txid: str, min_conf: int = 1, timeout_seconds: float = 900) -> dict[str, Any]:
    _ = min_conf
    return EsploraClient().wait_for_confirmation(txid, timeout=timeout_seconds)

class BitcoinCoreClient:
    def __init__(self, rpc_url: str, timeout: float = REQUEST_TIMEOUT) -> None:
        parsed = urlsplit(rpc_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Bitcoin Core RPC URL must be an HTTP(S) URL")
        self.auth = (unquote(parsed.username), unquote(parsed.password or "")) if parsed.username is not None else None
        host = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
        self.url, self.timeout = urlunsplit((parsed.scheme, host, parsed.path or "/", "", "")), timeout

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        try:
            response = requests.post(self.url, auth=self.auth, json={"jsonrpc": "2.0", "id": "bitcoin-script-lab", "method": method, "params": params or []}, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise NetworkError(f"Bitcoin Core RPC request failed: {exc}") from exc
        if payload.get("error"):
            raise NetworkError(f"Bitcoin Core RPC error: {payload['error']}")
        return payload.get("result")

    def test_mempool_accept(self, raw_hex: str) -> dict[str, Any]:
        info = self.call("getblockchaininfo")
        # Bitcoin Core reports both Testnet3 and Testnet4 as chain="test".
        # Testnet4's genesis hash distinguishes it from the deprecated chain.
        if info.get("chain") != "test" or info.get("initialblockdownload"):
            raise NetworkError("Bitcoin Core must be synchronized on Testnet4")
        genesis_hash = self.call("getblockhash", [0])
        if genesis_hash != "00000000da84f2bafbbc53dee25a72ae507ff4914b867c565be350b0da8bf043":
            raise NetworkError("Bitcoin Core RPC is not connected to Testnet4")
        result = self.call("testmempoolaccept", [[raw_hex]])
        if not isinstance(result, list) or len(result) != 1:
            raise NetworkError("Invalid testmempoolaccept response")
        return result[0]

def choose_utxo(utxos: list[UTXO], minimum_value: int) -> UTXO:
    for utxo in sorted(utxos, key=lambda item: item.value):
        if utxo.value >= minimum_value:
            return utxo
    raise ValueError(f"No confirmed UTXO can cover at least {minimum_value} satoshis")
