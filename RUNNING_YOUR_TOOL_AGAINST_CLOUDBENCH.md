# Running your own tool against CloudBench

This guide is for an outside team that has a tool which takes an application repo and produces cloud
setup (infrastructure as code), and wants to score it on CloudBench. Plain steps, no inside knowledge
needed.

CloudBench is agent-neutral. CloudBot is just the first entrant. Your tool is welcome to be the next.

## What CloudBench measures

Every case is one real app repo plus a contract that says what a correct deployment looks like. Your
tool is scored on how far it gets along this path:

understand the repo, design the setup, write the setup, validate it, deploy it, run the app, prove it
ran, tear it down.

The scoring comes in tiers. The first tier is free. The deploy tiers cost real cloud money and are run
with care.

| Tier | What it checks | Cloud cost |
|---|---|---|
| L1 Artifact | Your setup files are valid, and their resource graph covers the services the case expects | None |
| L2 Plan | A dry-run plan succeeds | Low (read only) |
| L3 Deploy | Apply, capture proof, then tear down with nothing left behind | Real (gated) |
| L4 Workload | Everything in L3, plus the app actually ran and passed the case's checks | Real (gated) |

The column that makes CloudBench different is L4: proof the app actually ran, not just that the setup
applied.

## What you need

1. This repo (the cases and the harness): `git clone https://github.com/oodunsi1/cloudbench`.
2. The shared library the harness reuses for validation and scoring (from the CloudBot paper repo):
   `git clone https://github.com/oodunsi1/cloudbot-paper2` and `pip install -e cloudbot-paper2/cloudbot-common/`.
3. Terraform on your PATH (for the validate and plan checks).

(A standalone, pip-installable harness package is planned so step 2 is not needed. For now the harness
reuses `cloudbot_common` from the paper repo.)

## The five steps

### 1. Pick a case

Cases live in `benchmark/cases/`. Start with the simplest, the word-count batch job. Read the case
file. The full meaning of each field is in [`benchmark/SCHEMA.md`](benchmark/SCHEMA.md). The fields
that matter to you:

- `repo_url` and `commit`: the exact app repo and pinned version to deploy.
- `workload_kind` and `building_block`: what kind of work it is and which cloud blocks it needs.
- `expected_service_families`: the cloud services a correct setup should include.
- `validation_contract`: how we know the app actually ran.
- `teardown_contract`: how we know nothing was left behind.

### 2. Check the case is well formed (optional)

```bash
cd harness
python -m cloudbench.cli validate ../benchmark/cases/aws-ec2-wordcount.yaml
```

### 3. Run your tool

Point your tool at the case's `repo_url` at the pinned `commit`. Let it produce your setup files
(Terraform today; CloudFormation and others can be scored too). Save them to a folder. You do not need
any cloud account for the free tier.

### 4. Score for free (L1)

```bash
cd harness
python -m cloudbench.cli score ../benchmark/cases/aws-ec2-wordcount.yaml --tier L1 \
  --terraform-dir /path/to/your/generated/terraform \
  -o my_score.json
```

This checks two things: your setup files validate, and their resource graph covers the services the
case expects. It writes a score report and needs no cloud money.

### 5. Deploy and prove (paid, gated)

The deploy tiers (L3 and L4) apply your setup to a real cloud account, run the app, check the case's
`validation_contract`, and tear everything down. These cost money and are run with explicit approval.
Today the public harness scores L1; the deploy-and-prove tiers are run through the CloudBot paper
repo's deploy harness, and a public path for outside teams is on the roadmap. If you want to run the
deploy tiers, open an issue and we will help.

## How different kinds of tools connect

Not every related work plugs in the same way.

| Your tool | How CloudBench scores it | What you get |
|---|---|---|
| A repo-to-cloud system that emits setup files (like CloudBot, MACOG, IaCGen, or a plain coding agent) | Fully: we read your files, score them at L1, and (gated) deploy and prove them | A fair, same-input, same-scorer comparison |
| A black-box product that deploys but hides its files (like a commercial platform) | On the outcome only: did it deploy, did the app run, did it clean up | An honest outcome comparison, marked as black-box, not an artifact one |
| Another benchmark | Not an entrant; we compare against it as a peer in the related-work tables | Where you sit in the field |

## The leaderboard numbers

Each run produces, per case: did it deploy (L3), did the app run (L4), how many model calls and how
long, how many repair tries, and whether it reused past work. We report these split by difficulty
level and building block. The submission format is in
[`benchmark/LEADERBOARD.md`](benchmark/LEADERBOARD.md).

## Fair-play rules

- Use the pinned commit. That is what keeps results comparable over time.
- Free L1 scoring is open to everyone. The paid deploy tiers are gated, so cost stays on the small,
  defensible set of cases.
- Bring your own retrieval or knowledge base if your tool uses one. We score each system the way it was
  designed, on the same case input.
