# AI-SDLC PoC TODO (Lifecycle)

## Scope Boundary (Locked)
- [x] Harbor is evaluation layer.
- [x] APM, SpecKit, and SDLC Orchestrator are system under evaluation.
- [x] PoC implementation lives in lifecycle repository.
- [ ] Harbor external dependency is configured and pinned.
- [x] SpecKit CLI is installed and pinned.
- [x] Lifecycle install helper for SpecKit bootstrap command is documented.
- [x] APM CLI is installed and pinned.

## Implementation Backlog
- [x] Add deterministic offline workflow adapter (`tools/ai_sdlc_poc/workflow.py`).
- [x] Add executable entrypoint (`python -m tools.ai_sdlc_poc`).
- [x] Add focused tests for context equality, impact/re-plan, reproducibility.
- [x] Generate initial Harbor-style evidence report.
- [x] Add runner mode: `--mode offline|live`.
- [x] Add live SpecKit adapter scaffold with planned/execute command steps.
- [x] Add live APM adapter scaffold with planned/execute command steps.
- [x] Isolate live tool execution under `tools/ai_sdlc_poc/runtime/`.
- [x] Persist DR evidence bundles to `tools/ai_sdlc_poc/evidence/`.
- [x] Persist real SpecKit output artifacts from live execution.
- [x] Persist real APM output artifacts from live execution.
- [x] Collect APM lockfile digest and package provenance from live run.
- [x] Wire shared design baseline v1 to concurrent workstreams.
- [x] Wire merge artifact generation for Agent A/B/C outputs.
- [x] Implement requirement-change loopback trigger (`serviceWatchdog()` run-cycle requirement).
- [x] Implement impact analysis output over affected artifacts:
  - [x] specification
  - [x] tasks
  - [x] Agent B tests
  - [x] design baseline
- [ ] Implement re-plan to baseline v2 and re-validation gate.
- [x] Add comparison module against PR #444 ground truth artifacts.

## Validation Backlog
- [x] Local pytest execution passes for offline adapter.
- [ ] Bazel target execution passes in environment with Bazel on PATH.
- [ ] Reproducibility check: two clean runs produce same normalized digest.
- [ ] Live execute check: all agents consume same APM context digest.
- [x] Live planning check: sequential and concurrent reports emitted by Harbor layer.

## DR Mapping Outputs
- [ ] DR-009 evidence bundle:
  - [x] identical context hash export path (`dr009/context-digest.txt`)
  - [x] APM lock/provenance file generation (`dr009/apm-lock.json`, `dr009/provenance.json`)
  - [x] live APM step output capture (`dr009/apm-steps.json`)
  - [ ] Validate with live execute outputs
- [ ] DR-010 evidence bundle:
  - [x] issue/spec/baseline/tasks/implementation/tests structure export (`dr010/sequential.json`)
  - [x] merge -> impact -> re-plan -> re-validation export files
  - [x] live SpecKit step output capture (`dr010/speckit-steps.json`)
  - [ ] Validate with live execute outputs
  - [ ] reproducibility statement and limits

## Open Environment Constraints
- [ ] Confirm Harbor source/reference package location for integration.
- [ ] Ensure `bazel` executable is available in shell PATH for Bazel target validation.
- [ ] Confirm network access/policy for installing SpecKit/APM and capturing pinned versions.

## Current Pins
- SpecKit CLI: 0.16.1.dev0 (`specify --version`)
- APM CLI: 0.28.0 (`apm --version`)
- Lock file: `tools/ai_sdlc_poc/tooling.lock.json`
