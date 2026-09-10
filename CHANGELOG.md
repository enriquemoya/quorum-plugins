# Changelog

All notable changes to this marketplace are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); each plugin is
versioned independently and its version lives in `marketplace.json`.

A note on what "tested" means here. The product is prose — nothing compiles —
so a guarantee with no assertion is a sentence. Two suites enforce that:
`scripts/check.py` (10 checks over every tracked file) and `scripts/e2e.py` (43
assertions over the documents' contracts). Both were built by injecting defects
and watching them fail. Anything below that is *not* covered by them says so.

## [Unreleased]

### quorum-tooling 3.0.1 · quorum-workflows 2.0.1

#### Fixed

- **Two manifests declared a `commands` directory that does not exist.** The
  runtime reports that as a load failure and the plugin's components never load
  — a total failure, and invisible from inside this repository where every file
  is present and every suite is green. One plugin had never had a commands
  directory; the other lost its only command earlier in the same session when a
  name collision was resolved by deleting it, and removing the file did not
  remove the declaration.

  Found by running the platform's own `claude plugin validate` for the first
  time, on a marketplace already published twice. `check.py` now asserts that
  every declared component path exists.

- **A verified unit with unchecked tasks.** Seven units had been marked
  VERIFIED while their task lists still showed open boxes — the same defect as a
  state file disagreeing with its diff, which this repository shipped once
  already. `check.py` now fails on it. ABANDONED and SUPERSEDED are exempt:
  there, open tasks are the honest record of what the unit did not do.

#### Documented

- **How to upgrade.** `claude plugin install` on something already installed is
  a no-op that reports success; `update` is the verb. This was never tested
  before and the documentation never said it.

- **An upgrade leaves the previous version directory in place**, so a
  cache-rooted search for a bundled file returns two matches on any machine that
  has upgraded once. The multiple-match branch was recorded as fixture-only on
  the reasoning that "one machine has one layout" — that reasoning was wrong,
  and the branch is the ordinary case rather than a corner. Verified after
  2.1.0 → 3.0.0: two matches, and the registry resolved to the right one.


### quorum-orchestrator 3.0.0 · quorum-tooling 3.0.0 · quorum-workflows 2.0.0

**Major, because a consumer repository that named a tracker-specific tool in its
own profile or overrides will find those references gone.** Nothing else in the
contract changed.

#### Fixed

- **The tracker driver's name stays inside the driver.** Thirty-five files
  described steps they could not perform — calling one product's tools directly,
  extracting credentials from a named MCP server's environment block, validating
  keys against a hardcoded prefix. 239 mentions, 58 tool calls, and 27 files that
  talked about tickets while referencing neither `{{role:tracker}}` nor the
  profile. Zero now, outside the driver skill and the two files that ARE the
  abstraction.

  Three operations, not the two the spec first proposed: delegate where the file
  reads or writes tracker state, genericise where it only links to one, delete
  where it had no business knowing. The middle case was found during
  implementation — the vault tree legitimately links to a ticket without needing
  one, and deleting those mentions would have lost something real.

- **`same-evidence-thrice` could not fire.** The rule stops a loop that keeps
  finding the same thing inside the iteration cap, and it reads
  `evidence_digest`. That digest lived only in `last_audit`, where each iteration
  overwrote the one before — so exactly one value ever existed and "seen three
  times" had nothing to compare against. It was written down, it read as a bound,
  and it bounded nothing. The digest is appended to each history entry now, and
  `last_audit` is named as display-only so nobody wires the check back to it.

#### Added

- `check.py` — the tracker check, with a **closed** matcher (product names, tool
  names, key patterns) rather than "ticket-words", because a loose matcher
  pressures a correct conditional annotation toward a spurious role reference.
  Three injections watched failing; the driver passes.
- `e2e.py` — 103 assertions, including one that the same-evidence bound reads
  the history.
- `.claude/runs/panel-tiers/BENCHMARK.md` — the tier comparison, whose
  conclusion is not the obvious one.

#### A correction about the constitution

An earlier draft called the tracker leak an **Article 2** violation. It is not
one. Article 2 forbids naming an external product the repository does not
integrate with; through its driver skill it integrates with this one. "The
driver may name it, the agnostic layer may not" is a design rule of this
marketplace, and citing the constitution for it was borrowed authority. The rule
stands on its own: a skill that describes steps it cannot perform is wrong.

#### Known, recorded, not fixed

- The tracker check is a **lexical invariant**. It proves a file that names a
  tracker also names an approved way to reach one. An inert reference satisfies
  it, and it does not prove any delegation is correct.
- Deleting tracker mentions from 19 files changed conventions that no suite
  exercises — the e2e count says nothing about the tracker path. Over-deletion is
  additive and cheap to restore; it is recorded as a known non-goal rather than
  waiting to be discovered.
- `check.py` reads `git ls-files`: a new file is outside every guard until it is
  committed.
- The `installed-paths` conditions carry forward unchanged.


### quorum-orchestrator 2.2.0 · quorum-tooling 2.2.0 · quorum-workflows 1.1.0

Everything here came from **installing the marketplace and using it**, which had
never been done. Both suites check the documents; the documents were internally
consistent and two of them were wrong about the machine.

#### Fixed

- **A bundled file is located by asking the runtime, not by guessing its
  layout.** Six files resolve `installPath` out of
  `~/.claude/plugins/installed_plugins.json`, verify the file is there, and fall
  back to a Glob rooted at `~/.claude/plugins/cache` only when the entry is
  missing. Never the parent: a marketplace clone sits beside the installed
  copies under it, so a parent-rooted search finds two files of which one is
  loaded.

- **`quorum-code-review` was a command and a skill.** The runtime lists both in
  one `/` namespace, so it picked, and neither file said which. The two had
  drifted — the skill states that it writes the review file and does not stage
  or commit it; the command never mentioned that, so half the callers got an
  artifact with no statement about who commits it. The command is deleted and
  the skill owns the name.

- **The implementation stage describes what it does.** Five phases, not the
  seven it had when it was the entry point, and the document says five stops
  rather than leaving them to be counted. Fetch and plan are reads now —
  `tasks.md` arrives audited and re-planning produced a second plan with less
  information. The tracker is a role everywhere, and a repository with no
  tracker gets a stated answer rather than a silence.

#### Added

- `check.py` — install-path depth check, and a namespace check that fails on any
  name declared in both a `commands/` and a `skills/` directory.
- `e2e.py` — 43 assertions became 98. The resolution is now **executed** against
  a fixture holding a marketplace clone, an installed copy and the registry;
  the Glob root is parsed out of the prose and run, rather than compared to
  itself.
- `GLOBAL.md` — a probe records the state it ran under.

#### A wrong fix, kept in the history

The first version of the install-path fix **broke resolution on every machine**,
and is worth reading in the log rather than only here. It rooted the search at
`~/.claude/plugins` on the finding that `cache/` did not exist. That finding was
measured between registering a marketplace and installing a plugin — registration
clones and reports success; installation is what creates `cache/`. The original
instruction had been right on all three counts, including a version segment in
its example, and the rewrite replaced a working instruction with one whose own
ambiguity rule would have stopped it.

It never shipped. It was caught by taking a critic's suggestion literally: it
said the multiple-match branch was exercisable with a decoy rather than
unexercisable on one machine, and the decoy run returned three matches, the
second of which was the directory reported as nonexistent an hour earlier.

#### Known, recorded, not fixed

- `check.py` reads `git ls-files`, so a new file is outside the guard until it
  is committed. This is how the install-path check passed at commit time and
  failed immediately after.
- `.claude/specs/` and `.claude/runs/` are exempt from the install-path check.
  Two critics called it a place a defect can live and neither withdrew.
- The cache-rooted fallback is an inference about the runtime's layout, observed
  on registry format version 2.
- The three units listed in the previous release remain open, plus
  `iteration-cap-decision`.


### quorum-orchestrator 2.1.0

Everything here came out of running the pipeline on this repository — writing
specs for its own missing pieces and putting each through the cross-provider
panel. Five debates, three model families, and the panel rejected the proposed
fix in four of them, each time producing something better than what was
proposed.

#### Changed

- **`quorum-status`: `BLOCKED` requires a probe that ran.** A `BLOCKED` claim
  now carries the invocation, its exit code, what it observed and when. There
  is deliberately no cannot-probe state: a precondition that could not be
  measured leaves the unit un-blocked rather than blocked on a guess. This
  correction exists because a unit in this very repository was declared
  `BLOCKED` on inferred evidence — an absent config file and unset environment
  variables — while seven models were reachable the whole time.

- **`quorum-panel`: detection asks the engine instead of reimplementing it.**
  Four distinct causes plus two indeterminate outcomes, where there had been a
  single boolean. A catalogue listing is explicitly rejected as the
  reachability test — presence is not reachability — and an unusable diagnostic
  is indeterminate, never "unconfigured". The fallback is open by default: a
  detection that cannot decide runs the degraded panel and says so, rather than
  refusing.

- **`quorum-panel`: the CPD path states measurements, not properties.** The
  incomplete-debate refusal now appears with its exit code, its empty stdout
  and its stderr message, re-observed on the current engine rather than
  inherited from a transcript that predates a change to the appended contract.
  The severity contract is described as appended by the dispatch layer *and*
  embedded by the author, both. The terminal findings block is never fenced.

- **`GLOBAL.md`: preconditions are measured, never inferred.** Names both
  shapes that caused the false `BLOCKED`: an absent configuration file and an
  unset environment variable, neither of which is evidence of anything.

- **`SPEC_STANDARD.md`: the task line format is fixed.** The task's own line
  carries `files:` and `AC:`, with prose indented beneath it. The previous
  wording described a shape no task in this repository actually had.

#### Added

- **`PIPELINE.md`** — the process anchor. Nine stages, two origins (ticket and
  spec), a 23-state machine, and a decision matrix with declared row
  precedence: the constitution row and the two `STUCK` rows override any row
  above them. Five things are never automatic in either autonomy mode — a
  constitution violation, a scope promotion, delivery, `STUCK`, and a
  single-provider verdict advancing past the implementation audit.

- **`/quorum-orchestrate`** — the single entry point, which routes and never
  executes. `--queue` derives its batch from `status.yml` rather than a stored
  list, drops units whose dependencies are unmerged, and refuses to run two
  units whose file sets fall in the same profile component.

- **A constitution for this repository** — three articles, each checkable by
  pointing at a file and a line. Article 3 is the one that shapes everything
  else: no guarantee without an assertion that has been *watched failing*.

- **Skill evals** for `quorum-init`, `quorum-panel` and `quorum-status`.

- **A precondition sweep in `scripts/check.py`**, which reports and never
  corrects — a repaired state file is a state file someone guessed at.

#### Known, recorded, not fixed

These are written down as units with specs rather than left as intentions:

- **`implement-phases`** — `/quorum-implement` still runs the seven phases it
  had when it *was* the entry point, five of which the pipeline now does
  upstream. The spec is written and its scope audit escalated; the
  implementation is a human gate and has not been taken. **Not tested, not
  changed.**
- **`verdict-credit-on-ambiguity`** — a seat whose reply carries no verdict
  token records `concerns` with zero findings and votes anyway. Deferred with
  evidence; it collides with never-shrink and `debate_complete` and needs its
  own unit.
- **One product name still appears in 41 tracked files.** None is under
  `governance/`, and the repository does integrate with that product through a
  driver skill, so the violation is narrower than it looks: the name leaks from
  the driver into layers that must work with any tracker or none. The sweep is
  its own unit.

#### What is not covered by the suites

The suites check the documents. They do not run a pipeline end to end against a
real repository, and they cannot: a full run costs model calls across several
providers. The cross-provider path was exercised by hand — six debates, three
families — and the transcripts are committed under `.claude/runs/` so a reader
can check the claims without re-spending them.
