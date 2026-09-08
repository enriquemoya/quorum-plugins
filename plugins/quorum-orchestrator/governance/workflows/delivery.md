# Workflow: DELIVERY

Input: slug. Agent: `quorum-delivery`. Precondition: status VERIFIED-family,
last_audit from impl-audit.

NEVER automatic, in either autonomy mode. Delivery acts outward.

Steps:
1) Verify the verdict and its gate. A `single-provider` panel needs explicit
   human approval to deliver on — it was the last check before the work goes
   out, and it ran degraded.
2) Transition to DELIVERING.
3) PR body via quorum-pr-generator, carrying the accepted_conditions verbatim
   under their own heading. A condition the audit recorded and the PR omits is
   one nobody outside this run will see.
4) QA handoff via quorum-qa-handoff-publisher when roles.qa-handoff is non-null.
5) Ticket link through {{ticket_url}}. Null template renders a bare key; never
   construct a URL from a guessed host.
6) Push, open the PR, update the tracker via roles.tracker.
7) MERGED is written AFTER the merge happens. An open PR is DELIVERING.

The merge click is a human's. A state that runs ahead of reality is worse than
no state — the queue reads it and depends_on is hard.
