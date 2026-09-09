# AUDIT_PROPOSAL.md — the proposal artifact

Every non-clean verdict, at either gate, emits a proposal at
`.claude/runs/<slug>/iter-NN-proposal.yml`. Silent passes are forbidden.

The proposal is what makes the loop possible: it names the stage the fix
belongs to, so the orchestrator knows where to route rather than guessing or
starting over.

```yaml
slug: <string>
step: scope-audit | impl-audit
iter: <int>                       # the spec-level counter, not a per-gate one
verdict: READY | READY_WITH_CONDITIONS | NEEDS_REVISION
       | SAFE  | SAFE_WITH_CONDITIONS  | NEEDS_FIX
governance_version: <string>      # which rules produced this
panel: cpd | single-provider      # how it was judged
evidence_digest: <string>         # sorted digest of the evidence refs below

findings:
  - id: F-01
    severity: critical | high | medium | low
    blocking: true | false
    evidence: "<file:line or artifact ref>"     # required, always
    constitution_article: <n or null>
    description: "<what is wrong>"
    proposed_fix:
      target_step: triage | prd | spec | architecture | design | tasks | impl
                 | governance          # ← the rule itself is wrong
      change: "<what to change>"

recommended_transition: "<from> -> <to>"
```

## Rules

- **A finding citing a constitution article is always `blocking: true`**, and
  in agent mode it HALTS rather than looping. The constitution is the one thing
  an autonomous run may not decide to work around.
- **A FAIL row in the requirement-traceability table forbids a SAFE or READY
  verdict**, unless a compensating entry exists in `accepted_conditions`.
- **`evidence` is required on every finding.** A finding without it is an
  opinion, and an opinion cannot be re-checked next iteration — which is what
  `evidence_digest` needs in order to detect a loop that is not converging.
- **The proposal never applies its own fix.** The audit judges; the targeted
  stage changes. An auditor that edits what it is judging has stopped being a
  check.
- **`target_step` must be a stage the routing table can reach from here.** A
  proposal that routes backwards past the agent frontier (`prd`) is an
  escalation, not a loop, and requires a human in either mode.
- **`target_step: governance` means the RULE is wrong, not the work.** No stage
  owns a governance rule, so this target routes to a human in both autonomy
  modes and does not loop the current unit. The finding is recorded against the
  unit that surfaced it and the correction becomes its own unit of work.

  This exists because an audit found a defect in the task format it was
  enforcing and had nowhere to put it. Fixing the rule from inside a unit the
  rule governs is the scope creep the containment check forbids, so the choice
  was between recording it with a null target and losing it. Neither is a route.

  A `governance` target never blocks the unit that raised it. That unit is
  judged against the rules in force; the rule changing is a separate decision
  with its own gates.
