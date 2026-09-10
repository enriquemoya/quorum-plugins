---
name: quorum-gen-unit-tests-dotnet4x
argument-hint: [base-branch]
description: Generate .NET Framework 4.7.2 unit tests (NUnit/Moq) for changed files
---

# Unit Test Code Generation Command

Generate unit test code (.cs files) by analyzing code changes between the current branch and a base branch (resolved from `profile.git.default_base_branch`; falls back to `develop`, then `main`, then `master`), then write compilable test files directly into the appropriate test projects following codebase conventions.

## Post-Review Fast Path
**If this skill was invoked with `--post-review` argument** (i.e., chained from `/quorum-code-review`), the current conversation already contains all git analysis data, file contents, sprint number, base branch, and application info from the code review. In this mode:

- **SKIP** the entire Setup Phase (base branch, sprint number, ApplicationName are already known)
- **SKIP** Step 1 (ticket keys already extracted from the branch name during review)
- **SKIP** Step 2 (all git commands, file reads, and diff data are already in the conversation)
- **DO run** the directory/filename check — look for the review output directory that was just created and check for existing `unittests_*.md` files to set the filename
- Then proceed directly to Source-to-Test Project Mapping and Test Generation using all the context already available

This eliminates redundant git operations, file reads, and user prompts, making the chained flow significantly faster.

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
For each changed `.cs` file, determine the corresponding test project using this mapping table:

| Source Path Pattern | Test Project Path | Test Namespace Root |
|---|---|---|
| `src/Core/the project.Core/` | `src/Core/Tests/` | `Tests.Unit.the project.Core` |
| `src/Business/Contoso.Business/` | `src/Business/Test/Tests.Unit.Contoso.Business/` | `Tests.Unit.Contoso.Business` |
| `src/Business/Contoso.Business.Core/` | `src/Business/Test/Test.Unit.Contoso.Business.Core/` | `Tests.Unit.Contoso.Business.Core` |
| `src/RestApi/the project.RestApi.Core/` | `src/RestApi/Tests.Unit.RestApi/` | `Tests.Unit.the project.RestApi.Core` |
| `src/Services/WorkItems/Contoso.Service.WorkItem/` | `src/Services/WorkItems/Tests/WorkItemsServiceTests/` | `Tests.Unit.Contoso.Service.WorkItem` |
| `src/ReplyAutomation/the project.ReplyAutomation/` | `src/ReplyAutomation/Tests/Tests.Unit.the project.ReplyAutomation/` | `Tests.Unit.the project.ReplyAutomation` |
| `src/Services/Processing/Contoso.Service.Processing/` | `src/Services/Processing/Tests/ProcessingTests/` | `Tests.Unit.Contoso.Service.Processing` |

**Fallback:** If a changed file doesn't match any known mapping, read the `.sln` file and nearby `.csproj` files to discover the test project. If no test project exists, note it in the summary and skip test generation for that file.

### Step 4: Discover Existing Tests & Conventions
For each changed source file:
1. Check if a `[ClassName]Tests.cs` already exists in the test project
2. If it exists, read it to understand:
   - Existing mocks and setup patterns
   - Method naming style used in that file
   - Which methods already have tests
   - The `Arrange()` method and how the target is constructed
3. Read the source class to identify:
   - Constructor dependencies (these become `Mock<T>` fields)
   - Public methods that need tests
   - Which methods are new or changed in the diff
4. Read the test project's `.csproj` to verify project references

---

## What Gets Tests
- **New public methods** added in the diff → full test coverage (happy path + key edge cases)
- **Modified public methods** → tests for the changed behavior
- **New classes** → new test file with setup, happy path tests for each public method
- **Protected methods** → test if there is no other way to achieve coverage through public API. When testing protected methods, verify `[assembly: InternalsVisibleTo("TestProjectAssemblyName")]` exists in the source project's `AssemblyInfo.cs` or a `Properties/AssemblyInfo.cs` file. If missing, add it.
- **Skip:** Private methods, auto-generated code, trivial property changes, configuration files, SQL migrations, `.cshtml`/`.js`/`.css` files

---

## Convention Reference

The following conventions are **mandatory** when generating test code. Every generated file and method MUST follow these patterns exactly.

### Testing Stack
- **NUnit 3.12.0** — test framework
- **Moq 4.18.1** — mocking framework
- **Target framework:** .NET Framework 4.7.2
- **NO FluentAssertions** — they are not in the project
- **IMPORTANT — NO `dotnet` CLI:** This is a .NET Framework 4.7.2 project, NOT .NET Core/.NET 5+. The `dotnet build`, `dotnet test`, and `dotnet restore` commands **will not work**. You MUST use `msbuild` to build and `nunit3-console` to run tests. See Build & Test Verification below.

### File & Class Structure
```csharp
using Moq;
using NUnit.Framework;
using [SourceNamespace];
using Tests.Unit.the project.Fakes;

namespace Tests.Unit.the project.[Area].[SubFolder]
{
    [TestFixture]
    public class [ClassName]Tests  // extend BaseFakeContextTestFixture if context injection needed
    {
        Mock<IDependency1> _dependency1Mock;
        Mock<IDependency2> _dependency2Mock;

        [TearDown]
        public void DoTearDown()
        {
            FakeContextUtil.ResetToDefaults();
        }

        private [ClassName] Arrange(Action additionalSetup = null)
        {
            _dependency1Mock = new Mock<IDependency1>();
            _dependency2Mock = new Mock<IDependency2>();

            additionalSetup?.Invoke();

            return new [ClassName](_dependency1Mock.Object, _dependency2Mock.Object);
        }
    }
}
```

### Arrange Pattern
Every test calls `Arrange()` to create the target. The `Arrange` method:
1. Initializes all mock fields to fresh defaults
2. Invokes an optional `Action` callback so the test can customize mocks or test data **before** the target is constructed
3. Constructs and returns the target

This gives each test full control over setup while keeping defaults DRY:

```csharp
// Simple test — use defaults
[Test]
public void GetById_WithValidId_ReturnsEntity()
{
    var target = Arrange();
    var result = target.GetById(5);
    Assert.IsNotNull(result);
}

// Test that needs custom mock behavior
[Test]
public void Process_WhenServiceReturnsNull_ThrowsException()
{
    var target = Arrange(() =>
    {
        _dependency1Mock.Setup(x => x.GetItem(It.IsAny<int>())).Returns((Item)null);
    });

    Assert.Throws<InvalidOperationException>(() => target.Process(1));
}

// Test that needs custom test data via fields
[Test]
public void Calculate_WithSpecificInput_ReturnsExpected()
{
    var target = Arrange(() =>
    {
        _dependency2Mock.Setup(x => x.GetRate()).Returns(0.15m);
    });

    var result = target.Calculate(100m);
    Assert.AreEqual(15m, result);
}
```

**Key rules:**
- **Prefer `Arrange()` over `[SetUp]`** — the goal is to centralize target construction in one place so that (a) a single test can override a mock for its own scenario without duplicating the `new TargetClass(...)` call, and (b) adding a new constructor dependency only touches `Arrange()`, not every test. A `[SetUp]` that constructs the target locks in mock behavior before any test can change it; a `[SetUp]` that only initializes mocks and leaves construction to each test defeats the DRY benefit. `Arrange(Action additionalSetup = null)` solves both. **`[SetUp]` is acceptable** when no test in the fixture needs per-test mock customization, or when extending a base fixture (e.g. `BaseFakeContextTestFixture`'s `DoSetup`) — pick whichever keeps the fixture clearest
- No `Target` field — the target is returned by `Arrange()` and stored in a local variable
- `Arrange` always runs **before** the target is constructed, so mock customizations take effect
- Pass `() => { }` or omit the parameter when defaults are sufficient

### Method Naming
Use the pattern: `MethodUnderTest_Condition_ExpectedResult`

Examples:
- `PerformWork_WhenConsumerNotFound_ShouldReturnFailedResult`
- `GetById_WithValidId_ReturnsEntity`
- `Process_WhenInputIsNull_ThrowsArgumentNullException`
- `Save_WithDuplicateEntry_ReturnsFalse`

### Assertions — NUnit Classic Style Only
```csharp
Assert.AreEqual(expected, actual);
Assert.IsNotNull(obj);
Assert.IsNull(obj);
Assert.IsTrue(condition);
Assert.IsFalse(condition);
Assert.That(actual, Is.EqualTo(expected));
Assert.That(collection, Has.Count.EqualTo(3));
Assert.Throws<ExceptionType>(() => target.Method());
Assert.ThrowsAsync<ExceptionType>(async () => await target.MethodAsync());
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
mock.Verify(x => x.Method(It.Is<Type>(v => v.Name == "test")), Times.Exactly(2));
```

### Shared Fakes Infrastructure
Use these when the class under test accesses `QUORUMContext.Current` or similar static context:

```csharp
// Repository factory — for classes that use QUORUMContext.Current
FakeContextUtil.SetFakeRepositoryFactory(new FakeRepositoryFactory(repoMock.Object));

// Work item queue — for work queue interactions
FakeContextUtil.SetFakeWorkItemQueue(queue.Object);

// User session — for user session access
FakeContextUtil.SetFakeUserSession(sessionMock.Object);

// System parameters — for system param lookups
FakeContextUtil.SetFakeSystemParameters(paramMock.Object);
```

**Base classes and helpers:**
- `BaseFakeContextTestFixture` — extend for classes needing full context setup (provides pre-configured fakes in `DoSetup`)
- `FakeRepositoryFactory` — wraps `Mock<IRepository>` for context injection
- `MockWorkMessageQueue` — captures enqueued work items; use `DequeueMessage<T>()` to assert
- `RepoMockExtensions` — `mockRepo.SetupRead<T>(list)`, `mockRepo.SetupFindByWithExpression<T>(list)` for quick repo mock setup

### Data-Driven Tests
```csharp
[TestCaseSource(nameof(TestData))]
public void Method_Scenario(Type input, Type expected)
{
    var target = Arrange();
    var result = target.Method(input);
    Assert.AreEqual(expected, result);
}

private static IEnumerable<TestCaseData> TestData()
{
    yield return new TestCaseData(input1, expected1).SetName("descriptive name");
    yield return new TestCaseData(input2, expected2).SetName("another case");
}
```

### Async Tests
```csharp
[Test]
public async Task MethodAsync_Condition_Expected()
{
    // Arrange
    var target = Arrange(() =>
    {
        _serviceMock.Setup(x => x.GetAsync(It.IsAny<int>())).ReturnsAsync(new Entity());
    });

    // Act
    var result = await target.MethodAsync();

    // Assert
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
- Append new methods to the file (before the closing braces of the class)
- Reuse existing mock fields and `Arrange()` method — only add new mock fields if the changed methods need dependencies not yet mocked
- If new mock fields are added, also add their initialization to the existing `Arrange()` method

#### 2. No Existing Test File
- Generate a complete new test file with proper namespace, usings, class structure
- Create mock fields for all constructor dependencies
- Generate `Arrange(Action additionalSetup = null)` method that initializes mocks, calls the callback, and constructs the target
- Generate `DoTearDown()` with `FakeContextUtil.ResetToDefaults()`
- Generate tests for each new/changed public method — each test calls `var target = Arrange(...)`
- **Register in `.csproj`:** Add `<Compile Include="..." />` entry to the test project's `.csproj` file (only for SDK-style projects that don't auto-include, or for old-style projects that list files explicitly — check the `.csproj` format first)

#### 3. Test Quality Rules
- Each test method tests ONE behavior
- Arrange-Act-Assert pattern with clear separation (blank lines between sections)
- Mock only direct dependencies, not transitive ones
- Use `It.IsAny<T>()` for parameters that aren't the focus of the test
- Use specific values when testing conditional logic
- Include at least: happy path, null/empty input, error/exception path
- For methods with branching logic, test each branch

---

## Build & Test Verification

**CRITICAL: Do NOT use `dotnet` CLI commands.** This is .NET Framework 4.7.2 — `dotnet build`, `dotnet test`, and `dotnet restore` will NOT work. You MUST use `msbuild` and `nunit3-console` as described below.

After generating all test files, build and run them to verify correctness.

### Bash Shell Build Commands

Because Claude Code runs in a bash shell on Windows, `msbuild` is not on PATH and paths with spaces require special handling. Use these **exact** command patterns — do NOT use `$()` command substitution or `vswhere`.

**NuGet restore** (if packages are missing):
```bash
nuget restore "C:\dev\platform\ContosoAdmin.sln"
```

**Build the test project:**
```bash
MSYS_NO_PATHCONV=1 "/c/Program Files/Microsoft Visual Studio/2022/Professional/MSBuild/Current/Bin/MSBuild.exe" "C:\dev\platform\[path-to-test-project].csproj" /p:Configuration=Debug /verbosity:minimal
```

**Run tests:**
```bash
MSYS_NO_PATHCONV=1 nunit3-console.exe "C:\dev\platform\src\Tests\bin\[TestAssembly].dll" --where "class == [FullyQualifiedTestClassName]"
```

**Key rules:**
- **Always prefix** msbuild and nunit3-console commands with `MSYS_NO_PATHCONV=1` — this prevents the bash shell from corrupting Windows paths
- **Use the exact MSBuild path shown above** — do NOT use variables, `$()` substitution, or `vswhere` to locate it
- **Always use Windows-style backslash paths** (`C:\dev\platform\...`) in the argument to msbuild and nunit3-console
- **Use the `--where` filter** to run ONLY the newly generated tests (not the entire test suite)

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
- `[path]` — {reason: SQL migration, config, view, etc.}

## .csproj Modifications
| Project File | Changes |
|---|---|
| `[path]` | Added `<Compile Include="..." />` for new test files |

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
- The "Potential Source Bugs Found" section is especially important — if a test reveals what appears to be a bug in the source code, describe it clearly

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
- **Follow conventions exactly:** Use the Convention Reference above — NUnit attributes, Moq patterns, naming conventions, no FluentAssertions
- **Existing test file awareness:** When adding to existing test files, match the style already present in that file
- **Build verification:** Always attempt to build and run after generation; fix issues iteratively
- **Source code is read-only:** Never modify source code under test — only generate/modify test files
- **Timeout handling:** Use 30s timeouts for git operations, fall back to individual file reads
- **Idempotent publishing:** each run creates a new comment; it never edits a previous one
