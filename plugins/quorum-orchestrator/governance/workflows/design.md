# Workflow: DESIGN

Input: slug. Agent: `quorum-design`. Precondition: status DRAFTING_ARCH.

Steps:
1) Read status.yml — note which stages complexity skipped; a skipped stage is
   not a missing one.
2) Read the upstream artifacts this unit actually has, the constitution, and
   profile.stack for this system's vocabulary.
3) Read the memory bank for decisions and patterns already covering this
   surface. Contradicting a recorded one is a decision, not a detail.
4) Write design.md. Every stack fact resolves from the profile; nothing is assumed.
5) Transition to DRAFTING_DESIGN through `quorum-status`.

Gates: in human mode the artifact is approved before the transition. In agent
mode the transition is recorded and the scope audit is what checks the result.
