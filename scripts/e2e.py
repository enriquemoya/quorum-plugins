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


def test_preconditions_are_measured() -> None:
    """A BLOCKED claim is a measurement, and the rules that keep it one.

    Every assertion here answers a finding a three-family panel raised against
    an earlier, narrower version of this rule. Two were blockers.
    """
    status = doc("skills/quorum-status/SKILL.md")

    # The original defect: a proxy stood in for the capability.
    assert_that(
        "invokes the capability being claimed, not a proxy" in status,
        "a probe must invoke the capability, not a proxy for it",
    )
    # gpt, round 2: successful execution alone does not prove a negative.
    assert_that(
        "is not a probe that failed to run" in status and "exit_code" in status,
        "a broken probe is distinguished from an observed absence",
    )
    # grok + gpt, blockers: an unspecified cannot-probe terminal re-arms it.
    assert_that(
        "There is no cannot-probe state" in status,
        "there is no cannot-probe state to assert from",
    )
    # grok, round 2: without a visible record, "stays put" is a silent park.
    assert_that(
        "OPEN QUESTION" in status and "same-state history entry" in status,
        "an unprobeable precondition becomes a visible history entry",
    )
    # kimi: reachability is time-varying, so a claim carries its timestamp.
    assert_that(
        "only as current as its probe" in status,
        "a reachability claim carries the time it was measured",
    )
    # kimi: the rule has to bind more than the one agent that tripped over it.
    rules = doc("governance/rules/GLOBAL.md")
    assert_that(
        "Preconditions are measured, never inferred" in rules
        and "every stage that evaluates one" in rules,
        "the rule binds every stage, not only triage",
    )
    assert_that(
        "absent config file" in rules and "unset environment variable" in rules,
        "the two shapes that produced the incident are named",
    )


def test_panel_detects_configured_but_unreachable() -> None:
    """The state most operators meet first, and the ways of getting it wrong.

    Between installing the engine and paying for a provider, the panel is fully
    configured and entirely unreachable — the shipped default names paid seats
    and a fresh install has no credentials. Reported as "no critic panel
    configured", it sends the operator to write a config that already exists.

    Every assertion answers a finding a three-family panel raised against an
    earlier version of this fix, which proposed a catalogue lookup.
    """
    panel = doc("skills/quorum-panel/SKILL.md")

    assert_that(
        "panel configured but unreachable" in panel,
        "the fourth cause is named distinctly from an unconfigured panel",
    )
    # All three critics: catalogue presence is not credentialed reachability.
    assert_that(
        "Catalogue presence is not reachability" in panel,
        "a catalogue lookup is rejected as the reachability test",
    )
    # The engine already draws typo/gates/auth apart; do not rebuild it.
    assert_that(
        "Ask the engine; do not reimplement it" in panel
        and "critic panel" in panel
        and "provider:<model>" in panel,
        "the panel reads the engine's checks rather than reimplementing them",
    )
    # kimi: a binary probe collapses "could not check" into "absent".
    assert_that(
        "could not determine reachability" in panel,
        "an unusable diagnostic is indeterminate, not unreachable",
    )
    # grok, round 2: name-scraping with a closed fallback restores the defect.
    assert_that(
        "The fallback is open, never closed" in panel,
        "a renamed check falls back to indeterminate, never to unconfigured",
    )
    # kimi: per-seat partiality is already modelled; do not flatten it.
    assert_that(
        "partially reachable panel is" in panel,
        "a partly reachable panel is distinguished from a dead one",
    )


def test_bundled_files_are_resolved_not_guessed() -> None:
    """Six files locate a bundled file at run time. All six must do it the same way.

    An earlier draft of this fix would have repaired the command and left the
    other five resolving to nothing — the literal fallback deleted, the Glob
    still rooted nowhere. The uniformity is the point, so it is asserted per
    file rather than in aggregate.

    The middle ``**`` is checked because a smoke run showed a narrower pattern
    finding one layout while a second candidate sat unseen under the same root:
    a quieter version of the defect this replaced.
    """
    runtime = [
        ("plugins/quorum-orchestrator/commands/quorum-implement.md", "quorum-orchestrator"),
        ("plugins/quorum-orchestrator/agents/quorum-decision-documenter.md", "quorum-memory-bank"),
        ("plugins/quorum-orchestrator/agents/quorum-memory-synchronizer.md", "quorum-memory-bank"),
        ("plugins/quorum-orchestrator/agents/quorum-pattern-documenter.md", "quorum-memory-bank"),
        ("plugins/quorum-tooling/skills/quorum-memory-bank/SKILL.md", "quorum-memory-bank"),
        ("plugins/quorum-workflows/skills/quorum-agent-journal/SKILL.md", "quorum-obsidian-vault"),
    ]
    for rel, plugin in runtime:
        body = flat((ROOT / rel).read_text(encoding="utf-8"))
        short = rel.rsplit("/", 1)[-1]
        if short == "SKILL.md":
            short = rel.rsplit("/", 2)[-2] + "/SKILL.md"
        assert_that(
            "~/.claude/plugins`" in body or "~/.claude/plugins " in body,
            f"{short} roots its search at the parent",
            "not at a directory inside it",
        )
        assert_that(
            f"**/{plugin}/**/" in body,
            f"{short} keeps the middle ** in its pattern",
            "a version segment can sit between the plugin and its subdirectory",
        )
        assert_that(
            "STOP and report" in body,
            f"{short} stops rather than guessing",
            "no match, or more than one",
        )
    for rel, _ in runtime:
        body = flat((ROOT / rel).read_text(encoding="utf-8")).lower()
        short = rel.rsplit("/", 1)[-1]
        if short == "SKILL.md":
            short = rel.rsplit("/", 2)[-2] + "/SKILL.md"
        # Lower-cased on purpose: both "More than one match:" and "or more than
        # one:" are correct prose, and an assertion that pins the capitalisation
        # tests the sentence position rather than the rule.
        assert_that(
            "more than one" in body,
            f"{short} names the multiple-match case",
            "two layouts can coexist under one root",
        )


def test_implementation_stage_matches_the_pipeline() -> None:
    """The stage stopped being the entry point and kept the entry point's document.

    Each assertion below pins one contradiction that was actually in the file:
    a ticket key in the usage of a command whose frontmatter takes a slug, three
    flags the frontmatter never declared beside a missing one the preconditions
    depend on, a complexity derived here that triage already recorded, and a
    dry-run defined by a phase number in a file whose phases were about to be
    renumbered.
    """
    rel = "commands/quorum-implement.md"
    body = doc(rel)
    front = flat((PLUGIN / rel).read_text(encoding="utf-8").split("---")[1])

    # AC1 — a slug, and the ticket key demoted to a field
    assert_that(
        not re.search(r"/quorum-\w+ [A-Z]{2,}-\d+", body),
        "implement takes a slug, never a ticket key",
        "units on the spec path have no key",
    )
    assert_that(
        "carries its ticket key as a field" in body,
        "the ticket key survives as a field of the unit",
        "demoted, not deleted",
    )

    # AC2 — the two flag lists agree
    documented = {m.group(1) for m in re.finditer(r"\| `(--[a-z0-9-]+)` \|", body)}
    declared = set(re.findall(r"(--[a-z0-9-]+)", front))
    assert_that(
        documented == declared,
        "declared flags and documented flags are the same set",
        f"declared={sorted(declared)} documented={sorted(documented)}",
    )
    assert_that("--fix" in documented, "--fix is documented", "the preconditions depend on it")
    for gone in ("--complexity", "--resume", "--include-subtasks"):
        assert_that(gone not in documented, f"{gone} is gone", "decided per flag, in the spec")

    # AC4 — complexity is read, and no procedure for deriving it remains
    assert_that(
        "no procedure here for computing it" in body,
        "complexity is read from status.yml",
        "a value derived here can disagree with the audited one",
    )
    assert_that(
        "auto-detect" not in body.lower() and "classifies it" not in body,
        "no complexity-derivation procedure survives",
        "reading it and deriving it cannot both be true",
    )

    # AC5 — dry-run says what it stops before, not which phase
    assert_that(
        "before the first phase that writes" in body,
        "dry-run is described by what it stops before",
        "a phase number stops meaning what it says when phases are renumbered",
    )

    # AC6 — roles, not products; and the null-tracker case is stated
    assert_that(
        "{{role:tracker}}" in body,
        "the tracker is a role",
        "the profile models any tracker or none",
    )
    assert_that(
        "roles.tracker: null" in body and "no durable home at all" in body,
        "the null-tracker case has a stated answer",
        "transient and uncommitted, announced at the gate",
    )

    # AC7 — tasks.md is the plan, and the claimed precondition is checked
    assert_that(
        "`tasks.md` is the plan" in body,
        "tasks.md is the plan",
        "it arrived audited; re-planning produces a worse second plan",
    )
    assert_that(
        "naming criteria that\nexist in `requirements.md`" in flat(body)
        or "naming criteria that exist in `requirements.md`" in body,
        "the AC mapping is checked, not just claimed",
        "the preconditions have always asserted it",
    )

    # the gate count, which a --human unit may not change silently
    assert_that(
        "five stops" in body,
        "the stage states its own gate count",
        "removing phases changes how often a person is interrupted",
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
        test_preconditions_are_measured()
        test_panel_detects_configured_but_unreachable()
        test_bundled_files_are_resolved_not_guessed()
        test_implementation_stage_matches_the_pipeline()

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
