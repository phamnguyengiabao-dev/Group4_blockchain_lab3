"""CLI helpers shared by the two lab tasks."""
from __future__ import annotations

import json
import os

from .config import DEFAULT_FEE_RATE
from .network import BitcoinCoreClient, EsploraClient, NetworkError, choose_utxo


def add_spend_arguments(parser) -> None:
    parser.add_argument("destination", help="Testnet4 legacy destination address")
    parser.add_argument("amount", type=int, help="amount in satoshis")
    parser.add_argument("--fee-rate", type=int, default=DEFAULT_FEE_RATE, help="fee rate in sat/vB")
    parser.add_argument("--include-unconfirmed", action="store_true", help="allow an unconfirmed funding UTXO")
    parser.add_argument("--broadcast", action="store_true", help="broadcast after all local/RPC checks")
    parser.add_argument("--wait", action="store_true", help="wait up to 15 minutes for one confirmation")


def select_funding_utxo(address: str, amount: int, fee_rate: int, include_unconfirmed: bool):
    client = EsploraClient()
    utxos = client.get_utxos(address, confirmed_only=not include_unconfirmed)
    # A legacy 2-of-2 P2SH transaction is normally below 500 vbytes. Reserving
    # this much avoids selecting a UTXO that covers the amount but not its fee.
    return client, choose_utxo(utxos, amount + fee_rate * 500)


def emit_transaction(result, client: EsploraClient, *, broadcast: bool, wait: bool) -> None:
    if wait and not broadcast:
        raise ValueError("--wait requires --broadcast")
    summary = {
        "txid": result.txid,
        "destination": result.destination,
        "amount_sats": result.amount,
        "change_sats": result.change,
        "fee_sats": result.fee,
        "vsize": result.vsize,
        "raw_transaction": result.raw_hex,
        "local_script_verification": "passed",
        "broadcast": False,
    }
    rpc_url = os.getenv("BTC_LAB_RPC_URL")
    if rpc_url:
        preflight = BitcoinCoreClient(rpc_url).test_mempool_accept(result.raw_hex)
        summary["testmempoolaccept"] = preflight
        if not preflight.get("allowed"):
            print(json.dumps(summary, indent=2))
            raise NetworkError(f"Mempool preflight rejected transaction: {preflight.get('reject-reason', 'unknown')}")
    else:
        summary["testmempoolaccept"] = "skipped (BTC_LAB_RPC_URL is not configured)"

    if broadcast:
        txid = client.broadcast(result.raw_hex)
        if txid != result.txid:
            raise NetworkError(f"Broadcast returned unexpected txid {txid}")
        summary["broadcast"] = True
        if wait:
            summary["confirmation"] = client.wait_for_confirmation(txid)
    print(json.dumps(summary, indent=2))
