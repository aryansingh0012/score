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

"""Focused tests for the deterministic Harbor PoC adapter."""

import pytest

from tools.ai_sdlc_poc.workflow import CHANGED_REQUIREMENT, run_evaluation


def test_all_agents_receive_identical_context_and_baseline() -> None:
    report = run_evaluation()
    agents = report["concurrent"]["agents"]
    baseline = report["concurrent"]["baseline"]

    assert report["summary"]["context_hashes_match"]
    assert {agent["context_digest"] for agent in agents} == {
        report["apm"]["digest"]
    }
    assert baseline["id"] == "design-baseline-v1"
    assert baseline["digest"] == report["design_baseline"]["digest"]
    assert {agent["baseline_id"] for agent in agents} == {baseline["id"]}
    assert {agent["baseline_digest"] for agent in agents} == {baseline["digest"]}
    assert report["concurrent"]["merge"]["baseline_id"] == baseline["id"]
    assert report["concurrent"]["merge"]["baseline_digest"] == baseline["digest"]
    assert report["concurrent"]["merge"]["source_agents"] == [
        "agent_a",
        "agent_b",
        "agent_c",
    ]
    assert report["concurrent"]["merge"]["source_workstreams"] == [
        "watchdog mocking interface",
        "watchdog behavior tests",
        "Bazel test target integration",
    ]
    assert report["concurrent"]["merge"]["merged_artifacts"] == [
        "watchdog mocking interface",
        "design-baseline-v1",
        "watchdog behavior tests",
        "Bazel test target integration",
    ]


def test_requirement_change_triggers_replan_and_validation() -> None:
    report = run_evaluation()
    impact = report["impact_analysis"]

    assert impact["status"] == "conflict"
    assert impact["replan_required"]
    assert CHANGED_REQUIREMENT == impact["requirement_change"]
    assert impact["trigger"]["source"] == "serviceWatchdog()"
    assert impact["trigger"]["location"] == "ProcessGroupManager.run()"
    assert impact["trigger"]["status"] == "triggered"
    assert "agent_b.watchdog_behavior_tests" in impact["affected_artifacts"]
    assert {item["artifact"] for item in impact["artifact_impacts"]} == {
        "specification",
        "tasks",
        "agent_b.watchdog_behavior_tests",
        "design-baseline-v1",
    }
    assert any(
        item["status"] == "invalidated" and item["artifact"] == "agent_b.watchdog_behavior_tests"
        for item in impact["artifact_impacts"]
    )
    assert report["replan"]["updated_baseline"] == "design-baseline-v2"
    assert report["validation"]["status"] == "passed"


def test_replay_is_reproducible() -> None:
    assert run_evaluation() == run_evaluation()


def test_live_mode_plans_speckit_and_apm_steps() -> None:
    report = run_evaluation(mode="live", execute_live=False)

    assert report["execution"] == {"mode": "live", "live_execute": False}
    assert "live_adapters" in report
    assert "comparison" in report
    assert report["comparison"]["reference_path"].endswith(
        "artifacts\\harbor-report-live-plan.json"
    )
    assert report["comparison"]["matches"]
    assert report["live_adapters"]["speckit"]["tool"] == "speckit"
    assert report["live_adapters"]["apm"]["tool"] == "apm"
    assert all(
        step["status"] == "planned"
        for step in report["live_adapters"]["speckit"]["steps"]
    )
    assert all(
        step["status"] == "planned"
        for step in report["live_adapters"]["apm"]["steps"]
    )


def test_live_execute_mode_comparison_targets_exec_artifact() -> None:
    report = run_evaluation(mode="live", execute_live=True)

    assert report["comparison"]["reference_path"].endswith(
        "artifacts\\harbor-report-live-exec.json"
    )


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="mode must be 'offline' or 'live'"):
        run_evaluation(mode="invalid")
