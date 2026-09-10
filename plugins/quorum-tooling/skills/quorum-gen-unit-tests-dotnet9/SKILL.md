---
name: quorum-gen-unit-tests-dotnet9
argument-hint: [base-branch]
description: Generate .NET 9 unit tests (NUnit 4/Moq/AutoFixture) for changed files
---

# Unit Test Code Generation Command — .NET 9

Generate unit test code (.cs files) by analyzing code changes between the current branch and a base branch (resolved from `profile.git.default_base_branch`; falls back to `develop`, then `main`, then `master`), then write compilable test files directly into the appropriate test projects following the API project conventions.

## Post-Review Fast Path
**If this skill was invoked with `--post-review` argument** (i.e., chained from `/quorum-code-review`), the current conversation already contains all git analysis data, file contents, sprint number, base branch, and application info from the code review. In this mode:

- **SKIP** the entire Setup Phase (base branch, sprint number, ApplicationName are already known)
- **SKIP** Step 1 (ticket keys already extracted from the branch name during review)
- **SKIP** Step 2 (all git commands, file reads, and diff data are already in the conversation)
- **DO run** the directory/filename check — look for the review output directory that was just created and check for existing `unittests_*.md` files to set the filename
- Then proceed directly to Source-to-Test Project Mapping and Test Generation using all the context already available

---

## Setup Phase
1. **Set base branch:** Use the branch given as an argument. Otherwise resolve `profile.git.default_base_branch` from the consumer repo's `profile.yml`; if that is absent, fall back to the first of `develop` / `main` / `master` that exists as a ref. **Do NOT read a compare-branch value out of `quorum-config.json`** — that key is for sprint reviews and points somewhere else.
2. **Display base branch:** Show "🧪 **GENERATING UNIT TESTS AGAINST BASE BRANCH: [base_branch]**"
3. **Get application info:** Read `.claude/quorum-config.json` for ApplicationName
4. **Ask for sprint number:** **ALWAYS prompt user to enter the current sprint number** - do not assume or skip this step. Invoke `/quorum-sprint-number` to calculate the current sprint. Present the calculated sprint number as a suggestion but allow user to override if needed.
5. **Create directory:** `code-reviews/[year]/Sprint[sprint]/[ApplicationName]/[cleaned-branch-name]/`
6. **Check for existing unit test summaries:** Look for `unittests_*.md` files to determine the next number
7. **Set filename:** `unittests_{n}.md` where n increments from existing files (start at 1)

## Analysis Phase

### Step 1: Extract ticket keys

**With `roles.tracker` null, `{{profile.ticket_prefix}}` may be unset too.** Then there is no key to recognise: skip the extraction, say so, and carry on with the branch name as given. A ticket key is an annotation here, not an input — it labels output when one is available, and its absence changes nothing else.
Scan branch name and commit messages for ticket numbers matching pattern `{{profile.ticket_prefix}}-\d+`. Normalize to `{{profile.ticket_prefix}}-NNNNN` format (uppercase prefix, hyphen, digits). Track the primary ticket (from branch name) and any additional tickets from commits.

### Step 2: Git Analysis
1. **Get commits:** `git --no-pager log --pretty=format:'%h %s (%an)' [base_branch]..HEAD`
2. **Get changed files:** `git --no-pager diff --name-only [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'`
3. **Get diff:** `git --no-pager diff [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'` (30s timeout)
4. **Fallback on timeout:** Read individual changed files if diff times out
5. **Read changed files:** Read each changed file in full to understand the complete implementation context, not just the diff
6. **Check for existing code review:** If `review_*.md` files exist in the same output directory, read the most recent one. Use its analysis as additional context for generating more targeted tests.
7. **Check local changes:** `git --no-pager diff --name-only HEAD`

### Step 3: Source-to-Test Project Mapping
For each changed `.cs` file, determine the corresponding test project. Use the solution structure to map source projects to test projects:

| Source Project Pattern | Test Project Pattern | Test Namespace Root |
|---|---|---|
| `Contoso.Portal.Services/` | `Tests.Unit.Contoso.Portal.Services/` | `Tests.Unit.Contoso.Portal.Services` |
| `Contoso.Portal.Api/` | `Tests.Unit.Contoso.Portal.Api/` | `Tests.Unit.Contoso.Portal.Api` |

**Fallback:** If a changed file doesn't match any known mapping, read the `.sln` file and nearby `.csproj` files to discover the test project. If no test project exists, note it in the summary and skip test generation for that file.

### Step 4: Discover Existing Tests & Conventions
For each changed source file:
1. Check if a `[ClassName]Tests.cs` (or `[ClassName]Test.cs`) already exists in the `Tests/` subdirectory
2. Check if a `[ClassName]Fixture.cs` exists in the `Fixtures/` subdirectory
3. If tests exist, read them to understand:
   - Existing mock setup and fixture patterns
   - Method naming style used in that file
   - Which methods already have tests
4. Read the source class to identify:
   - Constructor dependencies (these become `Mock<T>` fields or fixture factory parameters)
   - Public methods that need tests
   - Which methods are new or changed in the diff
5. Read the test project's `.csproj` to verify project references

---

## What Gets Tests
- **New public methods** added in the diff → full test coverage (happy path + key edge cases)
- **Modified public methods** → tests for the changed behavior
- **New classes** → new test file with setup, happy path tests for each public method
- **Protected methods** → test if there is no other way to achieve coverage through public API. When testing protected methods, verify `[assembly: InternalsVisibleTo("TestProjectAssemblyName")]` exists in the source project. For SDK-style projects, check for an `<InternalsVisibleTo Include="TestProjectAssemblyName" />` item in the `.csproj`. If missing, add it.
- **Skip:** Private methods, auto-generated code, trivial property changes, configuration files, SQL migrations, DTOs with no logic

---

## Convention Reference

The following conventions are **mandatory** when generating test code. Every generated file and method MUST follow these patterns exactly.

### Testing Stack
- **NUnit 4.3.2** — test framework (constraint-based assertions ONLY)
- **Moq 4.20.72** — mocking framework
- **AutoFixture 5.0.0** — test data generation
- **Moq.EntityFrameworkCore 9.0.0.1** — `ReturnsDbSet()` for EF Core DbContext mocking
- **Target framework:** .NET 9 (SDK-style csproj, auto-includes files)
- **NO FluentAssertions** — they are not in the project
- **Global usings:** `NUnit.Framework` is globally imported via csproj — do NOT add `using NUnit.Framework;`

### Directory Layout
```
Tests.Unit.Contoso.Portal.Services/
├── Tests/                    # Test classes organized by domain
│   ├── Users/
│   │   └── UserServiceTests.cs
│   ├── Budgets/
│   │   └── BudgetServiceTests.cs
│   └── ...
└── Tests.Unit.Contoso.Portal.Services.csproj
```

### Test File & Class Structure
```csharp
using AutoFixture;
using Moq;
using Moq.EntityFrameworkCore;
using Contoso.Portal.DataAccess;

namespace Tests.Unit.Contoso.Portal.Services.Tests.Users;

[TestFixture]
public class UserServiceTests
{
    private Fixture _fixture;
    private Mock<PortalDbContext> _mockDbContext;
    private Mock<ILogger<UserService>> _mockLogger;

    private UserService Arrange(Action additionalSetup = null)
    {
        _fixture = new Fixture();
        _fixture.Behaviors.OfType<ThrowingRecursionBehavior>().ToList()
            .ForEach(b => _fixture.Behaviors.Remove(b));
        _fixture.Behaviors.Add(new OmitOnRecursionBehavior());

        _mockDbContext = new Mock<PortalDbContext>();
        _mockLogger = new Mock<ILogger<UserService>>();

        additionalSetup?.Invoke();

        return new UserService(_mockDbContext.Object, _mockLogger.Object);
    }

    [Test]
    public async Task GetUserAsync_WithValidId_ReturnsUser()
    {
        // Arrange
        var userId = _fixture.Create<long>();

        var sut = Arrange(() =>
        {
            var users = new List<User>
            {
                _fixture.Build<User>()
                    .With(u => u.Id, userId)
                    .With(u => u.Email, "test@example.com")
                    .Create()
            };

            _mockDbContext.Setup(x => x.Users).ReturnsDbSet(users);
        });

        // Act
        var result = await sut.GetUserAsync(userId, CancellationToken.None);

        // Assert
        Assert.That(result, Is.Not.Null);
        Assert.That(result.Id, Is.EqualTo(userId));
    }

    [Test]
    public async Task GetUserAsync_WithNoMatchingUser_ReturnsNull()
    {
        // Arrange
        var sut = Arrange(() =>
        {
            _mockDbContext.Setup(x => x.Users).ReturnsDbSet(new List<User>());
        });

        // Act
        var result = await sut.GetUserAsync(999L, CancellationToken.None);

        // Assert
        Assert.That(result, Is.Null);
    }
}
```

### Arrange Pattern
Every test calls `Arrange()` to create the system under test. The `Arrange` method:
1. Initializes AutoFixture with the recursion behavior fix
2. Initializes all mock fields to fresh defaults
3. Invokes an optional `Action` callback so the test can customize mocks, DbSets, or test data **before** the target is constructed
4. Constructs and returns the target

This gives each test full control over setup while keeping defaults DRY:

```csharp
// Simple test — use defaults
[Test]
public async Task GetAllAsync_WithDefaults_ReturnsEmptyList()
{
    var sut = Arrange();
    var result = await sut.GetAllAsync(CancellationToken.None);
    Assert.That(result, Is.Empty);
}

// Test with custom mock setup
[Test]
public async Task DeleteAsync_WithNonExistentId_ThrowsNotFoundException()
{
    var sut = Arrange(() =>
    {
        _mockDbContext.Setup(x => x.Users).ReturnsDbSet(new List<User>());
    });

    var ex = Assert.ThrowsAsync<UserNotFoundException>(
        async () => await sut.DeleteAsync(999L, CancellationToken.None));
    Assert.That(ex!.Message, Does.Contain("999"));
}
```

**Key rules:**
- **Prefer `Arrange()` over `[SetUp]`** — the goal is to centralize target construction in one place so that (a) a single test can override a mock or AutoFixture behavior for its own scenario without duplicating the `new TargetClass(...)` call, and (b) adding a new constructor dependency only touches `Arrange()`, not every test. A `[SetUp]` that constructs the target locks in mock behavior before any test can change it; a `[SetUp]` that only initializes mocks and leaves construction to each test defeats the DRY benefit. `Arrange(Action additionalSetup = null)` solves both. **`[SetUp]` is acceptable** when no test in the fixture needs per-test mock customization — pick whichever keeps the fixture clearest
- No separate fixture factory classes — the `Arrange()` method lives in the test class itself
- Each test stores the return value in a local `sut` variable (not a class field)
- Mock fields are class-level so they can be accessed for `.Verify()` calls after the Act step
- `_fixture` is class-level so `_fixture.Create<T>()` / `_fixture.Build<T>()` can be used before and after the `Arrange()` call (it's initialized first inside `Arrange`)
- Pass `() => { }` or omit the parameter when defaults are sufficient

### Method Naming
Use the pattern: `MethodUnderTest_Condition_ExpectedResult`

Examples:
- `GetAllRepsAsync_WithValidManagementId_ReturnsRepsForThatManagementCompany`
- `GetAllRepsAsync_WithNoMatchingReps_ReturnsEmptyList`
- `DeleteUserAsync_WithNonExistentUser_ThrowsUserNotFoundException`
- `AddUser_SetsCorrectManagementCompanyId_PerEnvironment`

### Assertions — NUnit Constraint Model ONLY
**IMPORTANT:** Use `Assert.That()` with constraints. Do NOT use classic `Assert.AreEqual()` style.

```csharp
// Equality
Assert.That(result, Is.EqualTo(expectedValue));
Assert.That(result, Is.Not.EqualTo(otherValue));

// Null checks
Assert.That(result, Is.Not.Null);
Assert.That(result, Is.Null);

// Collection checks
Assert.That(result, Has.Count.EqualTo(3));
Assert.That(result, Is.Empty);
Assert.That(result, Is.EquivalentTo(new[] { 1L, 2L }));
Assert.That(result.All(r => r.Status == Active), Is.True);

// Boolean
Assert.That(condition, Is.True);
Assert.That(condition, Is.False);

// String
Assert.That(exception!.Message, Does.Contain(userId.ToString()));

// Numeric ranges / approximate
Assert.That(user.StatusUpdatedDate, Is.GreaterThan(originalDate));
Assert.That(user.StatusUpdatedDate, Is.EqualTo(DateTime.UtcNow).Within(TimeSpan.FromSeconds(5)));

// Exception testing
var exception = Assert.ThrowsAsync<UserNotFoundException>(
    async () => await sut.DeleteUserAsync(userId, companyId, CancellationToken.None));
Assert.That(exception!.Message, Does.Contain(userId.ToString()));
```

### AutoFixture — Test Data Generation
```csharp
// AutoFixture is initialized inside Arrange() — use _fixture after calling Arrange()

// Simple random value
var id = _fixture.Create<long>();
var email = _fixture.Create<string>();

// Build with specific properties
var user = _fixture.Build<User>()
    .With(u => u.Id, requesterId)
    .With(u => u.Email, "test@example.com")
    .Create();

// Omit a property
var user = _fixture.Build<User>()
    .Without(u => u.UserSecurity)
    .Create();

// Generate multiple
var users = _fixture.Build<User>()
    .With(u => u.ManagementCompanyId, companyId)
    .CreateMany(3)
    .ToList();
```

### Moq.EntityFrameworkCore — DbContext Mocking
```csharp
// Mock a DbSet property
var mockDbContext = new Mock<PortalDbContext>();
var users = new List<User> { /* test data */ };
mockDbContext.Setup(x => x.Users).ReturnsDbSet(users);

// Multiple DbSets
mockDbContext.Setup(x => x.Users).ReturnsDbSet(users);
mockDbContext.Setup(x => x.PropertyReps).ReturnsDbSet(propertyReps);

// SaveChangesAsync
mockDbContext.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
    .Returns(Task.FromResult(1));

// Verify SaveChangesAsync called
mockDbContext.Verify(
    db => db.SaveChangesAsync(It.IsAny<CancellationToken>()),
    Times.Once);
```

### Mocking — Moq Patterns
```csharp
// Setup
var mock = new Mock<IInterface>();
mock.Setup(x => x.Method(It.IsAny<Type>())).Returns(value);
mock.Setup(x => x.Method(It.IsAny<Type>())).ReturnsAsync(value);
mock.Setup(x => x.Method(It.Is<Type>(v => v.Id == 5))).Returns(value);

// Verify
mock.Verify(x => x.Method(It.IsAny<Type>()), Times.Once);
mock.Verify(x => x.Method(It.IsAny<Type>()), Times.Never);

// Verify with specific argument check
mockDbContext.Verify(db => db.Users.Add(It.Is<User>(
    u => u.ManagementCompanyId.Equals(id))), Times.Once);
```

### CancellationToken in Async Tests
```csharp
// Always pass CancellationToken.None in unit tests
var result = await sut.ProcessAsync(input, CancellationToken.None);

// Mock methods that accept CancellationToken
mockClient.Setup(c => c.CreateUserAsync(
    It.IsAny<string>(),
    It.IsAny<string>(),
    It.IsAny<CancellationToken>()))
    .ReturnsAsync(new AdminCreateUserResponse());

// Verify CancellationToken passed
mockDbContext.Verify(
    db => db.SaveChangesAsync(It.IsAny<CancellationToken>()),
    Times.Once);
```

### Shared Test Infrastructure
Use `FakePortalApiConfig` from Tests.Common when a service requires `IPortalApiConfig`:

```csharp
using Tests.Common.Contoso.Portal.Helpers;

// Use inside Arrange() callback — the mock is available as a field
private Mock<IPortalApiConfig> _mockConfig;

private MyService Arrange(Action additionalSetup = null)
{
    // ...other mocks...
    _mockConfig = FakePortalApiConfig.GetFakeConfig();
    additionalSetup?.Invoke();
    return new MyService(_mockDbContext.Object, _mockConfig.Object);
}
```

Use `LogVerificationHelper` to verify logging:
```csharp
using Tests.Common.Contoso.Portal.Helpers;

var mockLogger = new Mock<ILogger<UserService>>();
// ... run test ...
LogVerificationHelper.VerifyLogInformationContains(mockLogger, "Enqueuing", "EmailTemplate");
LogVerificationHelper.VerifyLogWarningContains(mockLogger, "User not found");
```

### Parameterized Tests
```csharp
[TestCase("active", true)]
[TestCase("inactive", false)]
[TestCase("pending", false)]
public void IsActive_WithStatus_ReturnsExpected(string status, bool expected)
{
    var sut = Arrange();
    var result = sut.IsActive(status);
    Assert.That(result, Is.EqualTo(expected));
}
```

---

## Test Generation Phase

### Generation Strategy

For each changed source file that has a test project mapping:

#### 1. Existing Test File Found
- Read the existing file completely
- Identify which new/changed methods lack tests
- Generate new `[Test]` methods matching the existing style in that file
- Append new methods to the file (before the closing brace of the class)
- Reuse existing mock fields and `Arrange()` method — only add new mock fields if the changed methods need dependencies not yet mocked
- If new mock fields are added, also add their initialization to the existing `Arrange()` method

#### 2. No Existing Test File
- Generate a complete new test file in `Tests/[Domain]/[ClassName]Tests.cs`
- Create mock fields for all constructor dependencies
- Generate `Arrange(Action additionalSetup = null)` method that initializes AutoFixture, initializes mocks, calls the callback, and constructs the target
- Generate tests for each new/changed public method — each test calls `var sut = Arrange(...)`
- **No `.csproj` registration needed** — SDK-style projects auto-include
- **No separate fixture factory file** — the `Arrange()` method lives in the test class

#### 3. Test Quality Rules
- Each test method tests ONE behavior
- Arrange-Act-Assert pattern with clear separation (comments + blank lines between sections)
- Mock only direct dependencies, not transitive ones
- Use `_fixture.Build<T>()` for test data — set only the properties relevant to the test
- Use `It.IsAny<T>()` for parameters that aren't the focus of the test
- Use specific values when testing conditional logic
- Include at least: happy path, null/empty input, error/exception path
- For methods with branching logic, test each branch
- Always pass `CancellationToken.None` for async method calls

---

## Build & Test Verification

After generating all test files, build and run them to verify correctness.

### Bash Shell Build Commands

Because Claude Code runs in a bash shell on Windows, paths with spaces or backslashes can cause issues. Always prefix `dotnet` commands with `MSYS_NO_PATHCONV=1` and use Windows-style backslash paths in quotes:

**Step 1 — Build the test project:**
```bash
MSYS_NO_PATHCONV=1 dotnet build "C:\dev\portal\service_api\[path-to-test-project].csproj" --configuration Debug --verbosity minimal
```

**Step 2 — Run tests:**
```bash
MSYS_NO_PATHCONV=1 dotnet test "C:\dev\portal\service_api\[path-to-test-project].csproj" --filter "FullyQualifiedName~[TestClassName]" --no-build
```

**Key rules:**
- **Always prefix** dotnet commands with `MSYS_NO_PATHCONV=1` to prevent bash from corrupting Windows paths
- **Always use Windows-style backslash paths** in quotes for the `.csproj` argument
- Use the `--filter` to run ONLY the newly generated tests (not the entire test suite)

### Handling Failures

- If tests fail due to code generation errors (wrong mock setup, incorrect assertions, missing dependencies), fix the generated test code and re-run
- If tests fail due to legitimate bugs discovered in the source code, note these in the summary as "Potential Source Bugs Found" — do NOT modify the source code
- Iterate up to 3 times on build/test failures before stopping and reporting status
- **Report results** in the summary document with test counts and pass/fail status

---

## Output Phase

### Generated Test Files
Write actual `.cs` files directly into the test project directories. Each file must be immediately compilable and follow all conventions from the Convention Reference above.

### Summary Document
Write `unittests_{n}.md` to the review output directory:

```markdown
# Unit Test Generation Summary - Sprint {sprint}
**Branch:** {branch_name}
**Ticket:** [{{profile.ticket_prefix}}-NNNNN]({{ticket_url}})
**Generated:** {date}
**Base Branch:** {base_branch}
**Application:** {ApplicationName}

## Changes Analyzed
{List of source files analyzed with brief description of changes}

## Tests Generated

### New Test Files Created
| File | Test Count | Source File | Notes |
|------|-----------|-------------|-------|
| `[path]` | N tests | `[source path]` | {context} |

### Tests Added to Existing Files
| File | New Methods | Source File | Notes |
|------|------------|-------------|-------|
| `[path]` | N methods | `[source path]` | {context} |

### Skipped (No Test Project Found)
- `[path]` — {reason}

### Skipped (Not Testable)
- `[path]` — {reason: SQL migration, config, DTO, etc.}

## Test Execution Results
| Test Class | Tests Run | Passed | Failed | Status |
|---|---|---|---|---|
| `[ClassName]Tests` | N | N | N | PASS / FAIL |

### Failures & Fixes
{Details of any test failures encountered and how they were resolved}

### Potential Source Bugs Found
{Any tests that revealed possible bugs in the source code — these were NOT fixed, just reported}

## Next Steps
- [ ] Review generated tests for accuracy and completeness
- [ ] Investigate any potential source bugs listed above
```

**Format rules:**
- Omit any section that has no applicable content

---

## Publishing the summary

After writing the summary document to disk, publish it through
`{{role:tracker}}` if that role is set: the primary ticket key comes from the
branch name, and the summary is posted as a comment prefixed with
`## Unit Test Generation Summary (Auto-Generated)` and the branch it came from.

**With `roles.tracker` null, or no ticket key in the branch, this step is
skipped and the run says so** — the summary is on disk either way, and a
repository with no tracker is a supported configuration rather than a failure.

How the comment reaches the tracker is the tracker skill's business, not this
one's. Generating unit tests does not require a ticket system; publishing a
summary to one is an optional courtesy at the end.

---

## Key Requirements
- **Compilable code:** Every generated `.cs` file must compile against the test project's dependencies
- **Follow conventions exactly:** Use the Convention Reference above — NUnit constraint model, Moq patterns, AutoFixture, fixture factories
- **Existing test file awareness:** When adding to existing test files, match the style already present in that file
- **Build verification:** Always attempt to build and run after generation; fix issues iteratively
- **Source code is read-only:** Never modify source code under test — only generate/modify test files
- **Timeout handling:** Use 30s timeouts for git operations, fall back to individual file reads
- **Idempotent publishing:** each run creates a new comment; it never edits a previous one
