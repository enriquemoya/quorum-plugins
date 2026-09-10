# Tasks — a seat whose evidence could not be read stops voting

- [x] T1: carry the parse state out of `_debate_state` — files: quorum_core/cpd_audit.py — AC: AC1
      The field is persisted on the record and the function drops it:
      `latest_round2` is `dict[str, str]`. Its return shape changes so the
      parse state reaches the decision. Nothing new is computed.

- [x] T2: an unreadable seat forfeits its token, and keeps its seat — files: quorum_core/cpd_audit.py — AC: AC1, AC1b, AC2, AC2b
      Only vote aggregation skips the token. The record keeps it, marked
      forfeited; the seat keeps its place in the panel and in the required-session
      count. Not the incomplete-debate path — that emits no verdict at all and
      undoes never-shrink. Not "downgraded to concerns" either: the seat has no
      opinion that was read, and inventing one is the failure being fixed.

- [x] T2b: the broken implementation the assertion must catch — files: tests/ — AC: AC2b
      A variant that drops the seat and still escalates. It satisfies every
      other criterion here, which is why the panel-size assertion is watched
      failing against it specifically.

- [x] T3: disclose the seats — files: quorum_core/cpd_audit.py — AC: AC3
      Follow `repair_retired_token_free`: an additive key on the verdict, the
      same string surfaced by the console.

- [x] T4: the three failing tests — files: tests/ — AC: AC5
      Against the unfixed tree: a fenced real block whose findings are dropped;
      a `malformed` block, which is a different state; and `none_declared`
      pinned as still voting. Plus the panel-size assertion.

- [x] T4b: the regression pin — files: tests/ — AC: AC4, AC5b
      A fenced ILLUSTRATIVE block must still not count. Watched failing against
      a deliberately over-broad fix, since it cannot fail against the unfixed
      tree.

- [x] T5: the full suite — files: (gate) — AC: AC6
