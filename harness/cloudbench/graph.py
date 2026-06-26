from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

# Terraform resource type -> provider-agnostic service family. A tool gets credit for a family if it
# uses ANY resource that provides it (e.g. an instance OR a launch template both give "compute"), so
# this map is deliberately broad: adding rows only improves recall and never lowers a score (observed
# families beyond the expected set count as "extra", not penalised). Family names align with the
# vocabulary the case YAMLs declare in expected_service_families.
_TF_RESOURCE_MAP = {
    # compute
    "aws_instance": "compute",
    "aws_launch_template": "compute",
    "aws_launch_configuration": "compute",
    "aws_autoscaling_group": "autoscaling",
    "aws_spot_instance_request": "compute",
    "aws_ecs_service": "ecs",
    "aws_ecs_task_definition": "ecs",
    "aws_ecs_cluster": "ecs",
    "aws_eks_cluster": "eks",
    "aws_eks_node_group": "eks",
    "aws_lambda_function": "lambda",
    "aws_lambda_event_source_mapping": "lambda",
    "aws_lambda_permission": "lambda",
    # networking
    "aws_vpc": "network",
    "aws_subnet": "network",
    "aws_internet_gateway": "network",
    "aws_nat_gateway": "network",
    "aws_route_table": "network",
    "aws_route": "network",
    "aws_route_table_association": "network",
    "aws_eip": "network",
    "aws_vpc_endpoint": "network",
    # security / identity
    "aws_security_group": "security_group",
    "aws_security_group_rule": "security_group",
    "aws_iam_role": "iam_role",
    "aws_iam_role_policy": "iam_role",
    "aws_iam_role_policy_attachment": "iam_role",
    "aws_iam_policy": "iam_policy",
    "aws_iam_instance_profile": "iam_instance_profile",
    "aws_iam_user": "iam_user",
    "aws_kms_key": "kms",
    "aws_kms_alias": "kms",
    "aws_secretsmanager_secret": "secrets",
    "aws_ssm_parameter": "ssm_parameter",
    # storage
    "aws_s3_bucket": "s3",
    "aws_s3_bucket_policy": "s3",
    "aws_s3_object": "s3",
    "aws_ebs_volume": "ebs",
    "aws_efs_file_system": "efs",
    "aws_ecr_repository": "ecr",
    # databases / cache
    "aws_db_instance": "rds",
    "aws_rds_cluster": "rds",
    "aws_db_subnet_group": "rds",
    "aws_dynamodb_table": "dynamodb",
    "aws_elasticache_cluster": "cache",
    "aws_elasticache_replication_group": "cache",
    "aws_redshift_cluster": "redshift",
    # load balancing
    "aws_lb": "alb",
    "aws_alb": "alb",
    "aws_lb_target_group": "alb",
    "aws_lb_listener": "alb",
    "aws_alb_target_group": "alb",
    # messaging / events
    "aws_sqs_queue": "sqs",
    "aws_sns_topic": "sns",
    "aws_sns_topic_subscription": "sns",
    "aws_kinesis_stream": "kinesis",
    "aws_cloudwatch_event_rule": "eventbridge",
    "aws_cloudwatch_event_target": "eventbridge",
    "aws_sfn_state_machine": "stepfunctions",
    # api / edge / dns / observability
    "aws_api_gateway_rest_api": "apigateway",
    "aws_apigatewayv2_api": "apigateway",
    "aws_cloudfront_distribution": "cloudfront",
    "aws_route53_zone": "route53",
    "aws_route53_record": "route53",
    "aws_cloudwatch_log_group": "cloudwatch",
    "aws_cloudwatch_metric_alarm": "cloudwatch",
}

_TF_RESOURCE_RE = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"')


def families_from_archspec(archspec: Dict[str, Any]) -> Set[str]:
    fams: Set[str] = set()
    for comp in archspec.get("components") or []:
        if isinstance(comp, dict):
            for key in ("service_family", "type"):
                v = comp.get(key)
                if isinstance(v, str) and v:
                    fams.add(v.strip().lower())
    for dep in archspec.get("stateful_deps") or []:
        if isinstance(dep, dict):
            v = dep.get("type")
            if isinstance(v, str) and v:
                fams.add(v.strip().lower())
    return fams


def families_from_terraform(terraform_dir: Path) -> Set[str]:
    fams: Set[str] = set()
    for tf in sorted(terraform_dir.glob("*.tf")):
        text = tf.read_text(encoding="utf-8", errors="replace")
        for match in _TF_RESOURCE_RE.finditer(text):
            rtype = match.group(1)
            mapped = _TF_RESOURCE_MAP.get(rtype)
            if mapped:
                fams.add(mapped)
    return fams


def graph_match_score(expected: Iterable[str], observed: Set[str]) -> Dict[str, Any]:
    """Fraction of expected service families present in observed set."""
    exp = {x.strip().lower() for x in expected}
    if not exp:
        return {"score": 0.0, "missing": [], "extra": sorted(observed), "matched": []}
    matched = exp & observed
    missing = sorted(exp - observed)
    extra = sorted(observed - exp)
    score = len(matched) / len(exp)
    return {
        "score": round(score, 4),
        "missing": missing,
        "extra": extra,
        "matched": sorted(matched),
    }


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
