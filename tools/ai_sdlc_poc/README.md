# Harbor AI-SDLC PoC

This package is the first executable slice of the lifecycle PoC. Harbor is the
evaluation and reporting layer; the workflow records the artifacts that the
real SpecKit and Microsoft APM executions must provide.

The offline replay uses the lifecycle task from issue #439, compares against
PR #444 as ground truth, runs sequential and concurrent paths, and deliberately
introduces the `serviceWatchdog()` run-cycle requirement to exercise impact
analysis and re-planning.

## What Was Implemented

The AI-SDLC PoC now includes an executable workflow and evidence pipeline that
can run deterministically offline and can also orchestrate live APM/SpecKit
commands.

Implemented capabilities:

- Deterministic Harbor workflow replay for the benchmark issue:
	"Write unit tests for watchdog in ProcessGroupManager".
	Implemented in: `tools/ai_sdlc_poc/workflow.py` (`run_evaluation`, `ISSUE`).
- Executable CLI entrypoint for running report generation and evidence writing.
	Implemented in: `tools/ai_sdlc_poc/__main__.py` (`main`).
- Shared context package generation with digest tracking so concurrent agents
	can be verified against the same context input.
	Implemented in: `tools/ai_sdlc_poc/workflow.py` (`ContextPackage`, `_context`).
- Design baseline v1 propagation across concurrent workstreams and merge
	artifact generation for Agent A/B/C outputs.
	Implemented in: `tools/ai_sdlc_poc/workflow.py` (`_design_baseline`, `_concurrent`, `_merge_agents`).
- Requirement-change loopback trigger for `serviceWatchdog()` in
	`ProcessGroupManager.run()`.
	Implemented in: `tools/ai_sdlc_poc/workflow.py` (`CHANGED_REQUIREMENT`, `_requirement_change_trigger`).
- Impact analysis over affected artifacts (specification, tasks, Agent B test
	artifacts, and design baseline).
	Implemented in: `tools/ai_sdlc_poc/workflow.py` (`_impact_analysis`).
- Re-plan and validation flow that advances to baseline v2 and records a
	passed validation state for the run-cycle requirement.
	Implemented in: `tools/ai_sdlc_poc/workflow.py` (`run_evaluation`).
- Live adapter scaffolds for SpecKit and APM with two modes:
	- planned mode (records intended commands without execution)
	- execute mode (runs commands and captures outputs)
	Implemented in: `tools/ai_sdlc_poc/adapters.py` (`speckit_sequence`, `apm_sequence`, `_run_or_plan`).
- Report comparison against checked-in reference artifacts to detect drift.
	Implemented in: `tools/ai_sdlc_poc/comparison.py` (`compare_against_reference`).
- DR evidence persistence:
	- DR-009: context, lock/provenance, APM step and audit outputs
	- DR-010: sequential, concurrent, merge, impact, replan, revalidation,
		summary, and comparison outputs
	Implemented in: `tools/ai_sdlc_poc/evidence.py` (`persist_evidence`).
- Requirements traceability metadata in provenance (Sphinx-Needs/ubcode
	fields, linked ID extraction, coverage status).
	Implemented in: `tools/ai_sdlc_poc/evidence.py` (`_build_requirements_tracking`, `_extract_need_ids`).
- Automated tests for workflow behavior and evidence persistence.
	Implemented in: `tools/ai_sdlc_poc/test_workflow.py` and `tools/ai_sdlc_poc/test_evidence.py`.

## Architecture Diagram (with Implementation Files)

```mermaid
flowchart TD
	A["S-CORE Lifecycle PoC"] --> HARBOR

	subgraph L1["Evaluation Layer"]
		HARBOR["Harbor Evaluation<br/>File: tools/ai_sdlc_poc/workflow.py"]
		ORCH["SDLC Orchestrator<br/>Function: run_evaluation"]
	end

	HARBOR --> ORCH

	subgraph L2["Tool Adapter Layer"]
		APM["APM Context Packaging<br/>File: tools/ai_sdlc_poc/adapters.py<br/>Function: apm_sequence"]
		SPEC["SpecKit Workflow<br/>File: tools/ai_sdlc_poc/adapters.py<br/>Function: speckit_sequence"]
	end

	ORCH --> APM
	ORCH --> SPEC

	subgraph L3["Shared Work Layer"]
		BASE["Shared Design Baseline (v1)<br/>File: tools/ai_sdlc_poc/workflow.py<br/>Function: _design_baseline"]
		AGA["Agent A: Mocking<br/>Mapping: WORKSTREAMS"]
		AGB["Agent B: Tests<br/>Mapping: WORKSTREAMS"]
		AGC["Agent C: Bazel<br/>Mapping: WORKSTREAMS"]
		MERGE["Merge Agent Outputs<br/>Function: _merge_agents"]
	end

	APM --> BASE
	SPEC --> BASE
	BASE --> AGA
	BASE --> AGB
	BASE --> AGC
	AGA --> MERGE
	AGB --> MERGE
	AGC --> MERGE

	subgraph L4["Decision and Lifecycle Layer"]
		IMPACT["Impact Analysis<br/>Function: _impact_analysis"]
		CONFLICT["Conflict"]
		VALID["Valid"]
		REPLAN["Re-plan"]
		CONT["Continue"]
		BASE2["Updated Baseline (v2)"]
		REVAL["Re-validation"]
	end

	MERGE --> IMPACT
	IMPACT --> CONFLICT
	IMPACT --> VALID
	CONFLICT --> REPLAN
	VALID --> CONT
	REPLAN --> BASE2
	BASE2 --> REVAL

	subgraph L5["Output Layer"]
		EVID["Persist Evidence<br/>File: tools/ai_sdlc_poc/evidence.py<br/>Function: persist_evidence"]
		COMP["Compare to Ground Truth<br/>File: tools/ai_sdlc_poc/comparison.py<br/>Function: compare_against_reference"]
		CLI["CLI Output Artifacts<br/>File: tools/ai_sdlc_poc/__main__.py"]
	end

	REVAL --> EVID
	EVID --> COMP
	COMP --> CLI
```

Note: the diagram above shows ownership and data flow, not strict time order.

## Chronological Order (Live Execution)

```mermaid
flowchart TD
	A["Environment Setup"] --> B["APM available on PATH<br/>external CLI dependency"]
	A --> C["SpecKit available via pinned command<br/>tools/ai_sdlc_poc/adapters.py::_speckit_command"]

	B --> D["Run PoC CLI<br/>tools/ai_sdlc_poc/__main__.py"]
	C --> D

	D --> E["Start evaluation orchestration<br/>tools/ai_sdlc_poc/workflow.py::run_evaluation"]

	E --> F["Run APM sequence<br/>tools/ai_sdlc_poc/adapters.py::apm_sequence"]
	E --> G["Run SpecKit sequence<br/>tools/ai_sdlc_poc/adapters.py::speckit_sequence"]

	F --> H["Build report + baseline + impact + replan/validation<br/>tools/ai_sdlc_poc/workflow.py"]
	G --> H

	H --> I["Persist evidence bundles<br/>tools/ai_sdlc_poc/evidence.py::persist_evidence"]
	H --> J["Compare with reference artifacts<br/>tools/ai_sdlc_poc/comparison.py::compare_against_reference"]

	I --> K["Harbor report/evidence output"]
	J --> K
```

Run from the lifecycle repository root:

```powershell
python -m tools.ai_sdlc_poc --output artifacts/harbor-report.json
python -m tools.ai_sdlc_poc --mode live --output artifacts/harbor-report-live-plan.json
python -m tools.ai_sdlc_poc --mode live --execute-live --output artifacts/harbor-report-live-exec.json
python -m pytest tools/ai_sdlc_poc/test_workflow.py
```

Recommended full validation command:

```powershell
python -m pytest tools/ai_sdlc_poc/test_workflow.py tools/ai_sdlc_poc/test_evidence.py -q
```

The live-tool phase will replace the recorded SpecKit and APM fixture fields
with outputs from pinned `specify` and `apm` commands. The adapter remains
responsible for orchestration evidence, not for reimplementing either tool.

Pinned tool versions are recorded in `tools/ai_sdlc_poc/tooling.lock.json`.

If you need to bootstrap SpecKit locally for this lifecycle harness, use the
version pinned in `tools/ai_sdlc_poc/tooling.lock.json`:

```powershell
.\tools\ai_sdlc_poc\scripts\install_speckit.ps1
```

Evidence bundles are written under `tools/ai_sdlc_poc/evidence/`:

- `dr009/` contains APM-focused context packaging outputs.
- `dr010/` contains orchestration and lifecycle-flow outputs.
- Live step outputs are captured in `dr009/apm-steps.json` and
	`dr010/speckit-steps.json`.
- DR-010 writes both `impact-analysis.json`/`revalidation.json` and the
	compatibility names `impact.json`/`validation.json`.

## Main Code Locations

- `tools/ai_sdlc_poc/workflow.py`: deterministic Harbor workflow, concurrency,
	impact analysis, replan, validation, and live adapter wiring.
- `tools/ai_sdlc_poc/adapters.py`: planned/execute orchestration for SpecKit
	and APM command sequences.
- `tools/ai_sdlc_poc/evidence.py`: DR-009/DR-010 evidence bundle persistence
	and requirements tracking metadata export.
- `tools/ai_sdlc_poc/comparison.py`: normalization and comparison against
	reference Harbor artifacts.
- `tools/ai_sdlc_poc/test_workflow.py`: workflow behavior assertions.
- `tools/ai_sdlc_poc/test_evidence.py`: evidence output structure assertions.
