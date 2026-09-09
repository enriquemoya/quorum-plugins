#!/usr/bin/env python3
"""End-to-end: build a repository, walk the pipeline over it, assert what held.

`check.py` decides whether the documents are consistent with each other. This
asks a different question — whether following them actually works — by building
a polyglot repository in a temp directory and walking a unit of work through
the routing table the router itself declares.

Four of these assertions exist because the first manual run of this walk found
four defects. Each one is pinned here so the fix cannot quietly come undone:
the gate exit code taken from a pipeline rather than a command, a workspace
declaration treated as the whole component list, a ticket path chosen with no
tracker to read from, and a decision matrix with two rows matching one case.

    python3 scripts/e2e.py           # run
    python3 scripts/e2e.py --keep    # leave the test bed for inspection
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins/quorum-orchestrator"

RESULTS: list[tuple[bool, str, str]] = []


def assert_that(ok: bool, name: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), name, detail))


def flat(text: str) -> str:
    """Collapse whitespace so a phrase can be matched across a line wrap.

    The first version of this suite grepped for a sentence that the source had
    wrapped mid-phrase, and reported a fix as missing when it was present. Any
    assertion about prose has to normalise first, or it tests the line width.
    """
    return re.sub(r"\s+", " ", text)


def doc(rel: str) -> str:
    return flat((PLUGIN / rel).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# the test bed
# --------------------------------------------------------------------------


def build_bed(root: Path) -> None:
    """A deliberately polyglot repository.

    The Python worker sits OUTSIDE the npm workspace on purpose: that is the
    shape that showed a workspace declaration cannot name every component.
    """
    (root / "apps/web/src").mkdir(parents=True)
    (root / "apps/api/src").mkdir(parents=True)
    (root / "workers/src").mkdir(parents=True)
    (root / ".github/workflows").mkdir(parents=True)

    (root / "package.json").write_text(
        json.dumps(
            {
                "name": "tb",
                "private": True,
                "workspaces": ["apps/web", "apps/api"],
                "scripts": {
                    "type-check": "tsc --noEmit",
                    "test:unit": "vitest run",
                    "lint": "eslint .",
                },
                "devDependencies": {"vitest": "^1.6.0", "typescript": "^5.4.0"},
            },
            indent=2,
        )
    )
    (root / "apps/web/package.json").write_text('{"name":"web","dependencies":{"vue":"^3.4.0"}}')
    (root / "apps/api/package.json").write_text(
        '{"name":"api","dependencies":{"fastify":"^4.0.0","pg":"^8.11.0"}}'
    )
    (root / "apps/web/src/index.ts").write_text('export const hello = () => "hi"\n')
    (root / "apps/api/src/main.ts").write_text(
        'import Fastify from "fastify"\nexport const app = Fastify()\n'
    )
    (root / "workers/src/worker.py").write_text("def run():\n    pass\n")
    (root / "docker-compose.yml").write_text("services:\n  db:\n    image: postgres:16\n")
    (root / ".github/workflows/ci.yml").write_text("name: ci\n")


# --------------------------------------------------------------------------
# 1. routing
# --------------------------------------------------------------------------


def parse_routes() -> dict[str, str]:
    """Read the routing table out of the router itself.

    Parsing the document rather than restating it is the point: a table that
    drifts from this suite's copy would pass, which is how a walk can be green
    against a router nobody can follow.
    """
    router = (PLUGIN / "commands/quorum-orchestrate.md").read_text(encoding="utf-8")
    block = re.search(r"\| Status \| Next \|\n\|---\|---\|\n((?:\|.*\|\n)+)", router)
    if not block:
        return {}
    routes: dict[str, str] = {}
    for line in block.group(1).strip().split("\n"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        for state in re.findall(r"`([A-Z_]+)`", cells[0]) or ["(none)"]:
            routes[state] = cells[1]
    return routes


def test_routing() -> None:
    routes = parse_routes()
    assert_that(len(routes) >= 20, "routing table parses", f"{len(routes)} states")

    # A spec-path, simple unit: the shortest legal walk to MERGED.
    walk = [
        "(none)", "TRIAGE", "DRAFT_PRD", "PRD_READY", "DRAFTING_SPEC",
        "DRAFTING_TASKS", "SCOPE_AUDIT", "READY", "IN_PROGRESS",
        "IMPL_AUDIT", "VERIFIED", "DELIVERING", "MERGED",
    ]
    missing = [s for s in walk if s not in routes]
    assert_that(not missing, "every state on the happy path routes", f"missing: {missing}")

    # The loop states have to route too, or a rejected unit dead-ends.
    loops = ["NEEDS_REVISION", "NEEDS_FIX", "STUCK"]
    missing = [s for s in loops if s not in routes]
    assert_that(not missing, "the loop and halt states route", f"missing: {missing}")

    assert_that(
        "HALT" in routes.get("STUCK", ""), "STUCK halts rather than routing", routes.get("STUCK", "")
    )


# --------------------------------------------------------------------------
# 2. the four regressions
# --------------------------------------------------------------------------


def test_gate_exit_code(bed: Path) -> None:
    """The defect that mattered most: a red gate reporting green.

    `npm run test:unit` with no node_modules exits 127. The same command piped
    to `tail` — which is how you get "the last 40 lines" the audit asks for —
    exits 0. This runs both, so the assertion rests on a measurement rather
    than on the claim being repeated.
    """
    if shutil.which("npm") is None:
        assert_that(True, "gate exit code (skipped — npm not installed)", "")
        return

    direct = subprocess.run(
        ["npm", "run", "test:unit"], cwd=bed, capture_output=True, text=True
    ).returncode
    piped = subprocess.run(
        "npm run test:unit 2>&1 | tail -1", cwd=bed, shell=True, capture_output=True, text=True
    ).returncode

    assert_that(direct != 0, "the gate really is red", f"direct exit {direct}")
    assert_that(
        piped == 0 and direct != 0,
        "a pipe hides the failure (this is why the rule exists)",
        f"direct {direct}, piped {piped}",
    )

    guidance = doc("commands/quorum-impl-audit.md") + doc("agents/quorum-audit.md")
    assert_that(
        "exit code of the COMMAND, never of a pipeline" in guidance
        or "exit code from the command, not from a pipeline" in guidance.lower()
        or "take the exit code from the command" in guidance.lower(),
        "the audit warns about the pipe",
    )
    assert_that("127" in guidance, "the audit distinguishes 127 from a real failure")


def test_component_sweep(bed: Path) -> None:
    """A workspace declaration names its own ecosystem and nothing else."""
    declared = set(json.loads((bed / "package.json").read_text())["workspaces"])
    present = {
        d.name if d.parent == bed else str(d.relative_to(bed))
        for d in (bed / "apps/web", bed / "apps/api", bed / "workers")
    }
    outside = present - declared - {"apps/web", "apps/api"}
    assert_that(
        "workers" in outside,
        "the bed has a component outside the workspace",
        f"declared {sorted(declared)}, outside {sorted(outside)}",
    )

    table = doc("skills/quorum-init/references/detection-table.md")
    assert_that(
        "blind to every other" in table and "sweep the rest of the tree" in table,
        "the detection table says a declaration is ecosystem-scoped",
    )
    assert_that("keep sweeping" in doc("skills/quorum-init/SKILL.md"), "the init step sweeps too")


def test_ticket_path_needs_a_tracker() -> None:
    triage = doc("agents/quorum-triage.md")
    assert_that(
        "is the ticket path even available" in triage and "roles.tracker" in triage,
        "triage checks the tracker before choosing an origin",
    )


def test_matrix_precedence() -> None:
    pipeline = doc("PIPELINE.md")
    assert_that(
        "first match wins" in pipeline.lower(),
        "the decision matrix declares row precedence",
    )
    assert_that(
        "constitution row" in pipeline and "override" in pipeline,
        "the constitution row is stated to override the loop row",
    )


# --------------------------------------------------------------------------
# 3. the gates hold
# --------------------------------------------------------------------------


def test_gates_hold() -> None:
    """The refusals that make the pipeline more than a sequence of prompts."""
    audit = doc("agents/quorum-audit.md")
    assert_that("Silent passes are forbidden" in audit, "silent passes are forbidden")
    assert_that("You never fix" in audit or "never fix" in audit, "the auditor does not fix")
    assert_that(
        "audit_iterations` comes from" in audit or "read from the file" in audit,
        "the iteration counter is read from the file",
    )

    panel = doc("skills/quorum-panel/SKILL.md")
    assert_that(
        "Exits 2 on an incomplete debate" in panel or "exit code" in panel,
        "the panel refuses to conclude an incomplete debate",
    )
    assert_that("single-provider" in panel, "the panel records when it degraded")

    delivery = doc("agents/quorum-delivery.md")
    assert_that("never runs automatically" in delivery, "delivery never runs automatically")
    assert_that(
        "MERGED" in delivery and "only when the merge actually happened" in delivery,
        "MERGED is written after the merge, not at PR open",
    )

    prd = doc("agents/quorum-prd.md")
    assert_that("always human-interactive" in prd, "the PRD stage stays human")


# --------------------------------------------------------------------------


def test_governance_corrections() -> None:
    """The three defects the dogfood run found in the process itself.

    Each is pinned because each was shipped: a consumer writing a real
    `tasks.md` hits the first immediately, and the other two are holes an audit
    falls into rather than defects it reports.
    """
    standard = doc("governance/rules/SPEC_STANDARD.md")
    assert_that(
        "nothing wraps it" in standard and "indented continuation" in standard,
        "the task format states that the task line does not wrap",
    )
    # The format has to survive a task with three paths, which is what broke it.
    sample = (
        "- [ ] T7: wire the export job — files: a/one.ts, a/two.ts, w/three.py — AC: AC3, AC4\n"
        "      Prose beneath, on as many lines as it needs.\n"
    )
    parsed = re.findall(r"- \[ \] (T\d+): .+? — files: (.+?) — AC: (.+)$", sample, re.M)
    assert_that(
        len(parsed) == 1 and len(parsed[0][1].split(",")) == 3,
        "a three-path task parses under the corrected format",
        f"{len(parsed)} parsed",
    )

    proposal = doc("governance/rules/AUDIT_PROPOSAL.md")
    assert_that("| governance" in proposal, "a proposal can target the process itself")
    assert_that(
        "never blocks the unit that raised it" in proposal,
        "a governance finding does not block the unit that found it",
    )

    status = doc("skills/quorum-status/SKILL.md")
    assert_that("BLOCKED` is not terminal and is not `STUCK`" in status,
                "BLOCKED is distinguished from STUCK")
    assert_that("blocked_on:" in status, "a BLOCKED unit records what it is waiting for")
    assert_that("not BLOCKED" in status, "the queue excludes BLOCKED units")
    assert_that(
        "BLOCKED" in doc("commands/quorum-orchestrate.md"),
        "the router routes BLOCKED",
    )


def main() -> int:
    keep = "--keep" in sys.argv
    bed = Path(tempfile.mkdtemp(prefix="quorum-e2e-"))
    try:
        build_bed(bed)
        print(f"test bed: {bed}\n")

        test_routing()
        test_component_sweep(bed)
        test_ticket_path_needs_a_tracker()
        test_matrix_precedence()
        test_gate_exit_code(bed)
        test_gates_hold()
        test_governance_corrections()

        width = max(len(n) for _, n, _ in RESULTS)
        for ok, name, detail in RESULTS:
            print(f"  {'ok  ' if ok else 'FAIL'}  {name:<{width}}  {detail}")

        failed = [n for ok, n, _ in RESULTS if not ok]
        print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
        if failed:
            print("\nfailures:")
            for n in failed:
                print(f"  {n}")
        return 1 if failed else 0
    finally:
        if keep:
            print(f"\ntest bed kept at {bed}")
        else:
            shutil.rmtree(bed, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
