"""Small data models shared by network and transaction modules."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UTXO:
    txid: str
    vout: int
    value: int
    confirmed: bool = False
    block_height: int | None = None

    def __post_init__(self) -> None:
        if len(self.txid) != 64:
            raise ValueError("txid must contain 64 hexadecimal characters")
        try:
            bytes.fromhex(self.txid)
        except ValueError as exc:
            raise ValueError("txid is not valid hexadecimal") from exc
        if self.vout < 0:
            raise ValueError("vout cannot be negative")
        if self.value <= 0:
            raise ValueError("UTXO value must be positive")


@dataclass(frozen=True, slots=True)
class BuiltTransaction:
    raw_hex: str
    txid: str
    fee: int
    vsize: int
    amount: int
    change: int
    destination: str
