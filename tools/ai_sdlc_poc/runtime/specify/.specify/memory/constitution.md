# Lifecycle AI-SDLC PoC Constitution

## Core Principles

### I. Reproducible Evidence First
Every workflow execution must produce deterministic, reviewable artifacts. The AI-SDLC PoC is valid only when outputs can be replayed and compared against known baselines.

### II. Tool Orchestration, Not Tool Reimplementation
This runtime orchestrates SpecKit and APM steps and records their evidence. It must not duplicate or replace the domain logic of either tool.

### III. Test-Backed Changes (Non-Negotiable)
All behavior changes must be covered by automated tests before merge. At minimum, relevant tests under tools/ai_sdlc_poc must pass, including workflow and evidence persistence checks.

### IV. Impact-Driven Replanning
Requirement changes must trigger explicit impact analysis, invalidation tracking, and replan/revalidation artifacts. No silent continuation is allowed after a detected conflict.

### V. Traceability and Provenance
Each generated artifact must preserve enough context to explain inputs, baseline identity, tooling versions, and execution mode. Reports must remain auditable by other engineers without hidden state.

## Engineering Constraints

- Keep changes focused and minimal to preserve deterministic behavior.
- Preserve compatibility with lifecycle repository conventions (Bazel-first build/test flow, Apache-2.0 licensing context, and existing artifact paths).
- Prefer explicit structured outputs (JSON plus concise text digests) for machine and human review.
- Avoid introducing non-essential runtime dependencies.

## Language and Build Matrix

### Python Scope (This PoC Runtime)
- Primary code: tools/ai_sdlc_poc.
- Expectations: deterministic behavior, explicit data schemas, stable JSON outputs, and targeted pytest coverage for workflow and evidence.
- Runtime/tool orchestration versions must align with tools/ai_sdlc_poc/tooling.lock.json.

### C++ Scope (Lifecycle Product Code)
- Core implementation areas include score/launch_manager and score/health_monitor.
- PoC changes must not assume C++ API behavior without evidence or tests.
- Cross-language impacts must be documented when PoC outputs influence C++ implementation tasks.

### Rust Scope (Lifecycle Product Code)
- Rust workspace members are defined in Cargo.toml.
- PoC artifacts that claim Rust impact must reference concrete modules/crates and expected verification paths.
- Respect workspace lint posture (e.g., clippy/rust warnings) when proposing Rust-facing changes.

### Build and Test Orchestration
- Bazel is the default system-level build/test entrypoint in lifecycle.
- Cargo workspace is authoritative for Rust crate membership and local Rust iteration.
- Python tooling/typing constraints follow repository configuration (including basedpyright settings at repo root).

## Workflow and Quality Gates

1. Define or update spec and tasks with requirement references.
2. Verify constitution compliance before implementation.
3. Implement in small, testable increments.
4. Run targeted tests for changed behavior and evidence generation.
5. For PoC runtime changes, execute:

```powershell
python -m pytest tools/ai_sdlc_poc/test_workflow.py tools/ai_sdlc_poc/test_evidence.py -q
```

6. For lifecycle-wide integration-sensitive changes, define and run the relevant Bazel tests (for example under //score/... and //tests/...) appropriate to the touched components.
7. Confirm reproducibility and expected impact/revalidation outputs.
8. Merge only when artifacts, tests, and traceability are complete.

## Governance

- This constitution overrides informal local practices for this runtime.
- Pull requests must document how each core principle is satisfied or why it is not applicable.
- Exceptions require written justification in the change record and a follow-up action to remove the exception.
- Amendments must include: motivation, concrete text diff, version bump rationale, and ratification by maintainers of lifecycle/tools/ai_sdlc_poc.

**Version**: 1.1.0 | **Ratified**: 2026-08-12 | **Last Amended**: 2026-08-12
