from __future__ import annotations

import unittest

from common.bitcoin_compat import prepare_python_bitcoinlib

prepare_python_bitcoinlib()
from bitcoin.core import CMutableTransaction, CTransaction
from bitcoin.core.script import CScript, OP_0, OP_2, OP_CHECKMULTISIG, SIGHASH_ALL, SignatureHash
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2PKHBitcoinAddress

from common.models import UTXO
from common.scriptcheck import verify_input
from common.txbuild import build_multisig_spend, build_p2pkh_spend


def fixed_secret(byte_value: int) -> CBitcoinSecret:
    return CBitcoinSecret.from_secret_bytes(bytes([byte_value]) * 32, compressed=True)


class TransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.destination_secret = fixed_secret(9)
        self.destination = str(P2PKHBitcoinAddress.from_pubkey(bytes(self.destination_secret.pub)))
        self.utxo = UTXO("11" * 32, 0, 100_000, True, 1)

    def test_p2pkh_builds_and_verifies(self) -> None:
        secret = fixed_secret(1)
        result = build_p2pkh_spend(
            utxo=self.utxo, wif=str(secret), destination=self.destination, amount=50_000, fee_rate=2
        )
        tx = CTransaction.deserialize(bytes.fromhex(result.raw_hex))
        previous = P2PKHBitcoinAddress.from_pubkey(bytes(secret.pub)).to_scriptPubKey()
        verify_input(tx, 0, previous)
        self.assertGreaterEqual(result.fee, result.vsize * 2)
        self.assertEqual(result.amount + result.change + result.fee, self.utxo.value)

    def test_p2pkh_wrong_key_fails(self) -> None:
        secret = fixed_secret(1)
        result = build_p2pkh_spend(
            utxo=self.utxo, wif=str(secret), destination=self.destination, amount=50_000, fee_rate=2
        )
        tx = CTransaction.deserialize(bytes.fromhex(result.raw_hex))
        wrong_previous = P2PKHBitcoinAddress.from_pubkey(bytes(fixed_secret(2).pub)).to_scriptPubKey()
        with self.assertRaises(Exception):
            verify_input(tx, 0, wrong_previous)

    def test_multisig_builds_with_dummy_and_verifies(self) -> None:
        keys = [fixed_secret(3), fixed_secret(4)]
        redeem = CScript([OP_2, bytes(keys[0].pub), bytes(keys[1].pub), OP_2, OP_CHECKMULTISIG])
        change_address = str(CBitcoinAddress.from_scriptPubKey(redeem.to_p2sh_scriptPubKey()))
        result = build_multisig_spend(
            utxo=self.utxo,
            wifs=[str(key) for key in keys],
            redeem_script_hex=bytes(redeem).hex(),
            destination=self.destination,
            amount=50_000,
            change_address=change_address,
            fee_rate=2,
        )
        tx = CTransaction.deserialize(bytes.fromhex(result.raw_hex))
        self.assertEqual(bytes(tx.vin[0].scriptSig)[0], int(OP_0))
        verify_input(tx, 0, redeem.to_p2sh_scriptPubKey())
        self.assertGreaterEqual(result.fee, result.vsize * 2)

    def test_multisig_one_signature_fails(self) -> None:
        keys = [fixed_secret(5), fixed_secret(6)]
        redeem = CScript([OP_2, bytes(keys[0].pub), bytes(keys[1].pub), OP_2, OP_CHECKMULTISIG])
        change_address = str(CBitcoinAddress.from_scriptPubKey(redeem.to_p2sh_scriptPubKey()))
        result = build_multisig_spend(
            utxo=self.utxo,
            wifs=[str(key) for key in keys],
            redeem_script_hex=bytes(redeem).hex(),
            destination=self.destination,
            amount=50_000,
            change_address=change_address,
            fee_rate=2,
        )
        mutable = CMutableTransaction.from_tx(CTransaction.deserialize(bytes.fromhex(result.raw_hex)))
        digest = SignatureHash(redeem, mutable, 0, SIGHASH_ALL)
        one_signature = keys[0].sign(digest) + bytes([SIGHASH_ALL])
        mutable.vin[0].scriptSig = CScript([OP_0, one_signature, bytes(redeem)])
        with self.assertRaises(Exception):
            verify_input(mutable, 0, redeem.to_p2sh_scriptPubKey())

    def test_rejects_dust_destination(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 546"):
            build_p2pkh_spend(
                utxo=self.utxo,
                wif=str(fixed_secret(7)),
                destination=self.destination,
                amount=545,
                fee_rate=2,
            )


if __name__ == "__main__":
    unittest.main()
