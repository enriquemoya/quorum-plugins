#!/usr/bin/env python3
"""Structural checks for this marketplace. Standard library only.

These plugins are markdown, so nothing compiles and nothing type-checks. What
can still be wrong is the wiring: a router that names a command nobody wrote, a
state that exists in one file and not its neighbour, a manifest whose version
drifted from the marketplace's, a placeholder no schema defines. Every check
here exists because one of those was actually found, most of them by hand and
late.

`evals/evals.json` covers the other half — whether a skill does the right thing
when a model reads it. That is judged; this is decided. Neither replaces the
other, and this one is the one that can run on every commit.

    python3 scripts/check.py            # run everything
    python3 scripts/check.py --list     # name the checks and exit
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

FAILURES: list[str] = []
CHECKS: list[tuple[str, callable]] = []


def check(name: str):
    def register(fn):
        CHECKS.append((name, fn))
        return fn

    return register


def fail(where: str, message: str) -> None:
    FAILURES.append(f"{where}: {message}")


def tracked() -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True
    ).stdout
    return [ROOT / n.decode() for n in out.split(b"\0") if n]


def text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def manifests() -> list[tuple[Path, dict]]:
    return [
        (p, json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
    ]


# --------------------------------------------------------------------------
# 1. provenance
# --------------------------------------------------------------------------

_PROVENANCE = {
    "a personal name": r"\b(Jordan|Enmanuel|Alex|Doe|alice|Alice|bob|Bob|anita|maiev|wido|rosborne)\b",
    "a prior organisation": r"ballast\s*lane|\bperq\b|(?:former|prior|previous) employer",
    "an external product": r"\bengram\b|\bSAC4\b|gentleman-programming|dual[-_]harness|dh-dispatch|\bDH_[A-Z]",
    "a prior project": r"Electron-POS|electron-pos|fiscal\s?check",
    "a specific PR or CI run": r"\bPR-\d+\b|\bpipeline[ -]#?\d+\b|\bPRs #\d+",
    "first-person narration": (
        r"(?<![\w'])I\s+(?:also\s+|then\s+|had\s+to\s+)?"
        r"(?:wrote|ran|found|fixed|added|removed|built|made|chose|decided"
        r"|shipped|caught|lost|verified)\b|\bmy own\b"
    ),
}


@check("provenance — nothing names where this came from")
def _provenance() -> None:
    """A template that names its origin is not a template.

    Found the README claiming an origin on the day this check was written,
    which is the whole argument for having it: the scrub had been done by hand
    and by hand it missed a file.

    Quoted text is exempt for the narration rule only — a skill quoting what an
    agent should say ("I cannot act without a dossier") is content, not a
    claim about who wrote the code.
    """
    for path in tracked():
        body = text(path)
        if body is None or path.name == "check.py":
            continue
        for i, line in enumerate(body.split("\n"), 1):
            for what, pattern in _PROVENANCE.items():
                for m in re.finditer(pattern, line):
                    if what == "first-person narration" and line.count('"', 0, m.start()) % 2:
                        continue
                    fail(f"{rel(path)}:{i}", f"{what} — {m.group(0)!r}")


# --------------------------------------------------------------------------
# 2. wiring
# --------------------------------------------------------------------------


@check("wiring — every routed command and delegated agent exists")
def _wiring() -> None:
    """A router naming a command nobody wrote fails at the moment of use.

    Commands live in `commands/`, but a skill invoked as `/name` lives in
    `skills/<name>/SKILL.md`. Checking only the first is how `/quorum-init`
    read as missing when it was not.
    """
    commands = {p.stem for p in ROOT.glob("plugins/*/commands/*.md")}
    skills = {p.parent.name for p in ROOT.glob("plugins/*/skills/*/SKILL.md")}
    agents = {p.stem for p in ROOT.glob("plugins/*/agents/*.md")}
    invocable = commands | skills

    for path in ROOT.glob("plugins/*/commands/*.md"):
        body = text(path) or ""
        for name in set(re.findall(r"`/(quorum-[a-z-]+)`", body)):
            if name not in invocable:
                fail(rel(path), f"routes to /{name}, which is neither a command nor a skill")
        for name in set(re.findall(r"\*\*(quorum-[a-z-]+)\*\* agent", body)):
            if name not in agents:
                fail(rel(path), f"delegates to the {name} agent, which does not exist")


# --------------------------------------------------------------------------
# 3. states
# --------------------------------------------------------------------------

_STATE = re.compile(
    r"\b(TRIAGE|DRAFT_PRD|PRD_READY|ANALYZING|DRAFTING_SPEC|DRAFTING_ARCH"
    r"|DRAFTING_DESIGN|DRAFTING_TASKS|SCOPE_AUDIT|READY_WITH_CONDITIONS|READY"
    r"|NEEDS_REVISION|IN_PROGRESS|IMPL_AUDIT|NEEDS_FIX|VERIFIED_WITH_CONDITIONS"
    r"|VERIFIED|DELIVERING|MERGED|ABANDONED|SUPERSEDED|STUCK)\b"
)

_STATE_FILES = [
    "plugins/quorum-orchestrator/PIPELINE.md",
    "plugins/quorum-orchestrator/skills/quorum-status/SKILL.md",
    "plugins/quorum-orchestrator/commands/quorum-orchestrate.md",
]


@check("states — the three files that define them agree")
def _states() -> None:
    """The pipeline, the state contract and the router each list the states.

    Three copies of one set is three chances to drift. A state the router
    cannot route is a unit that stops with no next step; a state the router
    invents is a transition the contract will refuse.
    """
    sets = {}
    for name in _STATE_FILES:
        body = text(ROOT / name)
        if body is None:
            fail(name, "missing — the state set cannot be cross-checked")
            return
        sets[name] = set(_STATE.findall(body))

    union = set().union(*sets.values())
    for name, found in sets.items():
        for missing in sorted(union - found):
            fail(name, f"does not mention the state {missing}")


# --------------------------------------------------------------------------
# 4. placeholders
# --------------------------------------------------------------------------


@check("placeholders — every one used is defined in the schema")
def _placeholders() -> None:
    """`{{profile.x}}` resolving to nothing is a silently skipped step.

    Null is a legitimate value meaning "skip this concern". A placeholder the
    schema never defines is different: nobody decided to skip it, and nobody
    will notice that it was.
    """
    schema_path = ROOT / "plugins/quorum-orchestrator/PROFILE_SCHEMA.md"
    schema = text(schema_path)
    if schema is None:
        fail(rel(schema_path), "missing — placeholders cannot be checked")
        return

    for path in tracked():
        if path.suffix != ".md" or path == schema_path:
            continue
        body = text(path) or ""
        for m in re.finditer(r"\{\{(profile\.[a-z_.]+|role:[a-z-]+|ticket_url)\}\}", body):
            token = m.group(1)
            if token == "ticket_url":
                needle = "{{ticket_url}}"
            elif token.startswith("role:"):
                needle = token.split(":", 1)[1]
            else:
                needle = token.rsplit(".", 1)[-1]
            if needle not in schema:
                fail(rel(path), f"uses {{{{{token}}}}}, which PROFILE_SCHEMA.md does not define")


# --------------------------------------------------------------------------
# 5. manifests
# --------------------------------------------------------------------------


@check("manifests — valid JSON, and versions match the marketplace")
def _manifests() -> None:
    """The marketplace sat a minor release behind its own plugin.json.

    Nothing broke, which is the problem: an installer resolves the
    marketplace's number, so the drift decides which version people get and
    nothing reports it.
    """
    market_path = ROOT / ".claude-plugin/marketplace.json"
    try:
        market = json.loads(market_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(rel(market_path), f"unreadable: {exc}")
        return

    declared = {e["name"]: e["version"] for e in market.get("plugins", [])}
    for path, manifest in manifests():
        name, version = manifest.get("name"), manifest.get("version")
        if name not in declared:
            fail(rel(path), f"{name} is not listed in the marketplace")
        elif declared[name] != version:
            fail(
                rel(path),
                f"{name} is {version} here and {declared[name]} in the marketplace",
            )
    for name in declared:
        if name not in {m.get("name") for _, m in manifests()}:
            fail(rel(market_path), f"lists {name}, which has no plugin.json")


# --------------------------------------------------------------------------
# 6. frontmatter
# --------------------------------------------------------------------------


@check("frontmatter — every command and agent declares itself")
def _frontmatter() -> None:
    """A command with no frontmatter is a markdown file nobody can invoke."""
    for kind, pattern, required in (
        ("command", "plugins/*/commands/*.md", ("description",)),
        ("agent", "plugins/*/agents/*.md", ("name", "description")),
        ("skill", "plugins/*/skills/*/SKILL.md", ("name", "description")),
    ):
        for path in ROOT.glob(pattern):
            body = text(path) or ""
            if not body.startswith("---\n"):
                fail(rel(path), f"{kind} has no frontmatter")
                continue
            head = body.split("---", 2)[1]
            for field in required:
                if not re.search(rf"^{field}:", head, re.M):
                    fail(rel(path), f"{kind} frontmatter has no {field}")


# --------------------------------------------------------------------------
# 7. fences
# --------------------------------------------------------------------------


_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


@check("fences — code blocks are closed")
def _fences() -> None:
    """An unclosed fence swallows the rest of the file, silently.

    Counting occurrences of ``` is not enough, and the first run of this check
    proved it: a line reading "a fenced ```` ```mermaid ```` block" shows three
    backticks by wrapping them in four, which is correct markdown and counted
    as an opener. So this tracks fence LEVEL from line starts — a fence opens
    with three or more markers and closes with at least as many — which is what
    the markdown spec actually says and what a renderer actually does.
    """
    for path in tracked():
        if path.suffix != ".md":
            continue
        open_marker: str | None = None
        for line in (text(path) or "").split("\n"):
            m = _FENCE.match(line)
            if not m:
                continue
            marker = m.group(1)
            if open_marker is None:
                open_marker = marker
            elif marker[0] == open_marker[0] and len(marker) >= len(open_marker):
                open_marker = None
        if open_marker is not None:
            fail(rel(path), f"a {open_marker!r} fence is never closed")


# --------------------------------------------------------------------------
# 8. the example profile
# --------------------------------------------------------------------------


@check("example profile — parses, and covers every schema block")
def _example_profile() -> None:
    """The example is what people copy, so a block missing from it is a block
    most consumers never learn exists.

    YAML parsing needs a dependency this repo does not otherwise have, so it
    runs when PyYAML is importable and is reported as skipped when it is not.
    The coverage half needs no parser and always runs.
    """
    example_path = ROOT / "plugins/quorum-orchestrator/profile.example.yml"
    schema_path = ROOT / "plugins/quorum-orchestrator/PROFILE_SCHEMA.md"
    example, schema = text(example_path), text(schema_path)
    if example is None or schema is None:
        fail("profile example", "example or schema missing")
        return

    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        print("    (YAML parse skipped — PyYAML not installed)")
    else:
        try:
            yaml.safe_load(example)
        except yaml.YAMLError as exc:
            fail(rel(example_path), f"is not valid YAML: {exc}")

    schema_blocks = set(re.findall(r"^([a-z_]+):$", schema, re.M))
    example_blocks = set(re.findall(r"^([a-z_]+):$", example, re.M))
    for block in sorted(schema_blocks - example_blocks):
        fail(rel(example_path), f"has no `{block}:` block, but the schema defines one")


# --------------------------------------------------------------------------


def main() -> int:
    if "--list" in sys.argv:
        for name, fn in CHECKS:
            print(f"  {name}")
            if fn.__doc__:
                print(f"      {fn.__doc__.strip().splitlines()[0]}")
        return 0

    print(f"checking {len(tracked())} tracked files\n")
    for name, fn in CHECKS:
        before = len(FAILURES)
        fn()
        added = len(FAILURES) - before
        print(f"  {'FAIL' if added else 'ok  '}  {name}" + (f"  ({added})" if added else ""))

    if FAILURES:
        print(f"\n{len(FAILURES)} problem(s):\n")
        for line in FAILURES:
            print(f"  {line}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
