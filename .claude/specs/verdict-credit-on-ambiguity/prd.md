# PRD — an unreadable findings block leaves its verdict counted

## Problem

The severity parser is fail-closed by construction: when it cannot read a
terminal findings block it returns zero severities and never guesses. A panel
reviewing an incident found that this is fail-OPEN in effect, and the argument
is short enough to state completely.

Zero severities means the severity floor does not fire. The floor is what
upgrades an understated token — a `pass` over a blocker becomes `concerns`.
With zero severities there is nothing to upgrade against, so whatever token the
critic wrote stands unexamined. A critic whose evidence was discarded still
casts a full vote.

The incident: a critic wrapped its real terminal block in a code fence. The
verdict parsed, three findings were dropped, and `concerns` was recorded for a
seat whose evidence nobody read.

## The panel's finding, verbatim

> "'Ambiguity yields zero' is fail-open for a blocking gate; normalization
> turns dropped findings into an effective pass." — blocker

> "Records the verdict after silently dropping a fenced terminal block; that is
> fail-open admission, not fail-closed parsing." — major

> "Ambiguity must block verdict credit, not merely annotate a zero-finding
> parse." — round 2, after the annotate-only proposal was put to it

Evidence: `.claude/runs/verdict-credit-on-ambiguity/` carries the round-1 and
round-2 transcripts of debate `fence-parser`, three families, verdict
`escalate`.

## Users

Every gate that acts on a debate verdict, which is every gate that decides
whether work may proceed.

## Value

A seat whose evidence could not be read stops counting as a seat that agreed.

## Success

- A reply whose candidate findings could not be read is distinguishable from
  one that declared none, and the difference reaches the caller that decides.
- Such a seat does not contribute verdict credit to the debate.
- The pinned quoted-example semantics survive: an illustrative block inside a
  fence is still not counted as findings.
- Both failure directions are tested — a dropped real finding, and an inflated
  example.

## Non-goals

- Changing `parse_severity_block`'s window rule. Four resolutions were put to
  the panel and all four were refused; the defect is not in which lines the
  scan collects.
- Making the parser guess. Fail-closed on the parse is correct; what is wrong
  is what the debate does with a fail-closed parse.

## Constitution articles touched

- **Article 3.** This changes a guarantee about how verdicts are counted, so it
  needs assertions in both directions before it is trusted.

## Why this is not being executed now

It changes how a debate counts seats, which is the most load-bearing semantics
in the engine, in a published repository. The cheap half of the remedy shipped
separately: the appended contract now forbids fencing explicitly and names the
consequence, measured to take one panel from 2/3 to 3/3 compliance. That
reduces the incidence; it does not fix the semantics, and the two should not be
confused.
