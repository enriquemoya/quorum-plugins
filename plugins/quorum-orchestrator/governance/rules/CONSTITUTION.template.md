# CONSTITUTION.md — the articles this project will not violate

> Scaffolded by `/quorum-init` into `.claude/governance/rules/CONSTITUTION.md`.
> **It ships with no articles.** The articles are this project's, and an
> article nobody wrote is not a constraint anyone agreed to.

## What an article is

An article states something the product or the codebase must never do, in terms
that an auditor can check against a spec or a diff. It is not a preference, a
style guide, or a goal.

The test: **could an auditor point at a file and a line and say "this violates
article N"?** If not, it belongs in the memory bank as a convention, not here.

## Why articles are different from every other rule

A finding that cites an article is **always blocking**, in both audits, in both
autonomy modes. A spec that violates one cannot be READY; a diff that violates
one cannot be SAFE; and an agent-mode run HALTS for a human rather than
attempting a fix.

That weight is the point, and it is also the reason to write few of them. A
constitution with twenty articles is a constitution nobody reads, and an
auditor that fires on every change stops being informative.

## Format

```markdown
## Article 1 — <short name>

<What must never happen, stated so a violation is recognisable.>

**Applies to:** all | spec | ticket
**How an auditor checks it:** <what to look for, concretely>
**Why:** <the consequence that makes this non-negotiable>
```

`Applies to` exists because not every article is meaningful on every path — a
hotfix routed through the ticket path is not shaping the product, and holding
it to product-shaping articles produces noise rather than safety. Default to
`all`; narrow it only with a reason.

## Articles

<!-- Add this project's articles here. Start with the ones you would refuse to
     ship without, not the ones that are easy to write down. -->

*(none yet — `/quorum-init` asks for these)*
