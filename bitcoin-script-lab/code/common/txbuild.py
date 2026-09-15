"""Legacy P2PKH and 2-of-2 P2SH transaction construction."""
from __future__ import annotations
from collections.abc import Callable, Sequence
from .bitcoin_compat import prepare_python_bitcoinlib
prepare_python_bitcoinlib()
import bitcoin  # noqa: E402
from bitcoin.core import CMutableTransaction, CMutableTxIn, CMutableTxOut, COutPoint, b2lx, lx  # noqa: E402
from bitcoin.core.script import CScript, OP_0, SIGHASH_ALL, SignatureHash  # noqa: E402
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2PKHBitcoinAddress  # noqa: E402
from .config import BITCOINLIB_NETWORK, DUST_LIMIT
from .models import BuiltTransaction, UTXO
from .scriptcheck import verify_input
bitcoin.SelectParams(BITCOINLIB_NETWORK)

def create_txin(txid: str, output_index: int, *, sequence: int = 0xFFFFFFFD) -> CMutableTxIn:
    return CMutableTxIn(COutPoint(lx(txid), output_index), nSequence=sequence)

def create_txout(amount_sats: int, address: str) -> CMutableTxOut:
    if amount_sats <= 0:
        raise ValueError("Output amount must be positive")
    return CMutableTxOut(amount_sats, CBitcoinAddress(address).to_scriptPubKey())

def _sign_p2pkh(tx, secret: CBitcoinSecret, previous_script_pubkey) -> None:
    digest = SignatureHash(previous_script_pubkey, tx, 0, SIGHASH_ALL)
    tx.vin[0].scriptSig = CScript([secret.sign(digest) + bytes([SIGHASH_ALL]), bytes(secret.pub)])

def _sign_multisig(tx, secrets: Sequence[CBitcoinSecret], redeem_script: CScript) -> None:
    digest = SignatureHash(redeem_script, tx, 0, SIGHASH_ALL)
    signatures = [secret.sign(digest) + bytes([SIGHASH_ALL]) for secret in secrets]
    tx.vin[0].scriptSig = CScript([OP_0, *signatures, bytes(redeem_script)])

def _build_fee_aware(*, utxo: UTXO, destination: str, amount: int, change_address: str, fee_rate: int, previous_script_pubkey, signer: Callable[[CMutableTransaction], None]) -> BuiltTransaction:
    if fee_rate < 1:
        raise ValueError("Fee rate must be at least 1 sat/vB")
    if amount < DUST_LIMIT:
        raise ValueError(f"Destination amount must be at least {DUST_LIMIT} satoshis")
    if amount >= utxo.value:
        raise ValueError("Amount must leave room for the miner fee")
    change = utxo.value - amount - 1000
    include_change = change >= DUST_LIMIT
    for _ in range(8):
        outputs = [create_txout(amount, destination)]
        if include_change:
            outputs.append(create_txout(max(change, DUST_LIMIT), change_address))
        tx = CMutableTransaction([create_txin(utxo.txid, utxo.vout)], outputs)
        signer(tx)
        target_fee = len(tx.serialize()) * fee_rate
        new_change = utxo.value - amount - target_fee
        new_include_change = new_change >= DUST_LIMIT
        if new_include_change == include_change and (not include_change or abs(new_change - change) <= 2):
            break
        include_change, change = new_include_change, new_change
    else:
        raise RuntimeError("Fee calculation did not converge")
    if include_change:
        # DER ECDSA signatures can vary by one byte. Reserve a two-vbyte
        # safety margin so a later signature-length change cannot underpay.
        required_fee = (len(tx.serialize()) + 2) * fee_rate
        change = utxo.value - amount - required_fee
        if change < DUST_LIMIT:
            include_change = False
            tx.vout.pop()
            signer(tx)
        else:
            tx.vout[1].nValue = change
            signer(tx)
            # Recompute after signing; keep a small fee margin for signature-size variance.
            final_fee = (len(tx.serialize()) + 2) * fee_rate
            change = utxo.value - amount - final_fee
            tx.vout[1].nValue = change
            signer(tx)
    fee = utxo.value - sum(output.nValue for output in tx.vout)
    vsize = len(tx.serialize())
    if fee < vsize * fee_rate:
        raise RuntimeError("Constructed transaction fee is below the requested fee rate")
    verify_input(tx, 0, previous_script_pubkey)
    return BuiltTransaction(tx.serialize().hex(), b2lx(tx.GetTxid()), fee, vsize, amount, change if include_change else 0, destination)

def build_p2pkh_spend(*, utxo: UTXO, wif: str, destination: str, amount: int, fee_rate: int) -> BuiltTransaction:
    secret = CBitcoinSecret(wif)
    source = P2PKHBitcoinAddress.from_pubkey(bytes(secret.pub))
    previous = source.to_scriptPubKey()
    return _build_fee_aware(utxo=utxo, destination=destination, amount=amount, change_address=str(source), fee_rate=fee_rate, previous_script_pubkey=previous, signer=lambda tx: _sign_p2pkh(tx, secret, previous))

def build_multisig_spend(*, utxo: UTXO, wifs: Sequence[str], redeem_script_hex: str, destination: str, amount: int, change_address: str, fee_rate: int) -> BuiltTransaction:
    if len(wifs) != 2:
        raise ValueError("A 2-of-2 spend requires exactly two private keys")
    secrets = [CBitcoinSecret(wif) for wif in wifs]
    redeem = CScript(bytes.fromhex(redeem_script_hex))
    previous = redeem.to_p2sh_scriptPubKey()
    return _build_fee_aware(utxo=utxo, destination=destination, amount=amount, change_address=change_address, fee_rate=fee_rate, previous_script_pubkey=previous, signer=lambda tx: _sign_multisig(tx, secrets, redeem))
