# CloudBench leaderboard protocol

How model providers, researchers, and agent builders **submit and compare** results.

v1: JSON files under `experiments/leaderboard/` + tables in the paper.  
v2 (future): hosted site or HuggingFace dataset.

---

## Submission bundle

Each submission is one JSON file (example shape):

```json
{
  "submission_id": "gpt-4o-2026-06-cloudbench-v1",
  "submitter": "Example Labs",
  "agent_or_model": "gpt-4o",
  "agent_type": "multi_agent",
  "cloudbench_harness_version": "0.1.0",
  "cloudbot_commit": "abc123optional",
  "tier_claimed": "L1",
  "timestamp": "2026-06-02T12:00:00Z",
  "cases": [
    {
      "case_id": "uc1",
      "primary_service": "ec2",
      "building_block": "B0",
      "tier": "L1",
      "passed": true,
      "graph_match_score": 1.0,
      "repair_iterations": 0,
      "cost_usd": 0.0
    }
  ],
  "aggregate": {
    "pass_rate_L1": 0.67,
    "pass_rate_L3": null,
    "pass_rate_L4": null,
    "graph_match_mean": 0.92,
    "repair_iterations_mean": 1.2,
    "cost_usd_mean": 0.0,
    "by_primary_service": {
      "ec2": { "pass_rate_L1": 1.0, "n": 3 }
    }
  }
}
```

Produce per-case scores with:

```bash
bench score benchmark/cases/uc1.yaml --tier L1 \
  --archspec path/to/archspec.json \
  --terraform-dir path/to/terraform/ \
  -o experiments/leaderboard/runs/uc1-gpt4o.json
```

Aggregate across cases manually for v1; `bench aggregate` is planned later.

---

## Required reporting columns

| Column | Meaning |
|--------|---------|
| `pass_rate_L1` | Fraction of cases passing artifact tier |
| `pass_rate_L3` | Fraction passing deploy (null if not run) |
| `pass_rate_L4` | Fraction passing workload probes (null if not run) |
| `graph_match_mean` | Mean graph match score (L1) |
| `repair_iterations_mean` | Mean repair loop count |
| `cost_usd_mean` | Mean cloud + API cost per case |
| `by_primary_service` | Stratified pass rates (EC2, S3, RDS, …) |

Always report **tier claimed** — do not compare L1-only runs to L4 full deploy without labeling.

---

## Model provider path (recommended)

1. On each model release, run **full corpus at L1** in CI (no AWS credentials).
2. Publish `pass_rate_L1` + `by_primary_service` breakdown.
3. Optionally run **L3–L4 on a fixed subset** (e.g. B0–B1 only) with explicit cloud approval and cost ceiling.
4. Pin: model version, harness version, case commit SHAs.

---

## Researcher / agent builder path

1. Implement any pipeline (single LLM, RAG, multi-agent, CloudBot fork).
2. Tag ablations: `full`, `no_rag`, `no_repair`, `no_reuse` (see case `baseline_eligible`).
3. Submit JSON + short README describing architecture.
4. Compare to CloudBot reference on same cases and tier.

---

## Reproducibility rules

- Case `commit` must be pinned 40-char SHA for published rows.
- Record `cloudbench_harness_version` and agent/model id.
- L3–L4 runs must include teardown confirmation per case YAML.
- Do not cherry-pick cases without reporting `n` and which cases were skipped.

---

## Failure artifacts

If a case fails, attach or link a record per [`FAILURE_REGISTRY.md`](FAILURE_REGISTRY.md).
Optional for v1 submissions; required for CloudBot reference runs used in the paper.

---

## File layout (v1)

```
experiments/leaderboard/
  submissions/
    2026-06-example-labs-gpt4o.json
  runs/                    # per-case score JSON from bench score -o
```

Gitignore `experiments/runs/` for local scratch; commit curated submission JSON when publishing results.
