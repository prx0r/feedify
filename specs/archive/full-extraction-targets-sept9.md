# Full Extraction Targets

## Technical Accounts (New)

| Account | August | Total | Priority | Why |
|---------|--------|-------|----------|-----|
| **@Tim_Dettmers** | ✅ 19 | 21 | HIGH | Memory bottleneck guy, QLoRA, bitsandbytes |
| **@clattner_llvm** | ✅ 16 | 20 | HIGH | LLVM, Swift, MLIR, Mojo/MAX |
| **@awnihannun** | ✅ 9 | 20 | HIGH | MLX, Apple ML, local inference |
| **@dylan522p** | ✅ 9 | 20 | HIGH | SemiAnalysis, CoWoS+HBM |
| **@GavinSBaker** | ✅ 6 | 17 | HIGH | Atreides, transformers Mar 2023 |
| **@tri_dao** | ✅ 2 | 21 | HIGH | FlashAttention, memory hierarchy |
| **@jimkxa** | ❌ 0 | 21 | MEDIUM | Jim Keller, Tenstorrent |
| **@CJHandmer** | ❌ 0 | 23 | MEDIUM | Terraform Industries, solar |
| **@AdamMarblestone** | ❌ 0 | 20 | MEDIUM | Convergent Research, science infra |
| **@Ben_Reinhardt** | ❌ 0 | 21 | MEDIUM | Speculative Technologies |
| **@Thom_Wolf** | ❌ 0 | 19 | MEDIUM | Hugging Face, open AI |

## Investment Accounts (Priority 1)

| Account | August | Total | Priority | Why |
|---------|--------|-------|----------|-----|
| **@ArjunNMurti** | ✅ 12 | 20 | HIGH | AI electricity demand |
| **@FootnotesFirst** | ✅ 3 | 20 | HIGH | Mike Alkin, uranium 2018 |
| **@energybants** | ✅ 3 | 20 | HIGH | Mark Nelson, nuclear |
| **@firstadopter** | ✅ 1 | 21 | HIGH | Tae Kim, NVDA+VRT+SMCI |

## Accounts Without August Data (Need Alternative Sources)

| Account | Status | Alternative |
|---------|--------|-------------|
| @jimkxa | No August | Blog posts, interviews |
| @CJHandmer | No August | Blog posts |
| @AdamMarblestone | No August | Papers, blog |
| @Ben_Reinhardt | No August | Blog posts |
| @Thom_Wolf | No August | HuggingFace blog |
| @p_ferragu | No August | New Street Research |
| @solar_chase | No August | BloombergNEF |
| @ramez | No August | rameznaam.com |
| @xyru_fawkes | Not on X | Buyside Digest, Livewire |

---

## Full Extraction Plan

### For X-Active Accounts ( Priority 1)

1. **@Tim_Dettmers** — Ingest everything. Memory/quantization/inference.
2. **@clattner_llvm** — Ingest everything. Compiler/hardware abstraction.
3. **@awnihannun** — Ingest everything. Local inference, MLX.
4. **@ArjunNMurti** — Ingest everything. Energy/power.
5. **@FootnotesFirst** — Ingest everything. Uranium.
6. **@energybants** — Ingest everything. Nuclear.
7. **@dylan522p** — Ingest long-form only. SemiAnalysis.
8. **@GavinSBaker** — Ingest long-form only. Atreides.
9. **@tri_dao** — Ingest long-form only. FlashAttention.
10. **@firstadopter** — Ingest long-form only. Tae Kim.

### For Non-X Accounts (Priority 1)

1. **Xinyu Ru / Fawkes** — BuySide Digest, Livewire Markets
2. **Pierre Ferragu** — New Street Research
3. **Jenny Chase** — BloombergNEF
4. **Ramez Naam** — rameznaam.com
5. **Jim Keller** — Blog, interviews (Tenstorrent)
6. **Casey Handmer** — caseyhandmer.wordpress.com
7. **Adam Marblestone** — essentialtechnology.blog
8. **Ben Reinhardt** — spec.tech
9. **Thomas Wolf** — HuggingFace blog
10. **Doug O'Laughlin** — Fabricated Knowledge podcast

---

## The Meta-Finding

> **The highest-signal accounts split into two categories:**
>
> 1. **Investment precursors** who noticed structural changes (Xinyu, Mike Alkin, Arjun Murti)
> 2. **Technical architects** who understand the physical constraints (Jim Keller, Tri Dao, Tim Dettmers)
>
> **Feedify needs both.** The investment precursors tell you WHERE scarcity is moving. The technical architects tell you WHY.

---

## Feed Design

### `precursors.feedify.dev`

**Inputs:**
- X posts (daily)
- Blog posts (weekly)
- Fund letters (monthly)
- 13F filings (quarterly)
- Conference talks (as available)

**Scoring:**
1. Lead time (months)
2. Specificity (0-10)
3. Causal depth (0-10)
4. Surprise (0-10)
5. Downstream validity (0-10)
6. Sparse output bonus (0-10)
7. Cross-domain migration (0-10)

**Output:**
- Who noticed what, when
- How far ahead of consensus
- What happened next
- Where are they looking now

**That's the highest-signal feed we can build.**
