"""Task 1 CLI: create and spend a legacy Testnet4 P2PKH output."""
from __future__ import annotations

import argparse
import json

from common.cli import add_spend_arguments, emit_transaction, select_funding_utxo
from common.txbuild import build_p2pkh_spend
from common.wallet import ensure_p2pkh


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create or show the Task 1 Testnet4 address")
    init.add_argument("--replace", action="store_true", help="replace the saved key (unsafe if old address has funds)")
    init.add_argument("--show-private-key", action="store_true", help="print WIF for the lab demonstration")
    spend = commands.add_parser("spend", help="build and optionally broadcast a P2PKH spend")
    add_spend_arguments(spend)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    record = ensure_p2pkh(replace=getattr(args, "replace", False))
    if args.command == "init":
        output = {
            "network": record["network"],
            "address": record["key"]["address"],
            "public_key": record["key"]["public_key"],
            "private_key_wif": record["key"]["wif"] if args.show_private_key else "redacted (use --show-private-key)",
        }
        print(json.dumps(output, indent=2))
        return 0
    client, utxo = select_funding_utxo(
        record["key"]["address"], args.amount, args.fee_rate, args.include_unconfirmed
    )
    result = build_p2pkh_spend(
        utxo=utxo,
        wif=record["key"]["wif"],
        destination=args.destination,
        amount=args.amount,
        fee_rate=args.fee_rate,
    )
    emit_transaction(result, client, broadcast=args.broadcast, wait=args.wait)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
