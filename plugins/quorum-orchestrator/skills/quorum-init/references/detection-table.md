# Detection table

The signals `quorum-init` reads, and how much each one is worth. Ordered by how
hard the evidence is: a lockfile is what the build resolves, a folder name is
what someone typed once.

## Tier 1 — the build reads it

These settle a question on their own.

| File | Establishes |
|---|---|
| `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb` | Node, and the exact resolved versions |
| `packages.lock.json`, `*.csproj` `<PackageReference>` | .NET packages and target framework |
| `poetry.lock`, `uv.lock`, `Pipfile.lock` | Python dependencies |
| `go.sum` | Go modules |
| `Cargo.lock` | Rust crates |
| `gradle.lockfile`, `pom.xml` `<dependencies>` | JVM |

## Tier 2 — declared intent

Trustworthy, but a dependency can be declared and unused.

| File | Establishes |
|---|---|
| `package.json` `dependencies` / `devDependencies` | frameworks, test runners, linters |
| `pyproject.toml` `[project.dependencies]` | the same for Python |
| `*.csproj` `<TargetFramework>` | `net9.0` vs `net48` — decides which .NET generator |
| tool configs: `vitest.config.*`, `karma.conf.*`, `jest.config.*`, `cypress.config.*`, `playwright.config.*`, `pytest.ini` | which runner is configured, which is stronger than which is installed |

## Tier 3 — corroborating

Never decides alone. Use to confirm a Tier 1/2 finding, or to raise a question.

| Signal | Suggests |
|---|---|
| CI workflow steps | the commands that actually run in anger — often better than the scripts block |
| `Dockerfile` base image | runtime and version |
| folder names (`src/`, `app/`, `cmd/`, `Controllers/`) | layout conventions |
| `.editorconfig`, `.eslintrc*`, `.ruff.toml` | lint tooling |
| branch names, recent commit subjects | ticket prefix — a hypothesis, never a finding |

## Generated files

`no_hand_edit` is worth extra care: a wrong entry is a nuisance, a missing one
lets an agent overwrite generated code and lose the generator's input.

Look for a "do not edit" header first — most generators write one. Then the
conventional patterns:

| Pattern | Generator |
|---|---|
| `*.Designer.cs`, `*.edmx`, `*.g.cs` | Visual Studio / EF |
| `*.g.ts`, `*.generated.ts`, `**/__generated__/**` | codegen, GraphQL |
| `*_pb2.py`, `*.pb.go` | protobuf |
| `migrations/**` (framework-dependent) | ORM migrations — ask; some are hand-edited |

## Reading a monorepo

Several manifests in one tree is a layout, not a contradiction. Record where
each stack lives — `paths.ui_glob` scoped to the frontend package, commands
prefixed with the workspace runner. When one stack clearly dominates the work,
it is primary; when neither does, ask instead of picking.
