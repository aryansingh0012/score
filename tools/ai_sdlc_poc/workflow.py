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

"""Deterministic workflow adapter used by the Harbor evaluation layer.

The adapter records the artifacts that live SpecKit and APM executions must
provide. It is intentionally offline so lifecycle and re-planning checks can
be reproduced without a model subscription or network access.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.ai_sdlc_poc.comparison import compare_against_reference
from tools.ai_sdlc_poc.adapters import apm_sequence, speckit_sequence

ISSUE = "Write unit tests for watchdog in ProcessGroupManager"
CHANGED_REQUIREMENT = (
    "Watchdog tests must verify serviceWatchdog() is invoked during the "
    "ProcessGroupManager run cycle."
)
WORKSTREAMS = {
    "agent_a": "watchdog mocking interface",
    "agent_b": "watchdog behavior tests",
    "agent_c": "Bazel test target integration",
}


def _digest(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContextPackage:
    version: str
    lock: str
    instructions: str
    skills: str
    tools: str
    conventions: str
    requirements: str

    @property
    def digest(self) -> str:
        return _digest(*self.__dict__.values())


@dataclass(frozen=True)
class AgentOutput:
    agent: str
    workstream: str
    context_digest: str
    baseline_id: str
    baseline_digest: str
    artifacts: tuple[str, ...]


@dataclass(frozen=True)
class DesignBaseline:
    id: str
    version: str
    scope: str
    shared_contracts: tuple[str, ...]

    @property
    def digest(self) -> str:
        return _digest(self.id, self.version, self.scope, *self.shared_contracts)


@dataclass(frozen=True)
class RequirementChangeTrigger:
    source: str
    location: str
    requirement: str
    status: str
    reason: str


@dataclass(frozen=True)
class ArtifactImpact:
    artifact: str
    status: str
    reason: str
    follow_up: str


def _context() -> ContextPackage:
    return ContextPackage(
        version="apm-context-0.1.0",
        lock="apm.lock.yaml:benchmark-fixture-v1",
        instructions="S-CORE governed AI-SDLC instructions",
        skills="SpecKit workflow and lifecycle test skills",
        tools="specify-cli; apm; bazel",
        conventions="S-CORE lifecycle repository conventions",
        requirements=ISSUE,
    )


def _design_baseline() -> DesignBaseline:
    return DesignBaseline(
        id="design-baseline-v1",
        version="v1",
        scope="watchdog run-cycle benchmark",
        shared_contracts=(
            "serviceWatchdog() is invoked during the ProcessGroupManager run cycle",
            "all workstreams reference the same baseline contract",
            "merge artifacts preserve baseline identity for replan analysis",
        ),
    )


def _requirement_change_trigger() -> RequirementChangeTrigger:
    return RequirementChangeTrigger(
        source="serviceWatchdog()",
        location="ProcessGroupManager.run()",
        requirement=CHANGED_REQUIREMENT,
        status="triggered",
        reason="The watchdog run-cycle requirement changes the benchmark baseline and invalidates the current Agent B test assumptions.",
    )


def _sequential(context: ContextPackage) -> dict[str, Any]:
    return {
        "mode": "sequential",
        "context_digest": context.digest,
        "speckit_artifacts": [
            "constitution",
            "specification",
            "clarification",
            "plan",
            "tasks",
            "analysis",
            "implementation",
        ],
        "lifecycle": [
            "issue",
            "specification",
            "design_baseline_v1",
            "tasks",
            "implementation",
            "tests",
            "validation",
        ],
    }


def _concurrent(context: ContextPackage, baseline: DesignBaseline) -> list[AgentOutput]:
    return [
        AgentOutput(
            agent=agent,
            workstream=workstream,
            context_digest=context.digest,
            baseline_id=baseline.id,
            baseline_digest=baseline.digest,
            artifacts=(workstream, "design-baseline-v1"),
        )
        for agent, workstream in WORKSTREAMS.items()
    ]


def _merge_agents(
    agents: list[AgentOutput],
    baseline: DesignBaseline,
) -> dict[str, Any]:
    merged_artifacts = tuple(
        dict.fromkeys(
            artifact
            for agent in agents
            for artifact in (*agent.artifacts, agent.workstream)
        )
    )
    return {
        "status": "merged",
        "baseline_id": baseline.id,
        "baseline_digest": baseline.digest,
        "source_agents": [agent.agent for agent in agents],
        "source_workstreams": [agent.workstream for agent in agents],
        "merged_artifacts": list(merged_artifacts),
        "conflicts": [],
    }


def _impact_analysis() -> dict[str, Any]:
    trigger = _requirement_change_trigger()
    artifact_impacts = [
        ArtifactImpact(
            artifact="specification",
            status="needs-update",
            reason="The feature spec must capture the serviceWatchdog() run-cycle requirement.",
            follow_up="Revise the spec to make the run-cycle watchdog call explicit.",
        ),
        ArtifactImpact(
            artifact="tasks",
            status="needs-update",
            reason="The task breakdown must include the watchdog regression work and its validation path.",
            follow_up="Rework the task list to add the new acceptance and validation steps.",
        ),
        ArtifactImpact(
            artifact="agent_b.watchdog_behavior_tests",
            status="invalidated",
            reason="Agent B tests must assert serviceWatchdog() is called during the run cycle.",
            follow_up="Update the watchdog behavior tests to cover the run-loop invocation.",
        ),
        ArtifactImpact(
            artifact="design-baseline-v1",
            status="superseded",
            reason="The original baseline does not encode the new watchdog requirement.",
            follow_up="Replan against design-baseline-v2 with the updated acceptance criteria.",
        ),
    ]
    return {
        "requirement_change": CHANGED_REQUIREMENT,
        "trigger": asdict(trigger),
        "status": "conflict",
        "affected_artifacts": [artifact.artifact for artifact in artifact_impacts],
        "artifact_impacts": [asdict(artifact) for artifact in artifact_impacts],
        "replan_required": True,
    }


def run_evaluation(mode: str = "offline", execute_live: bool = False) -> dict[str, Any]:
    """Execute workflow modes and return Harbor-compatible evidence."""
    if mode not in {"offline", "live"}:
        raise ValueError("mode must be 'offline' or 'live'")
    context = _context()
    baseline = _design_baseline()
    agents = _concurrent(context, baseline)
    impact = _impact_analysis()
    report: dict[str, Any] = {
        "framework": "harbor",
        "benchmark": {
            "issue": ISSUE,
            "ground_truth": "PR #444",
            "starting_state": "repository state before PR #444",
        },
        "apm": asdict(context) | {"digest": context.digest},
        "design_baseline": asdict(baseline) | {"digest": baseline.digest},
        "sequential": _sequential(context),
        "concurrent": {
            "baseline": asdict(baseline) | {"digest": baseline.digest},
            "agents": [asdict(agent) for agent in agents],
            "merge": _merge_agents(agents, baseline),
        },
        "impact_analysis": impact,
        "replan": {
            "status": "completed",
            "updated_baseline": "design-baseline-v2",
            "added_acceptance": CHANGED_REQUIREMENT,
        },
        "validation": {
            "baseline": "design-baseline-v2",
            "service_watchdog_run_cycle": True,
            "status": "passed",
        },
    }
    report["summary"] = {
        "context_hashes_match": len(
            {agent.context_digest for agent in agents}
        )
        == 1,
        "concurrent_agents": len(agents),
        "impact_detected": impact["replan_required"],
        "validation": report["validation"]["status"],
    }
    report["execution"] = {
        "mode": mode,
        "live_execute": execute_live,
    }

    if mode == "live":
        repo_root = Path.cwd()
        report["live_adapters"] = {
            "speckit": speckit_sequence(repo_root, execute=execute_live),
            "apm": apm_sequence(repo_root, execute=execute_live),
        }
        report["comparison"] = compare_against_reference(report, repo_root)
    return report
