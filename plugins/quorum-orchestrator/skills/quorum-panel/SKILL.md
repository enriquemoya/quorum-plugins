---
name: quorum-panel
argument-hint: "<debate-id> --brief <file> [--security-brief <file>] [--lenses a,b,c]"
description: Runs an adversarial critic panel over a decision or a diff, in two rounds with a mandatory per-critic rebuttal, and refuses to render a verdict on an incomplete debate. Uses the cross-provider engine when it is installed; falls back to a same-provider panel and says so. Shared by both audit gates.
---

# The panel

A single reviewer agrees with itself. This runs several critics over the same
question, independently, then makes each one answer a rebuttal before any
verdict is rendered.

Two implementations, one contract. Which one ran is recorded, because they are
not equally strong and a verdict that hides the difference is a silent pass on
the method.

## Detection

Probe in this order. The order matters: `cpd-stats` fails when `.quorum/` is
absent, so testing the engagement first is what makes its failure mean
"no panel configured" rather than "not here".

```bash
command -v quorum >/dev/null 2>&1   || REASON="engine not installed"
test -d .quorum                     || REASON="not a Quorum engagement"
quorum cpd-stats >/dev/null 2>&1    || REASON="no critic panel configured"
```

Then a fourth question the first three cannot answer: **the panel is
configured — can its seats actually be reached?**

That is the ordinary state between installing the engine and paying for a
provider. The shipped default names paid seats and a fresh install has no
credentials, so a panel that is fully configured and entirely unreachable is
what most operators meet first. Without this probe it reports as "no critic
panel configured", sending them to write a config that already exists.

### Ask the engine; do not reimplement it

Run `quorum doctor` and read the checks it already emits. Three of them draw
distinctions a catalogue lookup cannot:

| Check | Means | The operator's fix |
|---|---|---|
| `critic panel` fails | seats violate the harness gates | change the seats or the gates |
| `panel catalog` warns | seats absent from the provider catalogue | a typo, or that tier is not offered |
| `provider:<model>` fails | the seat exists and the dispatch fails | authenticate, or change tier |

**Catalogue presence is not reachability.** A seat can be listed and
unauthorised; only `provider:<model>` establishes it, because that check
dispatches to the seat rather than looking it up. Reading the catalogue alone
would report a reachable panel that cannot run a round.

`provider:<model>` is per seat, so a partially reachable panel is
representable. Report the reachable count and name the unreachable seats — a
panel of three with one dead seat is not the same as a dead panel, and
collapsing them loses the distinction that decides whether a round can run.

### When the diagnostic cannot answer

Two failures are not the panel being unreachable, and neither may be recorded
as though it were:

**The diagnostic did not run.** Missing binary, non-zero exit for its own
reasons, no output. Record `panel_reason: "could not determine reachability"`
and say what was tried. A probe that failed to run and a probe that observed
absence are opposite conclusions.

**The expected checks are not in the output.** The engine may rename or
restructure its checks; this skill reads them by name and has no contract
guaranteeing those names. When `critic panel`, `panel catalog` and
`provider:` are all absent from a `doctor` run that otherwise succeeded, that
is a version mismatch, not a reachable panel and not an unconfigured one.

**The fallback is open, never closed.** Do not fall back to "no critic panel
configured" — that is the wrong answer this whole probe exists to stop
producing, and reaching it through a rename would restore the defect silently.
Fall back to "could not determine", which is true.

### What each outcome records

| Outcome | Path | `panel_reason` |
|---|---|---|
| all four pass | cross-provider | *(null)* |
| engine absent | same-provider | `engine not installed` |
| not an engagement | same-provider | `not a Quorum engagement` |
| no panel configured | same-provider | `no critic panel configured` |
| configured, seats unreachable | same-provider | `panel configured but unreachable: <the doctor line>` |
| diagnostic unusable | same-provider | `could not determine reachability: <what was tried>` |

Four distinguishable causes plus two indeterminates, because the operator's
next step differs for each — install the engine, run `quorum init`, configure a
panel, authenticate, or look at why the diagnostic will not answer.

State which path is running, and why, **before** the round starts. An operator
who learns at the verdict that the panel was degraded has already spent the run.

## Path A — cross-provider (`panel: cpd`)

Critics come from different model families. The executor cannot certify its own
work, and a shared blind spot has to survive several architectures rather than
one.

```bash
# Round 1 — every configured critic, in parallel, against the brief.
quorum cpd-run --debate "<debate-id>" \
               --decision "<one line: what is under review>" \
               --brief-file <brief> \
               [--security-brief-file <sec-brief>] \
               --progress --json

# → .quorum/reviews/<debate-id>/round1.json

# Classify the findings from that file, then author ONE rebuttal PER CRITIC
# into <pushback-dir>/<decision_id>.md

# Round 2 — resume each critic's own session with its own rebuttal.
quorum cpd-resume --debate "<debate-id>" \
                  --pushback-dir <dir> --standard --json

# → .quorum/reviews/<debate-id>/round2.json

# Verdict. Exits 2 on an incomplete debate and is never forced.
quorum cpd-conclude --debate "<debate-id>"
```

**A non-zero exit from `cpd-conclude` is the verdict.** Do not work around it,
do not summarise the rounds by hand, do not record a verdict it declined to
render. An incomplete debate producing no verdict is the feature.

**One rebuttal per critic.** Never a merged one: a single rebuttal answered by
everybody collapses the independent signal that having several families bought.

## Path B — same-provider (`panel: single-provider`)

The cross-provider engine is absent. Run the panel with subagents instead, and
be exact about what is lost.

**What is lost.** Every critic is the same model. Cross-family diversity is
gone, and with it the main defence against a shared blind spot. Subagent
sessions also do not resume: the round-2 critic re-reads the finding and the
rebuttal rather than remembering having written the finding, so it is answering
an argument rather than defending its own.

**What survives, and is still worth running.** Independent contexts — no critic
sees another's reasoning. Distinct lenses, so disagreement comes from where
they are looking rather than from sampling noise. A mandatory rebuttal round. A
verdict that refuses to render when any critic's round-2 is missing.

### Lenses

The lenses are what make the fallback more than the same question asked three
times. Give each critic **one** and do not let it wander.

| Gate | Lens | Asks |
|---|---|---|
| scope | traceability | does every acceptance criterion have a task, and every task a criterion? |
| scope | constitution | does anything here violate an article? cite the article |
| scope | feasibility | what is missing that would block implementation? |
| impl | satisfaction | does the diff do what the approved scope said, no more |
| impl | integrity | data and security rules from `governance/rules/` against the actual diff |
| impl | test adequacy | do the tests fail if the change is reverted? |

`--lenses` overrides the set. Fewer than two is not a panel; say so and refuse.

### Critic containment

Every critic subagent is **read-only** — `tools: Read, Glob, Grep`. This is not
caution, it is convergence: a critic with write or bash drifts into
investigating rather than judging. It reads one more file, runs one more check,
and the round never ends.

Everything a critic needs is in its brief. If something genuinely is not, that
absence is itself a finding.

### Round 2

For each critic that produced findings, author a rebuttal naming what is wrong
with the finding and dispatch a fresh critic with: the original brief, that
critic's finding, and the rebuttal. Ask it to hold, withdraw, or revise.

A critic with no findings still gets round 2 — the standard re-verify — because
"found nothing" that is never re-asked is indistinguishable from "did not look".

## Anti-bias, both paths

- **The brief carries the decision and the neutral predicates. Never the
  author's rationale or preferred conclusion.** A critic told what the author
  hopes will find reasons for it.
- **Classify round-1 findings before authoring any rebuttal.** Editing the
  position in response to a finding, and then rebutting from the edited
  position, launders the change through the debate.
- **`pass` means "found no fatal flaw", not "this is correct".** Surface
  concerns alongside a pass; a pass that swallowed three concerns is a worse
  outcome than a fail.
- **A dispatch failure is inconclusive, not a pass.** Retry once, then
  escalate. Treating a timeout as agreement is the cheapest way to fake a
  clean panel.

## What the panel returns

```yaml
panel: cpd | single-provider
panel_reason: <string or null>       # why it degraded; null under cpd
debate_id: <string>
critics: [<id>, ...]
rounds_complete: true | false        # false ⇒ NO verdict is rendered
findings:
  - critic: <id>
    lens: <string or null>           # null under CPD, where lenses are the panel's own
    severity: critical | high | medium | low
    blocking: true | false
    evidence: "<file:line or artifact ref>"
    constitution_article: <n or null>
    description: "<what is wrong>"
    round2: held | withdrawn | revised    # required for every round-1 finding
```

`rounds_complete: false` is a terminal answer. The caller records that the
panel did not conclude and why — it does not substitute its own judgement for
the panel's absence.

## What this skill must not do

**Do not render a verdict on an incomplete debate.** Under CPD the exit code
enforces it; under the fallback the caller must, and the temptation is larger
precisely because nothing else will stop it.

**Do not merge rebuttals.** One per critic, always.

**Do not let a critic write.** Read-only tools, no exceptions, including "just
to check one thing".

**Do not silently degrade.** A run that fell back to the same-provider panel
says so before it starts and records it in the verdict. In agent mode that
recording is load-bearing: a `single-provider` verdict may iterate but may not
conclude.

**Do not put the author's conclusion in the brief.** It is the one input that
reliably produces agreement.
