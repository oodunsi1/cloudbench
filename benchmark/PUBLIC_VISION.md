# CloudBench — public vision

CloudBench aims to be the **standard check** when someone asks: *can this model or
agent deploy a real application from GitHub into the cloud?*

When OpenAI, Anthropic, or a research lab ships a new model, CloudBench should be
on the same short list as SWE-bench (code) and IaC-Eval (infrastructure templates)
— but for the **full repo → cloud → run app** path.

---

## Who uses CloudBench

| User | Typical use |
|------|-------------|
| **Model providers** | Run **L1** on every model release (no AWS cost). Optional L3–L4 on a subset for deploy claims. |
| **Researchers** | Submit custom agents, RAG stacks, or ablations; compare to CloudBot reference. |
| **Agent builders** | Measure whether adding memory, repair, or tools improves deploy success. |

CloudBench is **agent-neutral**. CloudBot (Analyst → Architect → Engineer → Repair)
is the **reference implementation**, not the only allowed entrant.

---

## What we measure (plain language)

1. Look at a **GitHub app repo**.
2. Figure out what cloud resources it needs.
3. Produce valid infrastructure (Terraform in v1).
4. Optionally deploy, run the app, prove it works, tear down.

Scores are **tiered** so cheap checks (L1) are separate from full deploy (L4).
See [`SCHEMA.md`](SCHEMA.md).

---

## Why a progressive ladder

Cloud skills stack: if a system cannot provision **one server**, it will fail when
the app also needs **storage + database + load balancer**. CloudBench starts simple
(B0: EC2 only) and adds services step by step. See [`BUILDING_BLOCKS.md`](BUILDING_BLOCKS.md)
and [`SERVICE_ATLAS.md`](SERVICE_ATLAS.md).

Leaderboard rows are **stratified by service** (e.g. CloudBench AWS EC2 vs AWS S3),
not one opaque score.

---

## Open improvement loop

Failed runs export a **standard failure record** ([`FAILURE_REGISTRY.md`](FAILURE_REGISTRY.md))
so any team can diagnose and improve. The CloudBot reference pipeline may consume
the same format; the benchmark belongs to the community. See [`PUBLIC_BOUNDARIES.md`](PUBLIC_BOUNDARIES.md).

---

## How to participate

1. Run cases with your agent or model.
2. Score with `bench score` ([`../harness/`](../harness/)).
3. Submit results per [`LEADERBOARD.md`](LEADERBOARD.md).
4. Propose new cases via service atlas gaps ([`SERVICE_ATLAS.md`](SERVICE_ATLAS.md)).

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [`NAMING.md`](NAMING.md) | CloudBench AWS EC2 / S3 / … naming |
| [`LEADERBOARD.md`](LEADERBOARD.md) | Submission format |
| [`SERVICE_ATLAS.md`](SERVICE_ATLAS.md) | Service coverage roadmap |
| [`FAILURE_REGISTRY.md`](FAILURE_REGISTRY.md) | Failure export schema |
| [`TRAINING_LOOP.md`](TRAINING_LOOP.md) | Public improvement loop |
