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

"""Run the deterministic lifecycle PoC replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.ai_sdlc_poc.evidence import persist_evidence
from tools.ai_sdlc_poc.workflow import run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["offline", "live"],
        default="offline",
        help="Select deterministic offline replay or live adapter mode.",
    )
    parser.add_argument(
        "--execute-live",
        action="store_true",
        help=(
            "Execute live adapter commands in --mode live. "
            "Without this flag, commands are emitted as planned only."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("harbor-report.json"),
        help="Path for the Harbor evidence report.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("tools/ai_sdlc_poc/evidence"),
        help="Directory for DR evidence bundles.",
    )
    args = parser.parse_args()
    report = run_evaluation(mode=args.mode, execute_live=args.execute_live)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    written = persist_evidence(report, args.evidence_root)
    print(f"Harbor PoC report written to {args.output}")
    print(f"Mode: {report['execution']['mode']}")
    print(f"Validation: {report['summary']['validation']}")
    print(f"Evidence files written: {len(written)}")


if __name__ == "__main__":
    main()
