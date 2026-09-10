# `integration-profile.yml` — contract

Place this at the root of the repo (or the workspace root, for a multi-repo
setup). Every field the integration kit reads is defined here.

```yaml
# Which checkouts participate, and what each one holds.
repos:
  service:
    path: ../service            # relative to this file, or absolute
    role: primary               # primary | satellite
  shared:
    path: ../shared-contracts
    role: satellite

paths:
  # Per repo: where per-partner code lives.
  integrations_root:
    service: src/Integrations
    shared: src/Contracts/Integrations
  # The file enumerating partner settings keys.
  settings_registry: src/Config/IntegrationSettings.cs
  # Where schema migrations are added.
  migrations: db/migrations
  # Optional: the factory/lookup that maps a partner id to its implementation.
  partner_lookup: src/Integrations/PartnerLookup.cs

# An existing partner to pattern-match against. REQUIRED.
reference_partner:
  id: northwind
  pipelines: [inbound_ingest, outbound_sync]

# The pipeline families this codebase supports.
pipelines:
  inbound_ingest:
    description: Partner pushes or we poll records in.
    entry_point: "{integrations_root}/{Partner}/Inbound"
  outbound_sync:
    description: We push state out to the partner on a schedule.
    entry_point: "{integrations_root}/{Partner}/Outbound"

test:
  framework: xunit             # xunit | nunit | jest | vitest | pytest | ...
  layout: mirror               # mirror | colocated
  root: tests/Unit

# Optional. Where credentials are READ from. Names only — never values.
credentials:
  style: env                   # env | secret-manager | config-file
  key_pattern: "INTEGRATION_{PARTNER}_{FIELD}"

# Optional. Ticket tracker, for the change-planner skill.
tracker:
  kind: ticket                   # the tracker | github | linear | none
  key_prefix: PROJ
  branch_pattern: "feature/{KEY}-{slug}"
```

## Notes

- **`reference_partner` is required.** The kit refuses to scaffold without one.
- `{Partner}` is substituted with the code identifier from the partner intake;
  `{PARTNER}` with its upper-case form.
- Unknown keys are ignored, so you can carry your own metadata in this file.
- Paths are always repo-relative once inside a `repos` entry.
