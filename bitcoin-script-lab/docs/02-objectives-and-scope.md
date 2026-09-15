# Lab 03 — Objectives & Scope

**Input:** [01-requirements-analysis.md](01-requirements-analysis.md)
**Output:** feeds [03-implementation-plan.md](03-implementation-plan.md)

---

## 1. Mission Statement

Build a small, well-tested Python toolkit that demonstrates Bitcoin Script in action on testnet: it creates a P2PKH address, locks and spends funds through it (Task 1); creates a 2-of-2 multisig P2SH address, locks and spends funds through it (Task 2); and documents the experience, security analysis, and the advantages/limitations of Bitcoin Script (Task 3) — all packaged exactly per the submission regulation (§7).

## 2. Learning Objectives (course-level)

| # | Objective | Evidenced by |
|---|---|---|
| LO-1 | Explain the UTXO model and how locking/unlocking scripts compose (`scriptPubKey` + `scriptSig`) | Code structure + report §Operation |
| LO-2 | Hand-assemble P2PKH locking & unlocking scripts from opcodes | Task 1 code + test vector walkthrough |
| LO-3 | Build and spend a 2-of-2 multisig inside P2SH, including the `OP_CHECKMULTISIG` dummy-element quirk | Task 2 code + successful testnet spend |
| LO-4 | Reason about the security properties and trade-offs of Script (single-key vs multisig, fee/privacy/design limits) | Task 3 report |
| LO-5 | Operate safely on testnet with disciplined key handling | `.gitignore` policy, persisted key files outside VCS |

## 3. Objectives → Scope Matrix (synthesis of requirements)

Every graded requirement from the analysis maps to one deliverable in scope:

| Req | Deliverable (in scope) |
|---|---|
| FR-1.1 | `task1_p2pkh.py` — key/address generation & printing |
| FR-1.2 | Faucet funding step (documented procedure + script to watch for confirmation) |
| FR-1.3 | `task1_p2pkh.py` spend flow: UTXO fetch → fee-aware tx build → sign → broadcast |
| FR-2.1–2.3 | `task2_multisig.py` — key pair generation, redeem script, P2SH address |
| FR-2.4 | Faucet funding of the P2SH address (same watcher) |
| FR-2.5 | `task2_multisig.py` spend flow: dual-signature input + redeem script reveal → broadcast |
| FR-2.6 | Multisig security discussion (report section + summary in code docstring) |
| FR-3.1–3.3 | `Report.pdf` (≤ 15 pages, 12 pt, no source code) covering operation, challenges, lessons, references |
| NFR-5 | `<GroupID>/Code/` + `<GroupID>/Report.pdf` → `<GroupID>.zip` packaging script |

## 4. Scope

### 4.1 In Scope

1. **Shared Bitcoin utility module** (`btc_utils.py` or `common/`):
   - UTXO lookup via a public testnet explorer API (Esplora).
   - Fee estimation (static sat/vByte target with configurable fallback).
   - Transaction construction helpers implementing the PDF's implied API:
     `create_txin`, `create_txout`, `create_signed_transaction` (P2PKH **and** P2SH/multisig variants), `broadcast_tx`.
   - Change-output logic so spends don't overpay fees.
   - Key/address/UTXO persistence to `.secrets/wallet.json` (git-ignored and excluded from packaging).
2. **Task 1 script** — full P2PKH lock & spend lifecycle on testnet.
3. **Task 2 script** — full 2-of-2 multisig P2SH lock & spend lifecycle on testnet, with the `OP_0` dummy element handled.
4. **Validation before broadcast** — verify scripts locally with the library's `VerifyScript`; when a Bitcoin Core RPC is available, also require `testmempoolaccept` so policy, fee, and serialization failures are caught without broadcasting.
5. **Documentation set** (this directory) and the **Report** content source (markdown → PDF), satisfying all §7 report requirements.
6. **Packaging script** producing the exact submission zip layout.

### 4.2 Out of Scope

- SegWit (bech32/P2WPKH/P2WSH) and Taproot — the lab specifies legacy P2PKH and P2SH only.
- Mainnet operations of any kind.
- Running a full node (public testnet APIs suffice).
- GUI/wallet software — CLI scripts only (an executable is optional per §7).
- 3-of-x or M-of-N generalization beyond what Task 2 needs (a parameterized helper is fine, but no extra tasks).
- HTLCs, timelocks (OP_CHECKLOCKTIMEVERIFY is introduced in the PDF as background only).

## 5. Success Criteria (measurable)

| # | Criterion | Verification |
|---|---|---|
| SC-1 | P2PKH address receives faucet funds (lock confirmed on testnet) | Explorer shows ≥ 1 confirmation on the funding tx |
| SC-2 | P2PKH spend tx is broadcast and confirmed; script validates on-chain | Txid visible & confirmed; input's scriptSig contains pubkey + signature |
| SC-3 | Multisig P2SH address receives funds | Explorer shows ≥ 1 confirmation |
| SC-4 | Multisig spend with both signatures broadcast & confirmed | Txid visible; scriptSig = `OP_0 sig1 sig2 <redeemScript>` |
| SC-5 | Negative test: spending multisig with only one signature **fails** script evaluation | Offline script execution returns false (or tx rejected) — demonstrates the security property |
| SC-6 | Report ≤ 15 pages, 12 pt, no source code, includes all §7 sections + references | Manual checklist against §7 |
| SC-7 | Submission zip matches `<GroupID>/Code/...`, `<GroupID>/Report.pdf` | Packaging script dry-run + manual check |

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Faucet exhaustion / rate limits | Blocks lock step | Try multiple faucets; retry with backoff; small requested amounts |
| Testnet3 vs Testnet4 API divergence | Breaks UTXO/broadcast helpers | Abstract network choice behind one config constant |
| `python-bitcoinlib` signing quirks (SIGHASH defaults, P2SH handling) | Invalid signatures, wasted debugging | Validate offline before broadcasting; pin library version |
| Dust thresholds / fee too low → tx stuck | Spend never confirms | Fee estimator with floor; RBF not required but documented |
| Random keys lost between lock and spend | Funds permanently unspendable | Persist keys to git-ignored wallet file immediately on generation |
| Team member parity (one person's machine holds keys) | Bus factor | Assign a testnet key custodian; back up only through an agreed secure channel, never through Git or the report; document the recovery procedure without exposing key material |

## 7. Deliverables Summary

1. `code/` — Python project (utils + Task 1 + Task 2 + offline tests).
2. `docs/` — requirements analysis, this scope document, implementation plan.
3. `report/` — report source (markdown/LaTeX) and final `Report.pdf`.
4. `package_submission.py` (or `.ps1`) — builds `<GroupID>.zip` per §7.
