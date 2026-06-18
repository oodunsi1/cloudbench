# CloudBench case schema

Extends the CloudBot case contract in
[`cloudbot-paper2/docs/benchmarks/SCHEMA.md`](../../cloudbot-paper2/docs/benchmarks/SCHEMA.md).
**CloudBench** is the benchmark name; validation logic reuses
`cloudbot_common.benchmark` from paper2.

## Required fields (inherited)

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable case id (`uc1`, `bb-s3-batch`, …) |
| `name` | string | Display name |
| `repo_url` | string | Clone URL — **one application per repo** (multi-repo layout) |
| `commit` | string | **Pinned full SHA** for published leaderboard runs |
| `workload_kind` | string | RepoSpec workload kind enum |
| `expected_service_families` | string[] | Provider-agnostic families in ArchSpec/TF graph |
| `validation_contract` | object | L4 workload success criteria |
| `teardown_contract` | object | Destroy + residual check |

## CloudBench extensions

| Field | Type | Required | Meaning |
|---|---|---|---|
| `paper_id` | string | no | Stable id for paper tables (defaults to `id`) |
| `level` | int | **yes** | Service-complexity ladder L0–L5 (see BUILDING_BLOCKS.md) |
| `ask_type` | string | no | How the task is posed — the inference spine. One of `explicit-instruction`, `single-service`, `service-group`, `use-case`, `app-repo`, `infer-from-app` (see [`ASK_TYPES.md`](ASK_TYPES.md)). Defaults to `app-repo`. |
| `building_block` | string | no | Primary cloud building block under test (B0–B6) |
| `provider` | string | no | Cloud provider: `aws`, `gcp`, `azure` (v1: `aws`) |
| `primary_service` | string | no | Main service under test: `ec2`, `s3`, `rds`, `alb`, `lambda`, … |
| `aws_services` | string[] | no | All AWS services touched (atlas coverage); e.g. `[ec2, iam, s3]` |
| `complexity` | string | no | `single_service` \| `composed` \| `application` |
| `phase` | int | no | Corpus phase when case was added (see SERVICE_ATLAS.md) |
| `runtime` | object | no | Language hints (`language: java`) |
| `baseline_eligible` | string[] | no | Ablation tags: `full`, `iac_only`, `no_rag`, `no_repair`, `no_reuse` |
| `security_contract` | object | no | Optional Checkov/policy checks (GenSIaC / DPIaC inspired) |
| `cost_ceiling_usd` | number | no | Max AWS spend per run (harness enforces when set) |
| `description` | string | no | Free text |

### `security_contract` (optional)

```yaml
security_contract:
  tool: checkov
  min_pass_rate: 0.8          # fraction of applicable policies that must pass
  fail_on_critical: true
```

### `baseline_eligible`

Default if omitted: `["full", "iac_only", "no_rag", "no_repair", "no_reuse"]`.

### Example case extensions

```yaml
provider: aws
primary_service: ec2
aws_services: [ec2, iam]
complexity: single_service   # single_service | composed | application
phase: 1
building_block: B0
```

## Evaluation tiers (reporting — not case fields)

| Tier | Measured | AWS cost |
|---|---|---|
| **L1 — Artifact** | RepoSpec schema; ArchSpec/TF graph vs `expected_service_families`; `terraform validate` | None |
| **L2 — Plan** | `terraform plan` succeeds | Low (read) |
| **L3 — Deploy** | apply + proof + destroy | Full (gated) |
| **L4 — Workload** | L3 + `validation_contract` on instance | Full (gated) |

Harness: `bench score --tier L1|L2|L3|L4`.

## Leaderboard metrics (from run artifacts)

Primary: `deploy_success` (L3), `workload_success` (L4).

Efficiency: `llm_call_count`, `llm_total_latency_s`, estimated tokens, `rag_call_count`.

Robustness: `repair_iterations`, `reuse_hit`, `llm_calls_saved`.

Quality: graph_match_score, security_pass_rate.

Stratify all metrics by `level`, `building_block`, and `primary_service`.

See [`LEADERBOARD.md`](LEADERBOARD.md) for submission format and [`SERVICE_ATLAS.md`](SERVICE_ATLAS.md) for service coverage.

## Pinning policy

- Development may use `commit: unpinned` locally.
- **Release harness rejects `unpinned`** and SHAs shorter than 40 hex chars.
- Record SHA in case YAML when the app repo is tagged for a benchmark release.

## Repo layout policy

**One GitHub repository per application case** (decided). Naming:
`cloudbench-{provider}-{service}-{slug}` — see [`NAMING.md`](NAMING.md).
