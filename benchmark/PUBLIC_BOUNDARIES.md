# CloudBench — public boundaries

CloudBench is an **open, agent-neutral benchmark**. This doc states what the public
project claims — and what belongs elsewhere.

---

## CloudBench is

- A **measurement standard** for repo → cloud deployment (tiered L1–L4)
- A **progressive service ladder** (building blocks + service atlas)
- A **community leaderboard** and failure export format
- **Independent** of any single agent vendor

CloudBot (in `cloudbot-paper2`) is the **reference pipeline** we score first.

---

## CloudBench is not

- A training dataset product for one company
- A claim about AGI or autonomous self-hosting
- A commitment to score “all 100 AWS services” in v1
- A substitute for CloudBot product/strategy docs (those live in private notes)

---

## Where vision and strategy live

| Need | Location |
|------|----------|
| Public benchmark goal | [`PUBLIC_VISION.md`](PUBLIC_VISION.md) |
| Leaderboard / failures | [`LEADERBOARD.md`](LEADERBOARD.md), [`FAILURE_REGISTRY.md`](FAILURE_REGISTRY.md) |
| Full CloudBot north star | **Private** — kept in the maintainers' local notes, not in this repo |

The benchmark's public scope is everything in this repository; CloudBot product and strategy notes are kept privately by the maintainers and are not part of CloudBench.

---

## Safe improvement loop (public wording)

Failed runs → standard failure JSON → **any** team improves agents/RAG/repair.  
The CloudBot reference pipeline uses the same format; the benchmark is not “for CloudBot only.”

Details: [`TRAINING_LOOP.md`](TRAINING_LOOP.md).
