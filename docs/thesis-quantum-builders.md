# User Message — 2026-09-08 (Word-for-Word)

QRL is interesting, but I’d define its moat carefully:

> **QRL’s moat is not “we know a secret quantum-proof algorithm.”**
> ML-DSA/XMSS are public standards.
> Its moat is **being a long-running, quantum-native financial network plus years of cryptographic engineering, audits, wallets, migration machinery and now an EVM-like PQ smart-contract stack.**

That is much harder to reproduce overnight.

## What QRL actually owns

QRL 1.x has been operating since 2018 with post-quantum signatures from genesis. That means it does not carry the same historical baggage as a chain that has millions of old ECDSA keys which someday need migrating. Its core cryptographic implementations have also gone through multiple audits; a 2026 Halborn audit found no cryptographic vulnerabilities in the reviewed PQ libraries, and QRL's latest September 4 update says the Ledger signing implementation matched its independently audited reference implementation byte-for-byte. ([QRL][1])

Now they're doing the much more ambitious part:

**QRL 2.0 / Zond**

```text
Post-quantum L1
        +
Proof of Stake
        +
ML-DSA-87
        +
XMSS option
        +
QRVM (EVM-derived)
        +
Hyperion (Solidity-derived)
        +
smart contracts
```

QRL 2.0 Testnet V2 launched March 31, 2026. Validators must use stateless ML-DSA; ordinary wallets can use either XMSS or ML-DSA. Mainnet has **no fixed date yet** and is explicitly contingent on audits and network stability. ([QRL][2])

That last fact matters. This is still genuinely early.

### My moat assessment

I'd score it roughly:

**Cryptographic algorithm moat: 2/10** — open standards.

**Engineering moat: 7/10** — making PQ crypto work safely everywhere is difficult.

**Operational-history moat: 8/10** — eight years is meaningful.

**Network moat today: 3/10** — tiny ecosystem/liquidity versus ETH/SOL.

**Quantum-brand/reputation moat: 8/10** — if Q-Day suddenly moves forward, QRL is one of the obvious names people discover.

**Potential QRL 2.0 moat: maybe 8/10**, *if* it launches safely and gets developers/liquidity before Ethereum completes its own PQ migration.

That's the bull case.

The bear case is simple:

> Ethereum successfully becomes post-quantum safe, and nobody needs to migrate anywhere.

So QRL needs to become more than **“the quantum-resistant coin.”**

It needs an ecosystem.

And that is exactly why **right now is an interesting time to build on it.**

---

# What I would build on QRL

There are a lot of obvious DeFi clones. I wouldn't bother starting with those.

I'd build things that only become more important in an **AGI + quantum** future.

### 1. Quantum-safe agent wallets

This is probably my favourite for you.

Imagine:

```text
Agent
 ↓
PQ identity
 ↓
QRL wallet
 ↓
policy contract
 ├─ maximum $10/day
 ├─ only approved counterparties
 ├─ x402 purchases allowed
 ├─ cannot withdraw treasury
 └─ every action cryptographically attributed
```

Call it something like a **PQ Agent Vault**.

The clever part isn't merely storing crypto.

You solve:

> How does an autonomous AGI hold authority without possessing unrestricted control?

The agent has an ML-DSA identity and gets scoped spending capabilities.

That connects almost perfectly with the authorization/principalhood thesis we were discussing.

QRL 2.0's Hyperion compiler is specifically being extended with lattice primitives such as **native ML-DSA-87 verification**, so this is not completely artificial positioning. ([QRL][3])

And it could eventually work across chains.

---

## 2. Q-Day migration scanner

This may be an actual business.

Input:

```text
wallet
contract
DAO
company
crypto treasury
```

Output:

```text
QUANTUM RISK

ECDSA keys exposed: 37
Funds at exposed addresses: $4.2m
PQ migration readiness: 14/100

Recommended:
→ rotate these keys
→ migrate these contracts
→ switch signing infrastructure
→ archive proof
→ deploy PQ recovery account
```

Initially this can support Ethereum/Bitcoin/company PKI.

Eventually:

> **one-click migration into QRL 2.0**

That gives you a business **before Q-Day**.

Very interesting.

---

# 3. Quantum-safe x402

This might be Feedify-related.

Today:

```text
Agent
→ x402
→ USDC
→ API
```

Eventually:

```text
AGENT A
   ↓ ML-DSA identity
PQ payment authorization
   ↓
AGENT B
   ↓
API/data/service
```

So build something like:

### `pq402`

An x402-compatible payment/authorization scheme that can prove:

* which autonomous agent paid
* authorization limits
* service purchased
* timestamp
* PQ signature
* reputation/history.

AGI massively increases machine-machine payments.

Quantum risk massively increases the importance of cryptographic identity.

That's a surprisingly coherent intersection.

---

# 4. Post-quantum provenance

Another good AGI × QRL combination.

If AI can generate:

* documents
* contracts
* videos
* models
* software
* scientific discoveries

at enormous scale, provenance becomes more valuable.

Build:

### `PQProof`

```text
file/model/document
        ↓
hash
        ↓
ML-DSA signature
        ↓
QRL timestamp
        ↓
immutable provenance record
```

Then:

> “This model checkpoint existed at this date and was signed by this organization.”

Or:

> “This scientific dataset is the exact dataset associated with this paper.”

Or even:

> “This agent generated this artifact under this authority.”

That's not dependent on speculative DeFi demand.

---

# 5. Quantum-safe company treasury

A proper product:

**QRL Safe**

Think Gnosis Safe, but designed around PQ custody.

Features:

* ML-DSA multisig
* spending policies
* agent permissions
* human recovery
* hardware wallets
* timelocks
* key rotation
* crypto-agility
* audit log.

Corporations eventually need this stuff regardless of whether they care about QRL as an investment.

---

# 6. PQ bridge / migration infrastructure

When QRL 2.0 mainnet launches, this could become one of the most valuable pieces of ecosystem infrastructure.

QRL explicitly intends holders to migrate from 1.x through a decentralized smart-contract-based mechanism rather than a centralized swap. ([QRL][2])

Then think larger:

```text
Ethereum asset
      ↓
bridge / proof
      ↓
quantum-safe representation
      ↓
QRL 2.0
```

There is substantial technical/security work here.

A good bridge, migration SDK or cross-chain wallet could become infrastructure.

---

# 7. QRL developer infrastructure

This is less glamorous but potentially easier money.

Right now the ecosystem is tiny.

That means lots of gaps:

* hosted QRL RPC
* indexed blockchain API
* event/webhook service
* block explorer APIs
* wallet SDK
* TypeScript SDK
* Python SDK
* validator monitoring
* staking dashboards
* multisig interfaces
* transaction simulation
* testnet faucet
* contract explorer
* QRL version of Etherscan verification
* QRL version of Tenderly
* PQ wallet-as-a-service
* enterprise HSM integrations.

The testnet can even be spun up privately using **Kurtosis + Docker/Kubernetes**, including execution nodes, consensus nodes, validators, monitoring and transaction spam tooling. ([QRL][4])

This is an unusually good playground.

---

# 8. Become an early QRL 2.0 validator operator

This is worth doing just to understand the technology.

Current 2.0 is Proof-of-Stake.

You can:

```text
run gqrl
+
run Qrysm beacon node
+
run validator
+
use ML-DSA validator keys
```

QRL's consensus implementation **Qrysm** derives from Ethereum Prysm, while `go-qrl` derives from geth, so you're simultaneously learning a lot about modern Ethereum architecture. ([GitHub][5])

Test QRL is free; QRL recommends asking in the testnet Discord channel. ([QRL][6])

That's where I would start this week.

---

# You can also still mine QRL right now

Current QRL 1.x remains:

### Proof-of-Work / RandomX

The same CPU-oriented algorithm family used by Monero.

You can use **XMRig** and either:

* pool mine
* solo mine through your own QRL node
* actually operate a mining pool.

QRL's docs explicitly support all three. ([The QRL Documentation][7])

Current network statistics are roughly:

* ~50 MH/s network hash rate
* ~1.296 QRL/block
* 60-second target
* ~12 pools
* ~300 miners/nodes depending on the snapshot.

([Minerstat][8])

But I would mine as **education**, not as a money strategy.

A rented VPS is almost certainly a terrible mining business because you're paying retail cloud prices for CPU time.

And more importantly:

### mining is going away with QRL 2.0.

2.0 switches to PoS. ([QRL][9])

So learning:

**node → wallet → transaction → mining → block explorer**

is worthwhile.

Buying CPU farms for QRL mining is not a thesis I'd pursue.

---

# There are also bug bounty / grant routes

QRL runs a bug bounty covering actively developed public repositories, including nodes, crypto libraries, wallets and supporting tools. ([QRL][10])

And the QRL Foundation explicitly funds:

* open-source development
* PQ blockchain work
* research
* education.

([QRL Foundation][11])

That's interesting for you because you could potentially make your learning project partially self-financing.

Rather than:

> “learn quantum someday”

you could become:

> **the guy building PQ agent infrastructure on QRL while learning actual quantum computing separately.**

Much better trajectory.

---

# Important distinction: QRL isn't learning quantum computing

This is worth emphasizing.

QRL teaches you:

### Post-quantum cryptography

```text
XMSS
ML-DSA
hash signatures
lattice cryptography
key management
PQC migration
blockchain cryptography
```

It does **not** teach you:

```text
qubits
superposition
entanglement
quantum circuits
Shor
Grover
Hamiltonians
error correction
quantum algorithms
```

For those, use Qiskit.

Do both in parallel.

---

# And Qiskit is amazingly cheap to start now

IBM's **Open Plan remains free** and currently gives you up to **10 minutes of actual quantum hardware runtime every 28 days**. Active users can also qualify for a one-time additional 180 minutes. ([IBM][12])

Ten QPU minutes sounds tiny.

It isn't when you're learning.

You can spend essentially unlimited time locally building/simulating circuits and only submit the final experiment to the hardware.

AWS Braket is also much cheaper at the low end than the $4,000/hour reservation numbers make it sound.

For example Rigetti Cepheus currently costs:

**$0.30/task + $0.000425/shot.**

So 100 shots is only about:

**$0.34.**

You don't need to rent the QPU for an hour. ([Amazon Web Services, Inc.][13])

Braket's local simulator is free as well. ([Amazon Web Services, Inc.][13])

So you can genuinely become competent for nearly nothing.

---

# I'd run this learning track

### Phase 1 — this week: QRL

Run:

```text
QRL 1.x wallet
↓
receive tiny QRL
↓
send transaction
↓
understand XMSS + OTS
↓
run node
↓
XMRig pool mining
```

You'll immediately learn one of the weirdest aspects of hash-based signatures: QRL 1.x XMSS signatures are **stateful**. An OTS index can only be used once; reuse can compromise security. ([The QRL Documentation][14])

That's genuinely useful cryptography knowledge.

### Phase 2 — QRL 2.0

```text
clone go-qrl
clone qrysm

↓
run Testnet V2
↓
make ML-DSA wallet
↓
run validator
↓
deploy Hyperion contract
↓
make tiny dApp
```

There's already a contract example and Web3 extension. ([QRL][15])

### Phase 3 — actual quantum

Learn Qiskit:

```text
|0⟩ / |1⟩
Hadamard
CNOT
measurement
Bell states
teleportation
Grover
phase estimation
Shor
noise
error mitigation
error correction
```

Run locally → IBM hardware.

### Phase 4

Implement tiny versions of:

**Shor versus RSA/ECC**

then:

**Grover versus symmetric crypto**

then:

**why ML-DSA/XMSS survive them.**

At that point QRL stops being marketing language and you'll actually understand what it's protecting against.

---

# The project I'd personally have you build first

I'd combine all of this:

## **Q-Day Lab**

A web app / open-source toolkit.

You enter:

```text
BTC address
ETH address
SSH key
TLS certificate
public key
crypto wallet
```

It shows:

```text
Classical algorithm:
ECDSA secp256k1

Known quantum attack:
Shor

Current vulnerability:
LOW / MEDIUM / FUTURE CRITICAL

Estimated migration complexity:
████████░░

PQ alternatives:
ML-DSA
SLH-DSA
XMSS

QRL compatibility:
YES

Live quantum capability:
IBM / Google / Quantinuum etc

Migration status:
NOT READY
```

Then include actual educational Qiskit demos explaining the attack.

And eventually:

### `Migrate to PQ`

That's legitimately a potential startup.

It gives you exposure to:

**quantum computing + cybersecurity + PQC + QRL + crypto + agent infrastructure.**

---

# Recent QRL activity is actually quite healthy

The sequence matters:

**March 31:** QRL 2.0 Testnet V2. ([QRL][2])

**April 3:** Halborn audit of two core PQ signature packages; no cryptographic vulnerabilities identified. ([QRL][1])

**June:** Falcon-1024 work entered the P2P layer; team independently checked its ML-DSA implementation against newly published attack classes and says none applied. ([QRL][16])

**August 4:** additional `go-qrllib` audit results published. ([QRL][17])

**September 4:** Ledger-app audit completed, no critical or crypto concerns; remediation underway. Overall 2.0 audit progress is reported at ~50%, rising to ~55% once Ledger remediation is completed. ([QRL][18])

And their weekly commits show active work in `qrysm`, `go-qrl`, Web3.js, wallet and testing rather than a dormant 2017 coin pretending quantum is trendy. ([QRL][19])

That's one of the things I like about it.

---

# Buying QRL without MEXC

There is finally a somewhat better answer.

### Easiest looking route: Banxa

Banxa's **current supported-assets documentation lists native QRL as both buy and sell supported**. ([Banxa][20])

So in principle:

```text
fiat
↓
Banxa
↓
native QRL
↓
your QRL wallet
```

is much cleaner than buying USDT → MEXC → QRL.

**However:** QRL's own markets page currently labels its Banxa route **“Under Maintenance”** and says Banxa uses MEXC on the backend. So I would verify that the checkout actually offers QRL before paying anything. ([QRL][21])

### BitMart

BitMart listed **QRL/USDT** in October 2025 and its trading page has subsequently shown live QRL trading. ([Bitmart][22])

That would be my first CEX alternative to check.

### Biconomy / XT

CoinGecko currently sees:

**MEXC** as largest volume, then **Biconomy.com**, then **XT.com**. QRL's total daily liquidity is still tiny—only tens of thousands of dollars—so spreads matter. ([CoinGecko][23])

### SwapSpace

Also easier UX:

```text
BTC/ETH/etc.
↓
SwapSpace
↓
native QRL address
```

SwapSpace currently exposes QRL swap routes. ([SwapSpace][24])

But QRL says the currently listed underlying provider is LetsExchange, which in turn uses MEXC, and its official markets page presently labels that path under maintenance too. ([QRL][21])

So the liquidity problem hasn't magically disappeared.

### Or mine it

You can literally make a QRL wallet, point XMRig at a pool and earn your first tiny quantity yourself.

For learning, that is actually the coolest option.

---

## One warning when buying

**QRL is its own blockchain.**

It is **not ERC-20**.

Do not buy some random `"QRL"` contract on Ethereum/Solana thinking it is the same asset. QRL explicitly warns about this. ([QRL][21])

And because current liquidity is extremely thin, I'd treat market orders very carefully. A ~$50M asset with ~$20–30k daily genuine-looking volume is not equivalent to buying ETH. ([CoinGecko][23])

---

### The bigger opportunity

I don't think your highest-upside move here is merely buying QRL.

It's:

> **become technically competent in quantum + PQ cryptography while the field is still weird, difficult and commercially immature.**

Do Qiskit on free real QPUs, operate QRL 1.x, become an early QRL 2.0 validator/developer, and build **Q-Day Lab + PQ agent-wallet infrastructure**.

If quantum timelines suddenly compress from “2035ish” to “holy shit, five years,” you'd then have exactly the asset our AGI thesis says becomes valuable:

**not generic intelligence, but accumulated technical state, code, reputation and infrastructure in a suddenly scarce domain.**

[1]: https://www.theqrl.org/press/halborn-audit-validates-qrls-postquantum-cryptography-library/?utm_source=chatgpt.com "Halborn Audit Validates QRL's Post-Quantum Cryptography Library"
[2]: https://www.theqrl.org/press/qrl-launches-testnet-v2-for-its-postquantum-evmfriendly-blockchain/?utm_source=chatgpt.com "QRL Launches Post-Quantum Smart Contract Testnet Ahead of 2.0 Mainnet"
[3]: https://www.theqrl.org/2/?utm_source=chatgpt.com "QRL 2.0: A blockchain engineered for the post-quantum world"
[4]: https://test-zond.theqrl.org/testnet/usage/kurtosis?utm_source=chatgpt.com "QRL 2.0 | Private QRL 2.0 Network with Kurtosis"
[5]: https://github.com/theQRL/qrysm?utm_source=chatgpt.com "GitHub - theQRL/qrysm · GitHub"
[6]: https://test-zond.theqrl.org/testnet/usage/getting-zond?utm_source=chatgpt.com "QRL 2.0 | Acquiring Test QRL"
[7]: https://docs.theqrl.org/use/wallet/overview/?utm_source=chatgpt.com "Mining QRL Overview | QRL Docs"
[8]: https://minerstat.com/coin/qrl?utm_source=chatgpt.com "Mining QRL Overview | QRL Docs"
[9]: https://www.theqrl.org/roadmap/?utm_source=chatgpt.com "QRL Roadmap"
[10]: https://www.theqrl.org/bug-bounty/?utm_source=chatgpt.com "QRL Bug Bounty Program"
[11]: https://qrl.foundation/development?utm_source=chatgpt.com "Development"
[12]: https://www.ibm.com/quantum/products?utm_source=chatgpt.com "IBM Quantum Computing | Products and services"
[13]: https://aws.amazon.com/braket/pricing/?utm_source=chatgpt.com "Amazon Braket Pricing"
[14]: https://docs.theqrl.org/use/wallet/overview/?utm_source=chatgpt.com "QRL Web Wallet | QRL Docs"
[15]: https://test-zond.theqrl.org/testnet/usage/contract-example?utm_source=chatgpt.com "QRL 2.0 | QRL 2.0 smart contract example"
[16]: https://www.theqrl.org/weekly/2026-june-19/?utm_source=chatgpt.com "QRL Weekly, 2026-June-19"
[17]: https://www.theqrl.org/weekly/2026-august-07/?utm_source=chatgpt.com "QRL Weekly, 2026-August-07"
[18]: https://www.theqrl.org/weekly/2026-september-04/?utm_source=chatgpt.com "QRL Weekly: Ledger app audit is complete, 2026-September-04"
[19]: https://www.theqrl.org/weekly/2026-august-21/?utm_source=chatgpt.com "QRL Weekly, 2026-August-21"
[20]: https://docs.banxa.com/products/hosted-checkout/docs/reference/supported-cryptocurrencies-and-blockchains?utm_source=chatgpt.com "Supported Cryptocurrencies & Blockchains"
[21]: https://www.theqrl.org/markets/ "QRL Markets"
[22]: https://www.bitmart.com/en-US/support/articles/7923014477723/360000908874/42061923119131?utm_source=chatgpt.com "[Primary Listing] BitMart Will List Quantum Resistant Ledger (QRL) - 2025-10-21 | BitMart Support"
[23]: https://www.coingecko.com/en/coins/quantum-resistant-ledger/historical_data?utm_source=chatgpt.com "Quantum Resistant Ledger Price History: Download QRL Historical Data | CoinGecko"
[24]: https://swapspace.co/exchange/qrl?utm_source=chatgpt.com "Exchange Quantum Resistant Ledger (QRL) | Swap Crypto with SwapSpace Exchange Aggregator"

*Saved word for word. No summarization. No condensation.*
