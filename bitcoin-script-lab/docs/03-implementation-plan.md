# Lab 03 — Implementation Plan

**Derived from:** [02-objectives-and-scope.md](02-objectives-and-scope.md)
**Method note:** phase-gated workflow inspired by the blockchain-agent-skills lifecycle — *plan → simulate (offline validation) → broadcast → confirm-depth*. Nothing goes on-chain before it passes offline script evaluation.

---

## 1. Architecture Overview

```
bitcoin-script-lab/
├── code/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py          # network (testnet3/testnet4), fee floor, API endpoints
│   │   ├── wallet.py          # key generation + persistence (JSON, git-ignored)
│   │   ├── network.py         # Esplora API: UTXO fetch, tx broadcast, confirmation wait
│   │   ├── txbuild.py         # create_txin / create_txout / create_signed_transaction
│   │   │                       #   (P2PKH + P2SH-multisig), fee & change logic
│   │   └── scriptcheck.py     # offline script execution before any broadcast
│   ├── task1_p2pkh.py         # lock (gen keys/addr) + spend (UTXO→sign→broadcast)
│   ├── task2_multisig.py      # lock (2-of-2 P2SH) + spend (dual-sig + redeem reveal)
│   ├── test_offline.py        # no-network unit tests incl. negative multisig case
│   ├── requirements.txt       # python-bitcoinlib (pinned), requests
│   └── README.md              # how to run each phase, faucet links
├── docs/                      # this documentation set
├── report/
│   ├── report.md              # report source (converted to Report.pdf)
│   └── assets/                # diagrams (tx flow, script stacks)
├── package_submission.py      # builds <GroupID>/Code + Report.pdf → <GroupID>.zip
├── .secrets/                  # local testnet keys/metadata; never committed or packaged
├── .gitignore                 # wallet.json, __pycache__, report build artifacts
└── README.md
```

**Key design decisions**

- **Implement the PDF's implied API ourselves.** `create_txin`, `create_txout`, `create_signed_transaction`, `broadcast_tx` don't exist in any library — they become a thin, well-tested layer over `python-bitcoinlib` primitives (`CMutableTransaction`, `CTxIn`, `CTxOut`, `CScript`, `Sign` helpers). This is deliberate: we want to show the script assembly, not hide it.
- **Offline-first.** `scriptcheck.py` uses the library's consensus-aware `VerifyScript(scriptSig, scriptPubKey, tx, input_index, flags)` *before* broadcasting. If Bitcoin Core RPC is configured, `testmempoolaccept` is the second gate. Failures are caught without wasting testnet cycles.
- **Persist everything needed to spend.** Keys, redeem script, and UTXO metadata are written to `.secrets/wallet.json` (git-ignored) immediately, so lock and spend can run in separate sessions. The file is never packaged or shown in the report.
- **Fee-aware by default.** Spends either sweep the UTXO (amount − fee) or create a change output; the plan never relies on zero-fee transactions.

---

## 2. Phase Plan

### Phase 0 — Environment & Foundations  *(est. 0.5 day)*

**Goal:** a reproducible dev environment and a validated skeleton.

- [ ] Create Python venv; `pip install python-bitcoinlib requests` (pin versions in `requirements.txt`).
- [ ] `config.py`: network selection constant (default **Testnet3**; Testnet4 switch documented), Esplora base URL, fee constants (sat/vByte floor).
- [ ] `wallet.py`: generate `CBitcoinSecret.from_secret_bytes(os.urandom(32))`, derive `pub`, addresses; save/load `.secrets/wallet.json` (keys as WIF, redeem scripts as hex). Display testnet WIF only when explicitly requested to satisfy the lab demonstration; redact it from screenshots and report artifacts.
- [ ] Verify library APIs offline: key → pubkey → P2PKH address round-trip; redeem script → P2SH address round-trip.
- [ ] `.gitignore` covering `.secrets/`, `wallet.json`, `.venv/`, `__pycache__/`, `*.pyc`, report build outputs.

**Exit criteria:** `python -c` snippets from the PDF run unmodified and print consistent key/address triples; wallet file saves and reloads.

### Phase 1 — Common Transaction Layer  *(est. 1 day)*

**Goal:** the four helper functions, network access, and offline validation — all unit-tested without touching the network.

- [ ] `network.py`:
  - `get_utxos(address)` → list of `{txid, vout, value, status}` from Esplora `/address/:addr/utxo`.
  - `broadcast_tx(tx)` → POST `/tx`; returns txid or raises with API error body.
  - `wait_for_confirmation(txid, min_conf=1)` → polls `/tx/:txid` with backoff.
- [ ] `txbuild.py`:
  - `create_txin(txid, output_index)` → `CTxIn(COutPoint(...), b"", sequence=0xffffffff)`.
  - `create_txout(amount_sats, address)` → `CTxOut(amount, address.to_scriptPubKey())`.
  - `create_signed_transaction(txins, txouts, keys, redeem_script=None)`:
    - P2PKH path: sign each input with `SIGHASH_ALL` using the standard bitcoinlib signature flow.
    - P2SH path: hash over the **redeem script** (P2SH signing), scriptSig = `[OP_0, sig1, sig2, redeem_script]` (dummy `OP_0` compensates the `OP_CHECKMULTISIG` off-by-one).
    - fee calculation: `estimate_fee(vsize)`, change output back to sender when UTXO value − amount − fee > dust threshold.
- [ ] `scriptcheck.py`: run `VerifyScript` with the relevant standard verification flags and assert success. Produce a sanitized opcode/stack walkthrough for the report without exposing private keys.
- [ ] Optional Bitcoin Core preflight: call `testmempoolaccept` on the signed raw transaction; block broadcast when `allowed` is false and record `reject-reason`.
- [ ] `test_offline.py`: known-vector tests —
  - P2PKH unlock validates with correct key, fails with wrong key.
  - Multisig validates with both sigs, **fails with one sig** (SC-5 negative case).
  - `OP_0` dummy-element presence check for multisig scriptSig.

**Exit criteria:** `test_offline.py` fully green; no network calls in tests.

### Phase 2 — Task 1: P2PKH Lock & Spend  *(est. 1 day + faucet latency)*

**Goal:** FR-1.1–1.3 demonstrated on testnet (SC-1, SC-2).

- [ ] `task1_p2pkh.py lock`: generate key triple → persist → print address + faucet instructions.
- [ ] Request testnet coins from a faucet (manual step; links in `code/README.md`).
- [ ] `task1_p2pkh.py spend`: fetch UTXOs for the address → pick largest → build output to a second (destination) address we control → fee + change handling → offline script check → broadcast → wait for confirmation.
- [ ] Record artifacts for the report: funding txid, spend txid, explorer URLs, vsize/fee, script hex dumps.
- [ ] Run a controlled failure once (wrong key / insufficient sig) and capture the error for the "challenges" report section.

**Exit criteria:** confirmed funding tx and confirmed spend tx visible on the explorer; artifacts saved under `report/assets/` (or referenced by txid).

### Phase 3 — Task 2: 2-of-2 Multisig P2SH Lock & Spend  *(est. 1 day + faucet latency)*

**Goal:** FR-2.1–2.5 demonstrated on testnet (SC-3, SC-4, SC-5).

- [ ] `task2_multisig.py lock`: two key triples → redeem script `OP_2 pk1 pk2 OP_2 OP_CHECKMULTISIG` → P2SH address → persist redeem script + both keys → print faucet instructions.
- [ ] Fund the P2SH address via faucet.
- [ ] `task2_multisig.py spend`: UTXO fetch → build tx signed by **both** keys over the redeem script → scriptSig with `OP_0` dummy + sigs + serialized redeem script → offline check → broadcast → confirm.
- [ ] Negative demonstration (offline): same spend with one signature fails evaluation — include stack trace in report.
- [ ] Record artifacts (txids, script hex, explorer URLs).

**Exit criteria:** confirmed multisig funding and spend txs; negative case documented.

### Phase 4 — Task 3: Report  *(est. 1 day)*

**Goal:** FR-3.1–3.3 and every §7 report requirement (SC-6).

Report outline (target ~10–12 pages, well under the 15-page cap):

1. **Cover & team** — members, course, group ID.
2. **Introduction** — Bitcoin, UTXO model, Bitcoin Script (why stack-based, non-Turing-complete).
3. **System design & operation** — component diagram; lock/spend flow for both tasks *in prose and diagrams* (script stack walkthroughs: what the stack looks like after `OP_DUP`, `OP_HASH160`, `OP_EQUALVERIFY`, `OP_CHECKSIG` / the multisig variant). **No source code** (NFR-3).
4. **Results** — testnet txids + explorer screenshots, fees, confirmation times.
5. **Security discussion** — multisig benefits (FR-2.6): no single point of failure, extortion resistance, escrow patterns; Script advantages (simplicity, determinism, auditability, limited attack surface) and limitations (non-Turing-complete, no loops, malleability history, limited state, fee/UX complexity of P2SH reveals).
6. **Challenges encountered** — the gaps from the analysis (helpers, fees, `OP_0` quirk, network selection, faucet availability) and how each was solved.
7. **Lessons learned** — per-member short reflections.
8. **Project structure** — annotated tree of `<GroupID>/Code/`.
9. **References** — all links and books used.

- [ ] Write `report/report.md` → convert to PDF (12 pt, single-sided; e.g. pandoc/pandas → PDF or Word → PDF).
- [ ] Check against the §7 checklist; verify page count ≤ 15.

**Exit criteria:** `Report.pdf` passes the §7 checklist.

### Phase 5 — Packaging & Submission  *(est. 0.25 day)*

- [ ] `package_submission.py`: builds `<GroupID>/Code/` (source + requirements + README, **no `.secrets/` or wallet files**), copies `Report.pdf`, zips to `<GroupID>.zip`.
- [ ] Dry-run the script; inspect the zip tree; confirm no secrets inside.
- [ ] Final review pass: every requirement FR/NFR/SC checked off in this plan.

**Exit criteria:** `<GroupID>.zip` structure matches §7 exactly (SC-7).

---

## 3. Schedule & Effort

| Phase | Working days | Dependency |
|---|---|---|
| 0 Environment | 0.5 | — |
| 1 Common layer + tests | 1 | P0 |
| 2 Task 1 on testnet | 1 (+faucet latency) | P1 |
| 3 Task 2 on testnet | 1 (+faucet latency) | P1 (parallelizable with P2) |
| 4 Report | 1 | P2, P3 |
| 5 Packaging | 0.25 | P4 |
| **Total** | **~4.75 days** | |

Team split suggestion: one member drives P1 + P2, one drives P3 (reusing P1), one owns P4 (report, starting early from docs), all review P5.

## 4. Test Strategy

| Layer | Test | Type |
|---|---|---|
| Script semantics | P2PKH unlock true/false; multisig 2-of-2 true, 1-of-2 false; dummy `OP_0` presence | Offline unit with `VerifyScript` (`test_offline.py`) |
| Mempool policy | Signed raw transaction accepted/rejected with reason | Bitcoin Core `testmempoolaccept` when RPC is available |
| Tx construction | Fee = in − out − change; dust threshold respected; address encoding | Offline unit |
| Network | UTXO fetch parsing; broadcast error surfaces | Mocked unit + one live smoke per task |
| End-to-end | SC-1…SC-4 confirmations on testnet explorer | Live checklist |
| Negative/security | Wrong-key spend fails; missing-signature spend fails | Offline (and never broadcast) |

## 5. Definition of Done

1. All functional requirements FR-1.x, FR-2.x, FR-3.x satisfied.
2. All success criteria SC-1…SC-7 verified and evidenced (txids / checklist).
3. `test_offline.py` green; both live flows confirmed on testnet.
4. `Report.pdf` compliant with every §7 clause.
5. `<GroupID>.zip` built by the packaging script and manually inspected.
6. No secrets (private keys, wallet files) anywhere in the repository or the zip.

## 6. Reference Library Versions (pin in requirements.txt)

- `python-bitcoinlib` — provides `bitcoin.wallet` (`CBitcoinSecret`, `P2PKHBitcoinAddress`, `P2SHBitcoinAddress`), `bitcoin.core` (`CScript`, `CMutableTransaction`, `EvalScript`).
- `requests` — Esplora API calls.
- Python ≥ 3.10.

## 7. External Resources (for the report's references section)

- Bitcoin Script opcodes reference — https://developer.bitcoin.org/reference/ops.html
- Bitcoin transactions & scripts guide — https://developer.bitcoin.org/devguide/transactions.html
- `python-bitcoinlib` documentation — https://bitcoinpython.readthedocs.io/
- Blockstream Esplora testnet explorer/API — https://blockstream.info/testnet/
- Testnet faucets (availability varies): e.g. https://coinfaucet.eu/en/btc-testnet/, https://testnet-faucet.com/ (confirm at run time)
- S. Nakamoto, *Bitcoin: A Peer-to-Peer Electronic Cash System* (2008)
- A. Antonopoulos, *Mastering Bitcoin*, 2nd ed., O'Reilly (esp. ch. 6–7)
