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

## Components — what the tree says about its own parts

A component owns a build, a test suite, or a deployable. These files NAME the
components, which is why they are read before anything is inferred:

| File | Names |
|---|---|
| `pnpm-workspace.yaml`, `package.json` `workspaces` | JS/TS packages |
| `nx.json`, `turbo.json`, `lerna.json` | the same, plus a task graph |
| `*.sln` `Project(...)` entries | .NET projects and their paths |
| `Cargo.toml` `[workspace] members` | Rust crates |
| `go.work` `use` directives | Go modules |
| `settings.gradle*` `include` | Gradle subprojects |
| `pyproject.toml` `[tool.uv.workspace]` / `[tool.poetry.group]` | Python members |

**A workspace declaration is authoritative for its OWN ecosystem, and blind to
every other.** `pnpm-workspace.yaml` names the JS packages; it cannot name the
Python worker beside them, and a repo with `apps/web`, `apps/api` and
`workers/` will declare two of its three components. Take the declaration, then
sweep the rest of the tree for what it could not see.

Whether a declaration exists or not, sweep one level below each source root and
take directories holding a manifest, a test directory, a `Dockerfile`, or an
entry point. When that yields nothing beyond the declared set, say so — a
declaration that turned out to be complete is a finding worth recording, not a
step to skip. When it yields nothing at all, the repository is ONE component: a
valid answer that beats inventing four.

`depends_on` comes from manifests only. An import you read in one file is not a
dependency edge; a partial graph presented as whole is worse than none.

## Entry points

| Signal | Kind |
|---|---|
| `scripts.start` / `scripts.dev` target | whatever it launches |
| `Program.cs`, `main.go`, `cmd/*/main.go`, `__main__.py`, `src/main.*` | process entry |
| route registration, `[ApiController]`, `@Controller`, FastAPI `APIRouter` | http |
| queue/consumer registration, `@Scheduled`, cron yaml | worker / job |
| `index.html`, an app-shell mount | ui |
| a package with only exports and no runner | library |

## Datastores and external services

Read what the process CONNECTS to, never what a README mentions.

| Signal | Establishes |
|---|---|
| `docker-compose*.yml` services | datastores present in development |
| driver/ORM dependencies (`pg`, `Npgsql`, `redis`, `mongoose`, `sqlalchemy`) | the store actually spoken to |
| connection-string KEYS in config/env samples | the store, and nothing else |
| SDK packages (`stripe`, `@aws-sdk/*`, `sendgrid`, `auth0`) | third-party services |

Record the dependency, never the credential: `postgres` not a host, `s3` not a
bucket, `oidc` not a tenant. Discovery frequently runs against someone else's
repository and writes to a committed file.

## Characteristics

| Signal | Characteristic |
|---|---|
| `.github/workflows/*`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile` | `ci` |
| `Dockerfile*`, `docker-compose*.yml` | `containerised` |
| `*.tf`, `*.bicep`, `cdk.json`, `serverless.yml` | `infra_as_code` |
| `openapi.*`, `swagger.*`, `*.graphql`, `*.proto` | `api_contract` |
| `migrations/`, `Migrations/`, `alembic.ini`, `prisma/migrations` | `migrations` |
| locale folders, `i18n` dependency | `i18n` |
| auth middleware, `oidc`/`jwt`/`saml` dependency | `auth` — the MECHANISM only |

Absent is a finding. Write `false` when you looked and found nothing, `null`
when you did not look. Those lead to different next steps, and a report that
renders them alike destroys the distinction.

## Reading a monorepo

Several manifests in one tree is a layout, not a contradiction. Record where
each stack lives — `paths.ui_glob` scoped to the frontend package, commands
prefixed with the workspace runner. When one stack clearly dominates the work,
it is primary; when neither does, ask instead of picking.
