# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""Tests for DR evidence bundle generation."""

import json
from pathlib import Path

from tools.ai_sdlc_poc.evidence import persist_evidence
from tools.ai_sdlc_poc.workflow import run_evaluation


def test_persist_evidence_writes_dr009_and_dr010_files(tmp_path: Path) -> None:
    evidence_root = tmp_path / "evidence"
    tooling_lock = tmp_path / "tooling.lock.json"
    tooling_lock.write_text(
        json.dumps({"specify": {"version": "x"}, "apm": {"version": "y"}}),
        encoding="utf-8",
    )

    report = run_evaluation(mode="live", execute_live=False)
    written = persist_evidence(report, evidence_root)

    assert written
    assert (evidence_root / "dr009" / "apm-lock.json").exists()
    assert (evidence_root / "dr009" / "context-digest.txt").exists()
    assert (evidence_root / "dr009" / "audit-report.json").exists()
    assert (evidence_root / "dr009" / "apm-steps.json").exists()
    assert (evidence_root / "dr009" / "provenance.json").exists()
    assert (evidence_root / "dr010" / "sequential.json").exists()
    assert (evidence_root / "dr010" / "concurrent.json").exists()
    assert (evidence_root / "dr010" / "merge.json").exists()
    assert (evidence_root / "dr010" / "speckit-steps.json").exists()
    assert (evidence_root / "dr010" / "impact-analysis.json").exists()
    assert (evidence_root / "dr010" / "impact.json").exists()
    assert (evidence_root / "dr010" / "replan.json").exists()
    assert (evidence_root / "dr010" / "revalidation.json").exists()
    assert (evidence_root / "dr010" / "validation.json").exists()
    assert (evidence_root / "dr010" / "summary.json").exists()

    apm_lock_payload = json.loads(
        (evidence_root / "dr009" / "apm-lock.json").read_text(encoding="utf-8")
    )
    assert "runtime_lockfile_sha256" in apm_lock_payload

    provenance_payload = json.loads(
        (evidence_root / "dr009" / "provenance.json").read_text(encoding="utf-8")
    )
    assert "requirements_tracking" in provenance_payload
    assert provenance_payload["requirements_tracking"]["system"] == "sphinx-needs/ubcode"
    assert "linked_need_ids" in provenance_payload["requirements_tracking"]
