"""Task 2 CLI: create and spend a legacy Testnet4 2-of-2 P2SH output."""
from __future__ import annotations

import argparse
import json

from common.cli import add_spend_arguments, emit_transaction, select_funding_utxo
from common.txbuild import build_multisig_spend
from common.wallet import ensure_multisig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create or show the Task 2 multisig address")
    init.add_argument("--replace", action="store_true", help="replace saved keys (unsafe if old address has funds)")
    init.add_argument("--show-private-keys", action="store_true", help="print WIFs for the lab demonstration")
    spend = commands.add_parser("spend", help="build and optionally broadcast a 2-of-2 spend")
    add_spend_arguments(spend)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    record = ensure_multisig(replace=getattr(args, "replace", False))
    if args.command == "init":
        keys = [
            {
                "public_key": key["public_key"],
                "private_key_wif": key["wif"] if args.show_private_keys else "redacted (use --show-private-keys)",
            }
            for key in record["keys"]
        ]
        print(json.dumps({"network": record["network"], "address": record["address"], "redeem_script": record["redeem_script"], "keys": keys}, indent=2))
        return 0
    client, utxo = select_funding_utxo(
        record["address"], args.amount, args.fee_rate, args.include_unconfirmed
    )
    result = build_multisig_spend(
        utxo=utxo,
        wifs=[key["wif"] for key in record["keys"]],
        redeem_script_hex=record["redeem_script"],
        destination=args.destination,
        amount=args.amount,
        change_address=record["address"],
        fee_rate=args.fee_rate,
    )
    emit_transaction(result, client, broadcast=args.broadcast, wait=args.wait)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
