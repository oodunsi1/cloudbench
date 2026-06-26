from __future__ import annotations

from pathlib import Path

from cloudbench.security import evaluate_contract, scan_terraform


def _write(tmp_path: Path, body: str) -> Path:
    (tmp_path / "main.tf").write_text(body, encoding="utf-8")
    return tmp_path


def test_clean_terraform_is_clean(tmp_path: Path) -> None:
    _write(tmp_path, 'resource "aws_instance" "app" {\n  ami = "ami-123"\n}\n')
    res = scan_terraform(tmp_path)
    assert res.scanner == "builtin"
    assert res.counts["critical"] == 0
    assert res.pass_rate == 1.0


def test_open_ssh_to_world_is_critical(tmp_path: Path) -> None:
    _write(tmp_path, '''
resource "aws_security_group" "app" {
  ingress {
    from_port   = 22
    to_port     = 22
    cidr_blocks = ["0.0.0.0/0"]
  }
}
''')
    res = scan_terraform(tmp_path)
    ids = [f["rule_id"] for f in res.findings]
    assert "open-sensitive-port" in ids
    assert res.counts["critical"] >= 1
    assert res.pass_rate < 1.0


def test_hardcoded_secret_is_critical(tmp_path: Path) -> None:
    _write(tmp_path, 'resource "aws_db_instance" "db" {\n  password = "hunter2pass"\n  storage_encrypted = true\n}\n')
    res = scan_terraform(tmp_path)
    assert "hardcoded-secret" in [f["rule_id"] for f in res.findings]


def test_var_reference_is_not_a_hardcoded_secret(tmp_path: Path) -> None:
    _write(tmp_path, 'resource "aws_db_instance" "db" {\n  password = var.db_password\n  storage_encrypted = true\n}\n')
    res = scan_terraform(tmp_path)
    assert "hardcoded-secret" not in [f["rule_id"] for f in res.findings]


def test_unencrypted_rds_is_medium(tmp_path: Path) -> None:
    _write(tmp_path, 'resource "aws_db_instance" "db" {\n  password = var.p\n}\n')
    res = scan_terraform(tmp_path)
    assert "unencrypted-rds" in [f["rule_id"] for f in res.findings]


def test_contract_gates_on_critical(tmp_path: Path) -> None:
    _write(tmp_path, '''
resource "aws_security_group" "app" {
  ingress { from_port = 22, to_port = 22, cidr_blocks = ["0.0.0.0/0"] }
}
''')
    res = scan_terraform(tmp_path)
    gated = evaluate_contract(res, {"fail_on_critical": True})
    assert gated.passed is False
    # no contract -> advisory only
    assert evaluate_contract(scan_terraform(tmp_path), None).passed is None


def test_min_pass_rate_contract(tmp_path: Path) -> None:
    _write(tmp_path, 'resource "aws_db_instance" "db" {\n  password = var.p\n}\n')  # one medium
    res = evaluate_contract(scan_terraform(tmp_path), {"min_pass_rate": 0.99})
    assert res.passed is False


# --- per-rule open-sensitive-port (no false-positive on a mixed security group) -------------------

from cloudbench.security import scan_builtin
import tempfile, pathlib


def _scan(tf: str):
    d = tempfile.mkdtemp()
    (pathlib.Path(d) / "main.tf").write_text(tf)
    return scan_builtin(pathlib.Path(d))


def test_mixed_sg_public_app_port_plus_restricted_db_is_not_critical():
    # a public app port (8080 -> world) AND a DB rule restricted to private ranges in the SAME group:
    # the old whole-block scanner false-flagged this as open-sensitive-port. Per-rule, it must not.
    tf = '''resource "aws_security_group" "app" {
  ingress {
    from_port   = 8080
    to_port     = 8080
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 5432
    to_port     = 5432
    cidr_blocks = ["10.0.0.0/8"]
  }
}
'''
    findings = _scan(tf)
    rules = {f.rule_id for f in findings}
    assert "open-sensitive-port" not in rules  # 5432 is NOT open to the world
    assert "open-ingress" in rules             # 8080 -> world is still flagged (high)


def test_genuinely_open_db_port_is_still_critical():
    tf = '''resource "aws_security_group" "db" {
  ingress {
    from_port   = 5432
    to_port     = 5432
    cidr_blocks = ["0.0.0.0/0"]
  }
}
'''
    assert "open-sensitive-port" in {f.rule_id for f in _scan(tf)}


def test_standalone_sg_rule_still_checked():
    tf = '''resource "aws_security_group_rule" "bad" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  cidr_blocks = ["0.0.0.0/0"]
}
'''
    assert "open-sensitive-port" in {f.rule_id for f in _scan(tf)}
