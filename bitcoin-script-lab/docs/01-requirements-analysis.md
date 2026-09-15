# Lab 03 — Requirements Analysis

**Course:** Blockchain (2026), Knowledge Engineering Department
**Lab:** Understanding Bitcoin's Scripting Language
**Source:** `Lab03.pdf` (6 pages)
**Status:** Analyzed — drives [02-objectives-and-scope.md](02-objectives-and-scope.md) and [03-implementation-plan.md](03-implementation-plan.md)

---

## 1. Source Document Summary

The lab builds a deeper understanding of **Bitcoin Script** — the stack-based, non-Turing-complete language that defines spending conditions in Bitcoin transactions. It progresses from a single-key payment (P2PKH) to a multi-key escrow-style payment (2-of-2 multisig inside P2SH), and closes with a written analysis.

| Section | Content |
|---|---|
| §1 Objective | Understand Bitcoin Script and how it operates in the network |
| §2 Prerequisites | Bitcoin basics: addresses, transactions/UTXO, Script opcodes, P2PKH vs P2SH |
| §3 Tools | Testnet wallet, Script documentation, code editor (Python suggested), testnet faucet |
| §4 Task 1 | Create a P2PKH script, lock funds, spend locked funds |
| §5 Task 2 | Create a 2-of-2 multisig (P2SH), lock funds, spend from the multisig address |
| §6 Task 3 | Report: experiences, insights, advantages and limitations of Bitcoin Script |
| §7 Submission | Strict folder/zip structure; Report.pdf ≤ 15 pages; zero-tolerance rules |

### Prerequisite concepts the lab expects us to command

- **Keys & addresses** — private key → public key → Bitcoin address derivation.
- **UTXO model** — transaction inputs reference unspent outputs of earlier transactions; outputs define destinations and amounts.
- **Script mechanics** — a stack machine of opcodes evaluated by network nodes: `OP_DUP`, `OP_HASH160`, `OP_EQUALVERIFY`, `OP_CHECKSIG`, `OP_CHECKMULTISIG`, `OP_CHECKLOCKTIMEVERIFY`.
- **Script types** — P2PKH locks funds to a single public-key hash; P2SH hides an arbitrary redeem script behind a script hash.

---

## 2. Evaluation Criteria (what the graders check)

1. **Task 1 (§4.4):** code *successfully locks and unlocks funds*; results and encountered issues are discussed.
2. **Task 2 (§5.4):** ability to *create and spend funds from a multisig address*; discussion of the security benefits of multisig.
3. **Task 3 (§6.3):** reflections and understanding of the practical applications of Bitcoin Script.
4. **Submission (§7):** compliance with folder/zip/report regulations — non-compliance scores **0**; plagiarism scores **0 for the entire course**.

---

## 3. Functional Requirements

### Task 1 — Basic Script Execution (P2PKH)

| ID | Requirement | Source |
|---|---|---|
| FR-1.1 | Generate a random private key, derive the public key and the P2PKH Bitcoin address, and print all three. | §4.3 |
| FR-1.2 | Lock funds: receive testnet BTC from a faucet at the generated address. | §4.3 |
| FR-1.3 | Spend locked funds: build a transaction input from a UTXO (`txid`, `output_index`), an output to a destination address (`amount_to_send` in satoshis), sign it with the private key, and broadcast it. | §4.3 |

### Task 2 — Multisignature Transactions (2-of-2 P2SH)

| ID | Requirement | Source |
|---|---|---|
| FR-2.1 | Generate two random private keys and derive both public keys. | §5.3 |
| FR-2.2 | Build the redeem script `OP_2 <pubkey1> <pubkey2> OP_2 OP_CHECKMULTISIG`. | §5.3 |
| FR-2.3 | Derive the P2SH address from the redeem script; print keys, redeem script (hex), and address. | §5.3 |
| FR-2.4 | Lock funds to the multisig address via a testnet faucet. | §5.3 |
| FR-2.5 | Spend from the multisig address with a transaction signed by **both** private keys, supplying the redeem script, and broadcast it. | §5.3 |
| FR-2.6 | Discuss the security benefits of multisig addresses. | §5.4 |

### Task 3 — Analysis & Reflection

| ID | Requirement | Source |
|---|---|---|
| FR-3.1 | Write a report summarizing experiences and insights from the lab. | §6.2 |
| FR-3.2 | Discuss the advantages and limitations of Bitcoin Script. | §6.2 |
| FR-3.3 | Cover, in the report: system operation (flow, key components, interactions), challenges and how they were overcome, lessons learned. | §7 |

---

## 4. Non-Functional Requirements & Constraints

| ID | Constraint | Source |
|---|---|---|
| NFR-1 | All on-chain work happens on **Bitcoin testnet** — no mainnet funds at risk. | §3 |
| NFR-2 | Report: **at most 15 pages, single page (single-sided), 12 pt font**, PDF format, Vietnamese or English. | §7 |
| NFR-3 | Report must **not contain source code** — describe operation in prose/diagrams instead. | §7 |
| NFR-4 | Report must include: team member information, project structure, design/implementation remarks, and **all related links and books**. | §7 |
| NFR-5 | Submission folder `<Group's ID>/` containing `<Code>/` (whole project), optional executable, `Report.pdf`; compressed as `<Group's ID>.zip`. | §7 |
| NFR-6 | Originality: plagiarism/cheating ⇒ 0 for the entire course. | §7 |

---

## 5. Gaps & Technical Issues Identified in the Provided Code

The PDF supplies reference snippets, but several things are **not provided** and must be designed by us. These are the actual engineering work of the lab:

1. **The snippets are illustrative, not directly executable.** They omit `import os`, use broad wildcard imports, and reference `create_txin`, `create_txout`, `create_signed_transaction`, and `broadcast_tx`, none of which are standard `python-bitcoinlib` APIs. We must supply explicit imports and implement these helpers.
2. **Fees are ignored in the snippets.** A real spend must pay a miner fee: either spend the whole UTXO minus fee to the destination, or add a **change output** back to the sender. Otherwise the transaction may be rejected or overpay.
3. **OP_CHECKMULTISIG off-by-one bug.** The opcode pops one extra element, so the unlocking script must start with a dummy `OP_0` — the classic consensus bug that must be reproduced correctly for Task 2 to work.
4. **P2SH spending structure.** For Task 2 the scriptSig must be `[OP_0, sig1, sig2] <serialized redeem script>`; the signing hash must be computed over the redeem script, not the P2SH scriptPubKey.
5. **Network choice.** Bitcoin testnets: Testnet3 (legacy, widely supported by existing educational tooling) vs Testnet4 (newer). The library, faucet, explorer/RPC endpoint, address display, and broadcast target must all use the same network.
6. **UTXO discovery.** The snippets hardcode `txid`/`output_index`; we should fetch them programmatically from a testnet explorer API (e.g. Blockstream Esplora) to avoid manual copy/paste errors.
7. **Broadcasting.** `broadcast_tx` needs a network endpoint — a public testnet API or local node.
8. **Key persistence.** Keys are generated randomly at runtime; to lock then later spend, keys/UTXO metadata must be persisted locally (never committed, packaged, placed in the report, or captured in screenshots).
9. **The prose and snippets disagree about supplied material.** §4.2 says a testnet address will be provided, while §4.3 generates one; §5.2 says public keys are provided, while §5.3 generates two key pairs. The implementation should support generated keys by default and accept instructor-provided values if supplied.

---

## 6. Assumptions

- A-1: Python 3 is the implementation language (matches all PDF snippets).
- A-2: `python-bitcoinlib` is the intended library (its `bitcoin.wallet.CBitcoinSecret` / `P2PKHBitcoinAddress` / `P2SHBitcoinAddress` APIs match the snippets exactly).
- A-3: Public testnet faucets and explorer APIs are available and rate-limited but usable for the small amounts this lab needs.
- A-4: The report is written in English (Vietnamese also permitted by §7).

## 7. Open Questions (to confirm with the instructor/team)

- Q-1: Is a specific testnet (3 or 4) required, or is either acceptable? *(Default plan: use the network with the most reliable faucet support at run time.)*
- Q-2: What is the Group ID to use in the submission folder/zip name?
- Q-3: Does "single page" in §7 mean single-sided printing? *(Assumed yes; it does not change content.)*
- Q-4: Is a short demo video or executable expected alongside the code? *(§7 marks the executable optional.)*
- Q-5: Will the instructor actually provide the Task 1 address and Task 2 public keys, or should every group generate its own as shown in §§4.3 and 5.3? *(Default plan: generate our own, with optional inputs for supplied values.)*
