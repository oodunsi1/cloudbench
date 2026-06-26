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
