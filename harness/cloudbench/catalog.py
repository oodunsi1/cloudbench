"""CloudBench service catalog + watcher.

The "supply" side of the map: the real, complete list of services a cloud sells. For AWS we read it
straight from ``botocore`` (bundled with boto3 — free, offline, versioned), attach each service's full
name, sort services into the console's category groups, and mark which already have a runnable repo.

`bench catalog` writes ``benchmark/grid/services/aws.yaml``. `bench catalog --refresh` rebuilds and
diffs against the stored file (added / removed services) — the watcher, realised for AWS. The same
shape extends to GCP / Azure / Alibaba via their SDKs later.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# The console category groups (from the AWS "All services" left nav). Canonical order.
CATEGORY_GROUPS: List[str] = [
    "analytics", "application-integration", "blockchain", "business-applications",
    "cloud-financial-management", "compute", "containers", "customer-enablement",
    "database", "developer-tools", "end-user-computing", "frontend-web-mobile",
    "game-development", "iot", "machine-learning", "management-governance",
    "media-services", "migration-transfer", "networking-content-delivery",
    "quantum-technologies", "satellite", "security-identity-compliance", "storage",
    "uncategorised",
]

# Seed mapping: category -> botocore service ids. Covers the common services; everything else falls
# to "uncategorised" and is filled in over time (the catalog's maintenance is part of the watcher).
_CATEGORY_SEED: Dict[str, List[str]] = {
    "compute": ["ec2", "lambda", "batch", "lightsail", "autoscaling", "elasticbeanstalk",
                "apprunner", "outposts", "imagebuilder", "ec2-instance-connect", "serverlessrepo"],
    "containers": ["ecs", "eks", "ecr", "ecr-public", "servicediscovery"],
    "storage": ["s3", "s3control", "s3outposts", "efs", "fsx", "glacier", "backup",
                "storagegateway"],
    "database": ["rds", "rds-data", "dynamodb", "dax", "elasticache", "redshift", "redshift-data",
                 "neptune", "docdb", "memorydb", "keyspaces", "qldb", "timestream-write",
                 "timestream-query"],
    "networking-content-delivery": ["elb", "elbv2", "route53", "route53domains", "cloudfront",
                                     "apigateway", "apigatewayv2", "globalaccelerator",
                                     "directconnect", "networkmanager", "vpc-lattice"],
    "application-integration": ["sqs", "sns", "eventbridge", "events", "stepfunctions", "sfn", "mq",
                                "swf", "appflow", "pipes", "scheduler"],
    "analytics": ["athena", "glue", "emr", "kinesis", "kinesisanalytics", "kinesisanalyticsv2",
                  "firehose", "quicksight", "opensearch", "es", "datazone", "cleanrooms",
                  "lakeformation", "dataexchange"],
    "machine-learning": ["sagemaker", "sagemaker-runtime", "bedrock", "bedrock-runtime",
                         "bedrock-agent", "comprehend", "rekognition", "textract", "translate",
                         "transcribe", "polly", "lexv2-models", "lexv2-runtime", "personalize",
                         "forecast", "kendra", "qbusiness"],
    "developer-tools": ["codecommit", "codebuild", "codedeploy", "codepipeline", "codeartifact",
                        "cloud9", "xray", "codeguru-reviewer", "codeguruprofiler", "codecatalyst"],
    "management-governance": ["cloudformation", "cloudwatch", "logs", "cloudtrail", "config", "ssm",
                              "organizations", "servicecatalog", "controltower", "health",
                              "resource-groups", "license-manager", "compute-optimizer",
                              "application-insights", "ssm-incidents", "ssm-contacts"],
    "security-identity-compliance": ["iam", "sts", "kms", "secretsmanager", "acm", "acm-pca",
                                     "guardduty", "inspector2", "macie2", "securityhub", "wafv2",
                                     "waf", "shield", "cognito-idp", "cognito-identity", "sso",
                                     "sso-admin", "identitystore", "detective", "accessanalyzer",
                                     "network-firewall", "fms", "ram", "verifiedpermissions"],
    "migration-transfer": ["dms", "datasync", "transfer", "mgn", "snowball", "migrationhuborchestrator"],
    "frontend-web-mobile": ["amplify", "amplifybackend", "amplifyuibuilder", "appsync", "location",
                            "devicefarm"],
    "iot": ["iot", "iot-data", "iotanalytics", "iotevents", "iotsitewise", "iotwireless",
            "iotfleetwise", "iottwinmaker", "greengrassv2"],
    "media-services": ["mediaconvert", "medialive", "mediapackage", "mediastore", "mediatailor",
                       "ivs", "ivschat", "kinesisvideo", "elastictranscoder"],
    "business-applications": ["connect", "ses", "sesv2", "workmail", "chime", "supplychain"],
    "end-user-computing": ["workspaces", "workspaces-web", "appstream", "worklink"],
    "customer-enablement": ["support", "servicequotas"],
    "game-development": ["gamelift"],
    "cloud-financial-management": ["ce", "budgets", "cur", "billingconductor", "freetier"],
    "quantum-technologies": ["braket"],
    "satellite": ["groundstation"],
    "blockchain": ["managedblockchain"],
    "pinpoint-shared": [],  # placeholder so the seed stays easy to extend
}


def _service_to_category() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for category, ids in _CATEGORY_SEED.items():
        if category not in CATEGORY_GROUPS:
            continue
        for sid in ids:
            mapping.setdefault(sid, category)
    return mapping


def _slug(service_id: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in service_id).strip("-")


# --------------------------------------------------------------------------------------------------
# Reading the live AWS service list from the SDK
# --------------------------------------------------------------------------------------------------

def aws_services() -> List[Dict[str, str]]:
    """Return every AWS service the installed SDK knows: ``{id, name}`` (full name when available)."""
    import botocore.session

    session = botocore.session.Session()
    loader = session.get_component("data_loader")
    out: List[Dict[str, str]] = []
    for sid in session.get_available_services():
        name = sid
        try:
            meta = loader.load_service_model(sid, "service-2")["metadata"]
            name = meta.get("serviceFullName") or meta.get("serviceAbbreviation") or sid
        except Exception:
            pass
        out.append({"id": sid, "name": name})
    return out


# --------------------------------------------------------------------------------------------------
# Which services already have a runnable repo (cross-link to the map's cells)
# --------------------------------------------------------------------------------------------------

def covered_services(root: Path) -> Dict[str, Dict[str, str]]:
    """Map service id -> {cell, status} for services that are the focus of a runnable cell."""
    cells_path = root / "benchmark" / "grid" / "cells.yaml"
    if not cells_path.is_file():
        return {}
    grid = yaml.safe_load(cells_path.read_text(encoding="utf-8")) or {}
    covered: Dict[str, Dict[str, str]] = {}
    for cell in grid.get("cells", []):
        if cell.get("status") != "covered" and not cell.get("app_generated"):
            continue
        case_rel = cell.get("case")
        if not case_rel:
            continue
        case_path = root / case_rel
        if not case_path.is_file():
            continue
        case = yaml.safe_load(case_path.read_text(encoding="utf-8")) or {}
        primary = case.get("primary_service")
        if primary and primary not in covered:  # keep the first (canonical) cell for a service
            status = "covered" if cell.get("status") == "covered" else "generated"
            covered[primary] = {"cell": cell.get("id", ""), "status": status}
    return covered


# --------------------------------------------------------------------------------------------------
# Building / writing / diffing the catalog
# --------------------------------------------------------------------------------------------------

def build_catalog(root: Path, provider: str = "aws") -> dict:
    if provider != "aws":
        raise ValueError(f"Only the AWS catalog is built today (got {provider!r}).")
    cat = _service_to_category()
    covered = covered_services(root)
    services = []
    for svc in aws_services():
        sid = svc["id"]
        link = covered.get(sid)
        services.append({
            "id": sid,
            "name": svc["name"],
            "category": cat.get(sid, "uncategorised"),
            "target_repo": f"cloudbench-aws-{_slug(sid)}",
            "status": link["status"] if link else "empty",
            "cell": link["cell"] if link else None,
        })
    services.sort(key=lambda s: s["id"])
    by_status: Dict[str, int] = {}
    for s in services:
        by_status[s["status"]] = by_status.get(s["status"], 0) + 1
    return {
        "provider": provider,
        "source": "botocore (AWS SDK service models)",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "category_groups": CATEGORY_GROUPS,
        "counts": {"total": len(services), **by_status},
        "services": services,
    }


def catalog_path(root: Path, provider: str = "aws") -> Path:
    return root / "benchmark" / "grid" / "services" / f"{provider}.yaml"


def write_catalog(catalog: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# CloudBench service catalog — the SUPPLY side of the map (auto-generated).\n"
        "# Built from the AWS SDK service list by `bench catalog`; refresh with `bench catalog --refresh`.\n"
        "# Each service is a corpus entry: target_repo is the run-as-is repo it will get; status is\n"
        "# empty | generated | covered (covered/generated rows cross-link to a cell). Human view:\n"
        "# ../../SERVICE_CATALOG.md\n"
    )
    body = yaml.safe_dump(catalog, sort_keys=False, default_flow_style=False, allow_unicode=True, width=100)
    path.write_text(header + body, encoding="utf-8")
    return path


def load_catalog(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def diff_catalogs(old: Optional[dict], new: dict) -> Dict[str, List[str]]:
    """Compare service-id sets (the watcher core): what was added / removed since last build."""
    old_ids = {s["id"] for s in (old or {}).get("services", [])}
    new_ids = {s["id"] for s in new.get("services", [])}
    return {
        "added": sorted(new_ids - old_ids),
        "removed": sorted(old_ids - new_ids),
    }


def refresh(root: Path, provider: str = "aws") -> Tuple[dict, Dict[str, List[str]], Path]:
    """Rebuild the catalog, diff against the stored file, write it. Returns (catalog, diff, path)."""
    path = catalog_path(root, provider)
    old = load_catalog(path)
    new = build_catalog(root, provider)
    diff = diff_catalogs(old, new)
    write_catalog(new, path)
    return new, diff, path
