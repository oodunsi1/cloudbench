# CloudBench failure registry

Standard format for exporting **why a run failed** so teams can improve agents, RAG,
and repair loops. Any submitter can use this schema; CloudBot reference runs should
emit these records for paper reproducibility.

---

## Purpose

- Make failures **comparable** across models and agents.
- Feed the public improvement loop ([`TRAINING_LOOP.md`](TRAINING_LOOP.md)).
- Enable community replication without sharing proprietary prompts.

---

## Record schema (JSON)

One record per failed case run:

```json
{
  "registry_version": "1.0",
  "case_id": "uc2",
  "paper_id": "aws-ec2-java-image",
  "provider": "aws",
  "primary_service": "ec2",
  "building_block": "B1",
  "tier": "L1",
  "passed": false,
  "stage": "engineer",
  "failure_mode": "graph_missing_family",
  "failure_detail": "expected iam_instance_profile, observed none",
  "graph_match": {
    "score": 0.75,
    "missing": ["iam_instance_profile"],
    "matched": ["compute", "security_group", "iam_role"]
  },
  "agent_or_model": "cloudbot-full",
  "harness_version": "0.1.0",
  "timestamp": "2026-06-02T12:00:00Z",
  "artifacts": {
    "score_json": "experiments/leaderboard/runs/uc2-fail.json",
    "repair_log": "repair_runs/.../log.txt"
  }
}
```

---

## Field definitions

| Field | Required | Values |
|-------|----------|--------|
| `case_id` | yes | Case YAML `id` |
| `tier` | yes | `L1` \| `L2` \| `L3` \| `L4` |
| `passed` | yes | `false` for registry entries |
| `stage` | yes | `analyst` \| `architect` \| `engineer` \| `repair` \| `apply` \| `probe` \| `teardown` |
| `failure_mode` | yes | Short enum (see below) |
| `failure_detail` | no | Human-readable one line |
| `graph_match` | no | From `bench score` output |
| `primary_service` | no | For atlas stratification |

### `failure_mode` enum (v1)

| Value | Meaning |
|-------|---------|
| `graph_missing_family` | Terraform/ArchSpec missing expected service family |
| `terraform_invalid` | `terraform validate` failed |
| `repospec_invalid` | RepoSpec schema failed |
| `plan_failed` | L2 plan error |
| `apply_failed` | L3 apply error |
| `probe_failed` | L4 workload check failed |
| `teardown_residual` | Resources left after destroy |
| `timeout` | Stage exceeded time limit |
| `other` | Free-text in `failure_detail` |

---

## How to produce records

1. Run `bench score ... -o score.json`.
2. If `passed` is false, map errors to `stage` and `failure_mode`.
3. Write one JSON file per failure under `experiments/failures/` (local) or attach to leaderboard submission.

Example mapping from L1 score:

- `graph_match.missing` non-empty → `graph_missing_family`, stage `engineer` or `architect`
- `terraform_validate_ok == false` → `terraform_invalid`, stage `engineer`
- `repospec_valid == false` → `repospec_invalid`, stage `analyst`

---

## Privacy

Do not include secrets, `.env` contents, or cloud credentials in `failure_detail` or `artifacts`.

---

## Future harness

Planned: `bench export-failure score.json --stage engineer -o failure.json`  
v1: manual mapping from score output is sufficient.
