..
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

Lifecycle Spec-Driven Development
################################

Abstract
========

This document defines the Spec-Driven Development (SDD) approach for the
``lifecycle`` repository when using SpecKit.

The purpose of SDD in this repository is to move feature work through a
repeatable sequence of specification, planning, task breakdown, and
implementation while keeping the feature intent traceable to the repository
requirements and architecture constraints.

SDD workflow
============

The default lifecycle SDD flow is:

1. ``specify``: capture the feature intent as a spec.
2. ``plan``: map the spec to the implementation approach.
3. ``tasks``: break the plan into executable work items.
4. ``implement``: apply the changes in the codebase.
5. Review gates: validate the output before advancing to the next stage.

The PoC harness in ``tools/ai_sdlc_poc`` uses this flow as the benchmark
shape for comparing generated outputs.

Scope
=====

This SDD definition applies to lifecycle feature work that needs a clear
trace from issue to implementation, especially where concurrent workstreams,
merge decisions, and re-planning are expected.

It is intended to support feature development in the lifecycle repository and
does not replace the existing architecture, safety, or verification
documentation.

Inputs
======

The SDD process is expected to start from:

* a feature issue or requirement statement,
* the lifecycle architecture and component constraints,
* the repository conventions and test strategy,
* the pinned SpecKit and APM toolchain used by the PoC harness.

Outputs
=======

An SDD run should produce, at minimum:

* a specification artifact,
* a plan artifact,
* a task breakdown,
* implementation changes,
* review and validation evidence.

For the benchmark case exercised by the PoC, the outputs are compared against
the stored Harbor reference reports for the issue tracked in PR #444.

Operating rules
===============

* Keep the specification focused on the feature intent, not the code shape.
* Keep the plan aligned with repository constraints and the existing module
  structure.
* Treat task output as actionable work items that can be reviewed
  independently.
* Re-plan when a requirement change affects the current baseline or invalidates
  a workstream.
* Preserve traceability between the issue, the SDD artifacts, and the final
  implementation.

Traceability
============

The SDD process for lifecycle is evaluated in the PoC under
``tools/ai_sdlc_poc``. That harness records the sequential and concurrent
artifact shapes, the merge output, the requirement-change impact, and the
re-validation step.

For the current benchmark slice, the reference issue is #439 and the ground
truth comparison target is PR #444.
