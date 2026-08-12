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

"""External tool adapter scaffolds for live PoC execution.

The default mode is "plan only" so the PoC can run without requiring tool
installation. When execution is enabled, commands are executed sequentially.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandSpec:
    name: str
    command: list[str]
    cwd: str


def _default_runner(spec: CommandSpec) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            spec.command,
            cwd=spec.cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as error:
        return {
            "name": spec.name,
            "command": spec.command,
            "cwd": spec.cwd,
            "status": "missing-tool",
            "returncode": 127,
            "stdout": "",
            "stderr": str(error),
        }

    return {
        "name": spec.name,
        "command": spec.command,
        "cwd": spec.cwd,
        "status": "ok" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _run_or_plan(
    specs: list[CommandSpec],
    execute: bool,
) -> list[dict[str, Any]]:
    if not execute:
        return [
            {
                "name": spec.name,
                "command": spec.command,
                "cwd": spec.cwd,
                "status": "planned",
            }
            for spec in specs
        ]

    return [_default_runner(spec) for spec in specs]


def speckit_sequence(repo_root: Path, execute: bool = False) -> dict[str, Any]:
    runtime_dir = _runtime_dir(repo_root, "specify")
    speckit_command = _speckit_command(repo_root)
    specs = [
        _speckit_bootstrap_spec(runtime_dir, speckit_command),
        CommandSpec("speckit-check", [*speckit_command, "check"], str(runtime_dir)),
        CommandSpec("speckit-workflow-list", [*speckit_command, "workflow", "list"], str(runtime_dir)),
    ]
    return {
        "tool": "speckit",
        "execute": execute,
        "runtime_dir": str(runtime_dir),
        "issue": ISSUE_TEXT,
        "steps": _run_or_plan(specs, execute),
    }


def apm_sequence(repo_root: Path, execute: bool = False) -> dict[str, Any]:
    runtime_dir = _runtime_dir(repo_root, "apm")
    specs = [
        CommandSpec("apm-init", ["apm", "init", "-y", "--target", "copilot"], str(runtime_dir)),
        CommandSpec("apm-install", ["apm", "install"], str(runtime_dir)),
        CommandSpec("apm-lock", ["apm", "lock"], str(runtime_dir)),
        CommandSpec("apm-compile", ["apm", "compile", "-t", "copilot"], str(runtime_dir)),
        CommandSpec("apm-audit", ["apm", "audit"], str(runtime_dir)),
    ]
    steps = _run_apm_sequence(runtime_dir, specs, execute)
    return {
        "tool": "apm",
        "execute": execute,
        "runtime_dir": str(runtime_dir),
        "steps": steps,
    }


ISSUE_TEXT = "Write unit tests for watchdog in ProcessGroupManager"


def _speckit_bootstrap_spec(runtime_dir: Path, speckit_command: list[str]) -> CommandSpec:
    if (runtime_dir / ".specify").exists():
        return CommandSpec("speckit-init-check", [*speckit_command, "version"], str(runtime_dir))

    return CommandSpec(
        "speckit-init",
        [
            *speckit_command,
            "init",
            ".",
            "--integration",
            "copilot",
            "--ignore-agent-tools",
            "--script",
            "py",
        ],
        str(runtime_dir),
    )


def _runtime_dir(repo_root: Path, tool_name: str) -> Path:
    runtime = repo_root / "tools" / "ai_sdlc_poc" / "runtime" / tool_name
    runtime.mkdir(parents=True, exist_ok=True)
    return runtime


def _speckit_command(repo_root: Path) -> list[str]:
    lock_path = repo_root / "tools" / "ai_sdlc_poc" / "tooling.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    version = lock["specify"]["version"]
    tag = version.replace(".dev0", "")
    if tag.startswith("v"):
        ref = tag
    else:
        ref = f"v{tag}"
    return [
        "uv",
        "tool",
        "run",
        "--from",
        f"git+https://github.com/github/spec-kit.git@{ref}",
        "specify.exe",
    ]


def _run_apm_sequence(
    runtime_dir: Path,
    specs: list[CommandSpec],
    execute: bool,
) -> list[dict[str, Any]]:
    if not execute:
        planned = [
            {
                "name": "apm-seed-content",
                "cwd": str(runtime_dir),
                "status": "planned",
                "path": str(runtime_dir / ".apm" / "instructions" / "score-ai-sdlc.instructions.md"),
            }
        ]
        planned.extend(_run_or_plan(specs, execute=False))
        return planned

    steps: list[dict[str, Any]] = []
    steps.append(_default_runner(specs[0]))
    steps.append(_seed_apm_content(runtime_dir))
    for spec in specs[1:]:
        steps.append(_default_runner(spec))
    return steps


def _seed_apm_content(runtime_dir: Path) -> dict[str, Any]:
    instructions_dir = runtime_dir / ".apm" / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    instruction_path = instructions_dir / "score-ai-sdlc.instructions.md"
    instruction_path.write_text(
        "---\n"
        "description: S-CORE AI-SDLC PoC runtime instruction\n"
        "applyTo: \"**/*\"\n"
        "---\n\n"
        "# S-CORE AI-SDLC PoC\n\n"
        "Use governed lifecycle workflow artifacts for the watchdog testing benchmark.\n",
        encoding="utf-8",
    )
    return {
        "name": "apm-seed-content",
        "cwd": str(runtime_dir),
        "status": "ok",
        "path": str(instruction_path),
    }
