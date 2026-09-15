"""Local consensus-script verification gate."""
from __future__ import annotations

from .bitcoin_compat import prepare_python_bitcoinlib

prepare_python_bitcoinlib()
from bitcoin.core.scripteval import (  # noqa: E402
    SCRIPT_VERIFY_CLEANSTACK,
    SCRIPT_VERIFY_DERSIG,
    SCRIPT_VERIFY_LOW_S,
    SCRIPT_VERIFY_NULLDUMMY,
    SCRIPT_VERIFY_P2SH,
    SCRIPT_VERIFY_SIGPUSHONLY,
    SCRIPT_VERIFY_STRICTENC,
    VerifyScript,
)

VERIFY_FLAGS = (
    SCRIPT_VERIFY_P2SH,
    SCRIPT_VERIFY_STRICTENC,
    SCRIPT_VERIFY_DERSIG,
    SCRIPT_VERIFY_LOW_S,
    SCRIPT_VERIFY_NULLDUMMY,
    SCRIPT_VERIFY_SIGPUSHONLY,
    SCRIPT_VERIFY_CLEANSTACK,
)


def verify_input(transaction, input_index: int, previous_script_pubkey) -> None:
    VerifyScript(
        transaction.vin[input_index].scriptSig,
        previous_script_pubkey,
        transaction,
        input_index,
        flags=VERIFY_FLAGS,
    )
