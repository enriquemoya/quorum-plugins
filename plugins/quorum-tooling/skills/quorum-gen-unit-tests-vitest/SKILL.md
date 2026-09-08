---
name: quorum-gen-unit-tests-vitest
argument-hint: [base-branch]
description: Generate Vue 3 / Vitest unit tests for changed files
---

# Unit Test Code Generation Command — Vue 3 / Vitest

Generate unit test code (.spec.ts files) by analyzing code changes between the current branch and a base branch (resolved from `profile.git.default_base_branch`; falls back to `develop`, then `main`, then `master`), then write compilable test files directly alongside the source following the client project conventions.

## Post-Review Fast Path
**If this skill was invoked with `--post-review` argument** (i.e., chained from `/quorum-code-review`), the current conversation already contains all git analysis data, file contents, sprint number, base branch, and application info from the code review. In this mode:

- **SKIP** the entire Setup Phase (base branch, sprint number, ApplicationName are already known)
- **SKIP** Step 1 (Jira tickets already extracted from branch name during review)
- **SKIP** Step 2 (all git commands, file reads, and diff data are already in the conversation)
- **DO run** the directory/filename check — look for the review output directory that was just created and check for existing `unittests_*.md` files to set the filename
- Then proceed directly to Test Generation using all the context already available

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

### Step 1: Extract Jira Tickets
Scan branch name and commit messages for ticket numbers matching pattern `PROJ-\d+`. Normalize to `PROJ-XXXXX` format (uppercase prefix, hyphen, digits). Track the primary ticket (from branch name) and any additional tickets from commits.

### Step 2: Git Analysis
1. **Get commits:** `git --no-pager log --pretty=format:'%h %s (%an)' [base_branch]..HEAD`
2. **Get changed files:** `git --no-pager diff --name-only [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'`
3. **Get diff:** `git --no-pager diff [base_branch]..HEAD -- . ':!.claude' ':!code-reviews'` (30s timeout)
4. **Fallback on timeout:** Read individual changed files if diff times out
5. **Read changed files:** Read each changed file in full to understand the complete implementation context, not just the diff
6. **Check for existing code review:** If `review_*.md` files exist in the same output directory, read the most recent one. Use its analysis as additional context for generating more targeted tests.
7. **Check local changes:** `git --no-pager diff --name-only HEAD`

### Step 3: Categorize Changed Files
For each changed `.ts`, `.tsx`, or `.vue` file, determine its type:

| File Type | Pattern | Test Strategy |
|---|---|---|
| Vue Component | `*.vue` | Component test with `mountWithProviders` / `shallowMountWithProviders` |
| Pinia Store | `*Store.ts`, `*store.ts` in `store/` dirs | Store test with `setActivePinia(createPinia())` |
| Composable | `use*.ts` in `hooks/` or `composables/` dirs | Composable test with mock dependencies |
| Utility/Lib | `*.ts` in `lib/` or `utils/` dirs | Pure function test |
| Type/Interface | `*.ts` with only types/interfaces | Skip — not testable |
| Config | `*.config.ts`, `vite.config.ts` | Skip — not testable |

### Step 4: Discover Existing Tests & Conventions
For each changed source file:
1. Check if a co-located `[FileName].spec.ts` already exists
2. If it exists, read it to understand:
   - Existing mock setup and wrapper patterns
   - `describe` block organization used in that file
   - Which functionality already has tests
3. Read the source file to identify:
   - Component props, emits, slots (for `.vue` files)
   - Store state, getters, actions (for stores)
   - Composable return values (for composables)
   - Function signatures and branching logic (for utilities)
4. Check for related test helpers and builders already in use

---

## What Gets Tests
- **New Vue components** → component tests covering rendering, props, events, permissions
- **New/modified composables** → tests for return values and reactive behavior
- **New/modified store actions/getters** → store tests with isolated Pinia
- **New/modified utility functions** → pure function tests with edge cases
- **Modified components** → tests for the changed behavior
- **Skip:** Type-only files, config files, style files, index re-exports, auto-generated code

---

## Convention Reference

The following conventions are **mandatory** when generating test code. Every generated file and method MUST follow these patterns exactly.

### Testing Stack
- **Vitest 2.1.5** — test framework and runner
- **@vue/test-utils 2.4.6** — Vue component testing (via custom helpers)
- **@pinia/testing 1.0.1** — Pinia store testing
- **jsdom** — DOM environment
- **NO Jest** — do not use Jest globals or matchers

### File Location & Naming
Tests are **co-located** with source files:
```
src/
├── lib/
│   ├── formatUserName.ts
│   └── formatUserName.spec.ts       # Co-located test
├── modules/home/store/
│   ├── propertyStore.ts
│   └── propertyStore.spec.ts        # Co-located test
├── components/contacts/
│   ├── Contact.vue
│   └── Contact.spec.ts              # Co-located test
└── core/hooks/
    ├── useHeaderSearch.ts
    └── useHeaderSearch.spec.ts       # Co-located test
```

### Test File Structure
```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mountWithProviders, shallowMountWithProviders } from '@/tests/helpers';
import ComponentName from './ComponentName.vue';

// Module-scope mocks (BEFORE describe blocks)
const mockFunction = vi.fn();

vi.mock('@/core/hooks/usePermissions', () => ({
  usePermissions: () => ({
    canComputed: mockFunction,
  }),
}));

describe('ComponentName', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render correctly', () => {
      const wrapper = createWrapper();
      expect(wrapper.exists()).toBe(true);
    });
  });

  describe('User Interactions', () => {
    it('should emit event on button click', async () => {
      const wrapper = createWrapper();
      await wrapper.find('button').trigger('click');
      expect(wrapper.emitted('submit')).toBeTruthy();
    });
  });
});

// Helper function at bottom of file
function createWrapper(options: Parameters<typeof shallowMountWithProviders>[1] = {}) {
  return shallowMountWithProviders(ComponentName, {
    ...options,
  });
}
```

### Mounting Components

**Use custom helpers** — NOT direct `mount()` / `shallowMount()`:

```typescript
import { mountWithProviders, shallowMountWithProviders } from '@/tests/helpers';

// Shallow mount (preferred for unit tests — stubs child components)
const wrapper = shallowMountWithProviders(Component, {
  props: { id: 20 },
});

// Full mount (when testing child component integration)
const wrapper = mountWithProviders(Component, {
  props: { id: 20 },
  initialState: {
    propertyStore: { selectedProperty: mockProperty },
  },
});

// With Pinia state
const wrapper = mountWithProviders(Component, {
  initialState: {
    propertyStore: { currentProperty: mockProperty },
  },
  stubActions: false,  // Set true to stub Pinia actions
});
```

These helpers automatically provide: Router, Pinia (testing), VueQuery.

### Mocking Patterns

**Module mocking with vi.mock():**
```typescript
// Mock at file scope (hoisted automatically)
const mockCanComputed = vi.fn();

vi.mock('@/core/hooks/usePermissions', () => ({
  usePermissions: () => ({
    canComputed: mockCanComputed,
  }),
}));

// Configure in beforeEach or per-test
beforeEach(() => {
  vi.clearAllMocks();
  mockCanComputed.mockReturnValue(computed(() => true));
});
```

**Storing mock callbacks:**
```typescript
let storedOnSuccess: (() => Promise<void>) | undefined;

vi.mock('@/core/queries/useMutationHandler', () => ({
  useMutationHandler: (_mutation: unknown, options: { onSuccess?: () => Promise<void> }) => {
    storedOnSuccess = options?.onSuccess;
    return {
      mutate: vi.fn(),
      isPending: mockIsPending,
    };
  },
}));

// Later in test
await storedOnSuccess!();
```

### Assertions — Vitest expect()
```typescript
// Equality
expect(value).toBe(expected);             // Strict ===
expect(value).toEqual(expected);           // Deep equality
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeDefined();
expect(value).toBeUndefined();

// Collections
expect(array).toHaveLength(3);
expect(array).toContain(item);

// Component assertions
expect(wrapper.exists()).toBe(true);
expect(wrapper.text()).toContain('Hello');
expect(wrapper.emitted('event')).toBeTruthy();
expect(wrapper.emitted('event')![0]).toEqual(['arg1']);

// Spy assertions
expect(spy).toHaveBeenCalled();
expect(spy).toHaveBeenCalledTimes(2);
expect(spy).toHaveBeenCalledWith('arg1', 'arg2');
expect(spy).not.toHaveBeenCalled();

// Props/attributes
expect(component.props('total')).toBe(600);
expect(element.attributes('disabled')).toBe('');
expect(element.attributes('disabled')).toBeUndefined();
```

### Pinia Store Tests
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useMyStore } from './myStore';

describe('useMyStore', () => {
  let store: ReturnType<typeof useMyStore>;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useMyStore();
  });

  afterEach(() => {
    store.$reset();
  });

  it('should have initial state', () => {
    expect(store.someValue).toBe('initial');
  });

  it('should update state via action', async () => {
    await store.fetchData();
    expect(store.items).toHaveLength(5);
  });
});
```

### Composable Tests
```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

// Module mocks BEFORE dynamic import
const mockRouterPush = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockRouterPush }),
  useRoute: () => ({ params: { id: '1' } }),
}));

describe('useMyComposable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return computed value', async () => {
    const { useMyComposable } = await import('./useMyComposable');
    const result = useMyComposable();
    expect(result.computedValue.value).toBe('expected');
  });
});
```

### Test Data Builders
Use the builder pattern from `@/tests/helpers` for consistent test data:

```typescript
import { BudgetBuilder, ContactBuilder, ChannelBuilder, VendorRequestBuilder } from '@/tests/helpers';

// Budget
const budget = new BudgetBuilder()
  .withAmount(10000)
  .withMonth('January')
  .withYear(2024)
  .build();

// Contact
const contact = new ContactBuilder()
  .withName('Test User')
  .withEmail('test.user@example.com')
  .build();

// Channel
const channel = new ChannelBuilder()
  .withDisplayName('Google Ads')
  .withSelfManaged(true)
  .build();

// Vendor Request (with status helpers)
const request = new VendorRequestBuilder()
  .withId(1)
  .withStatus(RequestStatus.Pending)
  .build();

// Or use shortcut helpers
const contact = createMockContact({ name: 'Jane' });
const contacts = createMockContacts(5);
```

### User Action Helpers
Use helpers from `@/tests/helpers` for DOM interactions:

```typescript
import { fillForm, submitForm, clickElement, elementExists, getElementText } from '@/tests/helpers';

// Fill multiple inputs by data-testid
await fillForm(wrapper, {
  'email-input': 'user@example.com',
  'name-input': 'Test User',
});

// Submit form
await submitForm(wrapper, 'submit-button');

// Click element
await clickElement(wrapper, 'delete-button');

// Check existence
expect(elementExists(wrapper, 'success-message')).toBe(true);

// Get text
expect(getElementText(wrapper, 'total-label')).toBe('$1,000');
```

### Component Event Testing
```typescript
// Emit testing
const wrapper = createWrapper();
const input = wrapper.findComponent({ name: 'MyInput' });

await input.vm.$emit('update:modelValue', 'New Value');

expect(wrapper.emitted('update')).toBeTruthy();
expect(wrapper.emitted('update')![0]).toEqual(['New Value']);

// Multiple emits
const emittedUpdates = wrapper.emitted('budget:update');
expect(emittedUpdates).toHaveLength(3);
expect(emittedUpdates![0][0]).toBe(0);  // First arg of first emit
```

### Reactivity Testing
```typescript
it('should react to permission changes', async () => {
  const hasPermission = ref(true);
  mockSectionDisabled.mockReturnValue(computed(() => !hasPermission.value));

  const wrapper = createWrapper();
  expect(wrapper.find('fieldset').attributes('disabled')).toBeUndefined();

  hasPermission.value = false;
  await wrapper.vm.$nextTick();

  expect(wrapper.find('fieldset').attributes('disabled')).toBe('');
});
```

### Describe Block Organization
Organize tests by feature/concern:
```typescript
describe('ComponentName', () => {
  describe('Rendering', () => { /* ... */ });
  describe('Permissions', () => {
    describe('when user has permission', () => { /* ... */ });
    describe('when user does not have permission', () => { /* ... */ });
  });
  describe('User Interactions', () => { /* ... */ });
  describe('Events', () => { /* ... */ });
  describe('Edge Cases', () => { /* ... */ });
});
```

---

## Test Generation Phase

### Generation Strategy

For each changed source file:

#### 1. Existing Test File Found
- Read the existing file completely
- Identify which new/changed functionality lacks tests
- Generate new `describe`/`it` blocks matching the existing style
- Append new describe blocks before the closing of the outer describe
- Reuse existing `createWrapper()` helper and mock setup
- If new mocks are needed, add them at file scope with the existing mocks

#### 2. No Existing Test File
- Generate a complete new `.spec.ts` file co-located with the source
- Include all necessary imports (vitest, helpers, component/module under test)
- Set up module-scope mocks with `vi.mock()`
- Create a `createWrapper()` helper function (for component tests)
- Generate tests organized by feature in nested `describe` blocks
- Include `beforeEach` with `vi.clearAllMocks()`

#### 3. Test Quality Rules
- Each `it` block tests ONE behavior
- Use `should [expected behavior]` naming for `it` blocks
- Use `createWrapper()` or `shallowMountWithProviders()` — never raw `mount()`
- Mock external dependencies at module scope
- Clear mocks in `beforeEach`
- Reset store state in `afterEach` (for store tests)
- Use builders for test data instead of inline object literals
- Use `data-testid` helpers for DOM queries when available
- Include: happy path, error/edge cases, permission checks (if applicable)
- For components with permissions, test both granted and denied states
- Always `await` DOM interactions and use `$nextTick()` for reactivity

---

## Build & Test Verification

After generating all test files, run them to verify correctness.

### Bash Shell Notes
Claude Code runs in a bash shell on Windows. Run vitest from the correct working directory. For paths with spaces or backslashes, prefix with `MSYS_NO_PATHCONV=1`.

### Running Tests
```bash
cd /c/dev/portal/web_client && npx vitest run [path/to/file.spec.ts] --reporter=verbose
```
- Run ONLY the newly generated test files (not the entire test suite)

### Handling Failures

- If tests fail due to code generation errors (wrong mock setup, missing imports, incorrect assertions), fix the generated test code and re-run
- If tests fail due to legitimate bugs discovered in the source code, note these in the summary as "Potential Source Bugs Found" — do NOT modify the source code
- Iterate up to 3 times on failures before stopping and reporting status
- **Report results** in the summary document with test counts and pass/fail status

---

## Output Phase

### Generated Test Files
Write `.spec.ts` files co-located with source files. Each file must pass vitest and follow all conventions from the Convention Reference above.

### Summary Document
Write `unittests_{n}.md` to the review output directory:

```markdown
# Unit Test Generation Summary - Sprint {sprint}
**Branch:** {branch_name}
**Ticket:** [PROJ-XXXXX](https://your-org.atlassian.net/browse/PROJ-XXXXX)
**Generated:** {date}
**Base Branch:** {base_branch}
**Application:** {ApplicationName}

## Changes Analyzed
{List of source files analyzed with brief description of changes}

## Tests Generated

### New Test Files Created
| File | Test Count | Source File | Type | Notes |
|------|-----------|-------------|------|-------|
| `[path]` | N tests | `[source path]` | Component / Store / Composable / Utility | {context} |

### Tests Added to Existing Files
| File | New Tests | Source File | Notes |
|------|----------|-------------|-------|
| `[path]` | N tests | `[source path]` | {context} |

### Skipped (Not Testable)
- `[path]` — {reason: type-only, config, style, etc.}

## Test Execution Results
| Test File | Tests Run | Passed | Failed | Status |
|---|---|---|---|---|
| `[path]` | N | N | N | PASS / FAIL |

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

## Jira Integration Phase

After writing the summary document to disk:

1. **Get Atlassian cloud ID:** Use `getAccessibleAtlassianResources` MCP tool to retrieve the cloud ID (reuse from earlier if already fetched).
2. **Identify primary ticket:** Use the primary PROJ-XXXXX ticket number extracted from the branch name
3. **Post comment:** Use `addCommentToJiraIssue` MCP tool to post the summary document as a comment on the ticket
4. **Comment format:** Prefix the content with a header: `## Unit Test Generation Summary (Auto-Generated)\nGenerated from branch: {branch_name}\n\n` followed by the full summary document content
5. **No ticket found:** If no PROJ-XXXXX ticket was found in the branch name or commits, skip Jira posting and inform the user: "No Jira ticket found - skipping Jira comment. Unit test summary saved to: {filepath}"
6. **Success message:** After posting, show: "Unit tests generated and summary posted to [PROJ-XXXXX](https://your-org.atlassian.net/browse/PROJ-XXXXX) and saved to: {filepath}"

---

## Key Requirements
- **Passing tests:** Every generated `.spec.ts` file must pass vitest
- **Follow conventions exactly:** Use the Convention Reference above — vitest APIs, custom helpers, builders, co-location
- **Existing test file awareness:** When adding to existing test files, match the style already present in that file
- **Test verification:** Always attempt to run after generation; fix issues iteratively
- **Source code is read-only:** Never modify source code under test — only generate/modify test files
- **Timeout handling:** Use 30s timeouts for git operations, fall back to individual file reads
- **Idempotent Jira posting:** Each run creates a new comment (does not edit previous ones)
