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

"""Evidence bundle writer for DR-009 and DR-010 outputs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def persist_evidence(report: dict[str, Any], evidence_root: Path) -> list[Path]:
    """Persist DR evidence bundle files and return created file paths."""
    written: list[Path] = []
    dr009_dir = evidence_root / "dr009"
    dr010_dir = evidence_root / "dr010"

    apm_payload = report.get("apm", {})
    live_adapters = report.get("live_adapters", {})
    apm_runtime_dir = Path(live_adapters.get("apm", {}).get("runtime_dir", ""))
    runtime_lock_path = apm_runtime_dir / "apm.lock.yaml"
    runtime_lock_sha256 = _sha256_file(runtime_lock_path) if runtime_lock_path.exists() else ""
    apm_lock = {
        "lock": apm_payload.get("lock", ""),
        "version": apm_payload.get("version", ""),
        "digest": apm_payload.get("digest", ""),
        "runtime_lockfile": str(runtime_lock_path) if runtime_lock_path.exists() else "",
        "runtime_lockfile_sha256": runtime_lock_sha256,
    }
    apm_lock_path = dr009_dir / "apm-lock.json"
    _write_json(apm_lock_path, apm_lock)
    written.append(apm_lock_path)

    context_digest_path = dr009_dir / "context-digest.txt"
    _write_text(context_digest_path, str(apm_payload.get("digest", "")))
    written.append(context_digest_path)

    audit_step: dict[str, Any] = {}
    for step in live_adapters.get("apm", {}).get("steps", []):
        if step.get("name") == "apm-audit":
            audit_step = step
            break
    audit_report_path = dr009_dir / "audit-report.json"
    _write_json(audit_report_path, audit_step)
    written.append(audit_report_path)

    apm_steps_path = dr009_dir / "apm-steps.json"
    _write_json(apm_steps_path, {"steps": live_adapters.get("apm", {}).get("steps", [])})
    written.append(apm_steps_path)

    provenance = {
        "framework": report.get("framework", ""),
        "benchmark": report.get("benchmark", {}),
        "execution": report.get("execution", {}),
        "tools": _read_tooling_lock(evidence_root),
        "runtime_lockfile_sha256": runtime_lock_sha256,
        "live_apm_steps": live_adapters.get("apm", {}).get("steps", []),
        "live_speckit_steps": live_adapters.get("speckit", {}).get("steps", []),
        "requirements_tracking": _build_requirements_tracking(report),
    }
    provenance_path = dr009_dir / "provenance.json"
    _write_json(provenance_path, provenance)
    written.append(provenance_path)

    sequential_path = dr010_dir / "sequential.json"
    _write_json(sequential_path, report.get("sequential", {}))
    written.append(sequential_path)

    concurrent_path = dr010_dir / "concurrent.json"
    _write_json(concurrent_path, report.get("concurrent", {}))
    written.append(concurrent_path)

    merge_path = dr010_dir / "merge.json"
    _write_json(merge_path, report.get("concurrent", {}).get("merge", {}))
    written.append(merge_path)

    speckit_steps_path = dr010_dir / "speckit-steps.json"
    _write_json(
        speckit_steps_path,
        {"steps": live_adapters.get("speckit", {}).get("steps", [])},
    )
    written.append(speckit_steps_path)

    impact_path = dr010_dir / "impact-analysis.json"
    _write_json(impact_path, report.get("impact_analysis", {}))
    written.append(impact_path)

    impact_compat_path = dr010_dir / "impact.json"
    _write_json(impact_compat_path, report.get("impact_analysis", {}))
    written.append(impact_compat_path)

    replan_path = dr010_dir / "replan.json"
    _write_json(replan_path, report.get("replan", {}))
    written.append(replan_path)

    validation_path = dr010_dir / "revalidation.json"
    _write_json(validation_path, report.get("validation", {}))
    written.append(validation_path)

    validation_compat_path = dr010_dir / "validation.json"
    _write_json(validation_compat_path, report.get("validation", {}))
    written.append(validation_compat_path)

    summary_path = dr010_dir / "summary.json"
    _write_json(summary_path, report.get("summary", {}))
    written.append(summary_path)

    comparison_path = dr010_dir / "comparison.json"
    _write_json(comparison_path, report.get("comparison", {}))
    written.append(comparison_path)

    return written


def _read_tooling_lock(evidence_root: Path) -> dict[str, Any]:
    lock_path = evidence_root.parent / "tooling.lock.json"
    if not lock_path.exists():
        return {}
    return json.loads(lock_path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_requirements_tracking(report: dict[str, Any]) -> dict[str, Any]:
    """Build lifecycle requirements-traceability metadata for provenance."""
    need_ids = sorted(_extract_need_ids(report))
    return {
        "system": "sphinx-needs/ubcode",
        "id_pattern": "UPPERCASE_WITH_UNDERSCORES (e.g., REQ_001, SPEC_WATCHDOG_RUN)",
        "linked_need_ids": need_ids,
        "linked_count": len(need_ids),
        "coverage": "linked" if need_ids else "unlinked",
        "index_hint": "Run ubcode indexing and query against docs needs cache.",
    }


def _extract_need_ids(report: dict[str, Any]) -> set[str]:
    """Extract likely Sphinx-Needs IDs from key report text fields."""
    candidates: set[str] = set()
    pattern = re.compile(r"\b(?:REQ|SPEC|TEST|TASK|ARCH|SEC)_[A-Z0-9_]+\b")
    text_fields = [
        str(report.get("benchmark", {}).get("issue", "")),
        str(report.get("benchmark", {}).get("ground_truth", "")),
        str(report.get("impact_analysis", {}).get("requirement_change", "")),
    ]
    for text in text_fields:
        candidates.update(pattern.findall(text.upper()))
    return candidates
