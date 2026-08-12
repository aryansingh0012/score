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

"""Report comparison helpers for the AI-SDLC PoC.

The PoC uses stored Harbor artifacts as the comparison baseline. The comparer
normalizes volatile runtime fields so the live harness output can be matched
against the checked-in reference report for the corresponding execution mode.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compare_against_reference(report: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    reference_path = _reference_path(repo_root, report)
    reference_report = json.loads(reference_path.read_text(encoding="utf-8"))
    normalized_report = _normalize(report)
    normalized_reference = _normalize(reference_report)
    diffs = _diff(normalized_reference, normalized_report)
    return {
        "reference_path": str(reference_path),
        "matches": not diffs,
        "diffs": diffs,
    }


def _reference_path(repo_root: Path, report: dict[str, Any]) -> Path:
    execution = report.get("execution", {})
    if execution.get("mode") == "live":
        if execution.get("live_execute"):
            return repo_root / "artifacts" / "harbor-report-live-exec.json"
        return repo_root / "artifacts" / "harbor-report-live-plan.json"
    return repo_root / "artifacts" / "harbor-report.json"


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"runtime_dir", "stdout", "stderr", "returncode", "comparison", "live_adapters"}:
                continue
            if key == "design_baseline":
                continue
            if key == "impact_analysis" and isinstance(item, dict):
                normalized[key] = {
                    subkey: _normalize(subitem)
                    for subkey, subitem in item.items()
                    if subkey in {"requirement_change", "status", "affected_artifacts", "replan_required"}
                }
                continue
            if key == "baseline" and isinstance(item, dict) and "id" in item:
                normalized[key] = _normalize(item["id"])
                continue
            if key == "agents" and isinstance(item, list):
                normalized[key] = [_normalize_agent(agent) for agent in item]
                continue
            if key == "merge" and isinstance(item, dict):
                normalized[key] = _normalize_merge(item)
                continue
            normalized[key] = _normalize(item)
        return normalized
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    return value


def _normalize_agent(agent: Any) -> Any:
    if not isinstance(agent, dict):
        return _normalize(agent)
    normalized: dict[str, Any] = {}
    for key, item in agent.items():
        if key in {"baseline_id", "baseline_digest"}:
            if key == "baseline_id":
                normalized["baseline"] = _normalize(item)
            continue
        normalized[key] = _normalize(item)
    return normalized


def _normalize_merge(merge: Any) -> Any:
    if not isinstance(merge, dict):
        return _normalize(merge)
    normalized: dict[str, Any] = {}
    for key in ("status", "outputs"):
        if key in merge:
            normalized[key] = _normalize(merge[key])
    if "outputs" not in normalized and "source_agents" in merge:
        normalized["outputs"] = _normalize(merge["source_agents"])
    return normalized


def _diff(expected: Any, actual: Any, path: str = "") -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    if type(expected) is not type(actual):
        diffs.append({"path": path or "$", "expected": expected, "actual": actual})
        return diffs

    if isinstance(expected, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            diffs.append({"path": f"{path}.{key}" if path else key, "expected": expected[key], "actual": None})
        for key in sorted(actual_keys - expected_keys):
            diffs.append({"path": f"{path}.{key}" if path else key, "expected": None, "actual": actual[key]})
        for key in sorted(expected_keys & actual_keys):
            diffs.extend(_diff(expected[key], actual[key], f"{path}.{key}" if path else key))
        return diffs

    if isinstance(expected, list):
        max_len = max(len(expected), len(actual))
        for index in range(max_len):
            item_path = f"{path}[{index}]" if path else f"[{index}]"
            if index >= len(expected):
                diffs.append({"path": item_path, "expected": None, "actual": actual[index]})
            elif index >= len(actual):
                diffs.append({"path": item_path, "expected": expected[index], "actual": None})
            else:
                diffs.extend(_diff(expected[index], actual[index], item_path))
        return diffs

    if expected != actual:
        diffs.append({"path": path or "$", "expected": expected, "actual": actual})
    return diffs
