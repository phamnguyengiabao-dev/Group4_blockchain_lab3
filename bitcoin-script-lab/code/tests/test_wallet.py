from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.wallet import generate_multisig_record, generate_p2pkh_record, load_wallet, save_wallet


class WalletTests(unittest.TestCase):
    def test_generates_testnet4_p2pkh(self) -> None:
        record = generate_p2pkh_record()
        self.assertEqual(record["network"], "testnet4")
        self.assertIn(record["key"]["address"][0], "mn")
        self.assertEqual(len(record["key"]["public_key"]), 66)

    def test_generates_2_of_2_p2sh(self) -> None:
        record = generate_multisig_record()
        self.assertEqual(record["kind"], "p2sh-2of2")
        self.assertTrue(record["address"].startswith("2"))
        self.assertEqual(len(record["keys"]), 2)
        self.assertTrue(record["redeem_script"].endswith("52ae"))

    def test_wallet_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wallet.json"
            expected = {"version": 1, "network": "testnet4", "task1": generate_p2pkh_record()}
            save_wallet(expected, path)
            self.assertEqual(load_wallet(path), expected)

    def test_migrates_legacy_testnet_wallet_to_testnet4(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wallet.json"
            task1 = generate_p2pkh_record()
            task1["network"] = "testnet"
            save_wallet({"version": 1, "network": "testnet", "task1": task1}, path)
            migrated = load_wallet(path)
            self.assertEqual(migrated["network"], "testnet4")
            self.assertEqual(migrated["task1"]["network"], "testnet4")


if __name__ == "__main__":
    unittest.main()
