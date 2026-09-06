---
name: quorum-gen-unit-tests-jasmine
argument-hint: [base-branch]
description: Generate Jasmine/Karma unit tests (AngularJS, Angular 5+, Vue 2) for changed files
---

# Unit Test Code Generation Command — Jasmine / Karma

Generate unit test code (.spec.js / .spec.ts files) by analyzing code changes between the current branch and a base branch (resolved from `profile.git.default_base_branch`; falls back to `develop`, then `main`, then `master`), then write compilable test files following codebase conventions. This skill covers three framework variants that all share the Jasmine/Karma test runner:

| Variant | Framework | File Extension | Repos |
|---|---|---|---|
| AngularJS | AngularJS 1.x | `.spec.js` | Platform (AdminUI, WebShared, WebMicrosite, WebPlugins) |
| Angular 5+ | Angular 5.2 | `.spec.ts` | Platform (ConsumerTracking) |
| Vue 2 | Vue 2.6 | `.spec.ts` | WebsiteHub |

## Post-Review Fast Path
**If this skill was invoked with `--post-review` argument** (i.e., chained from `/quorum-code-review`), the current conversation already contains all git analysis data, file contents, sprint number, base branch, and application info from the code review. In this mode:

- **SKIP** the entire Setup Phase (base branch, sprint number, ApplicationName are already known)
- **SKIP** Step 1 (Jira tickets already extracted from branch name during review)
- **SKIP** Step 2 (all git commands, file reads, and diff data are already in the conversation)
- **DO run** the directory/filename check — look for the review output directory that was just created and check for existing `unittests_*.md` files to set the filename
- Then proceed directly to Framework Detection and Test Generation using all the context already available

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

### Step 3: Framework Detection
Determine which framework variant applies to each changed file based on its path:

| Path Pattern | Variant | Test Extension |
|---|---|---|
| `Web/AdminUI/` | AngularJS | `.spec.js` |
| `Web/WebShared/` | AngularJS | `.spec.js` |
| `Web/WebMicrosite/` | AngularJS | `.spec.js` |
| `Web/WebPlugins/` | AngularJS | `.spec.js` |
| `ConsumerTracking/src/` | Angular 5+ | `.spec.ts` |
| Any path in WebsiteHub repo | Vue 2 | `.spec.ts` |

If uncertain, check the file extension and nearby test files to confirm the variant.

### Step 4: Discover Existing Tests & Conventions
For each changed source file:
1. Check if a co-located `.spec.js` or `.spec.ts` already exists
2. If it exists, read it to understand:
   - Existing mock and spy setup patterns
   - `describe` block organization
   - Which functionality already has tests
3. Read the source file to identify:
   - Dependencies to inject/mock
   - Public methods/functions/components to test
   - Which are new or changed in the diff

---

## What Gets Tests
- **New controllers/services/components** → full test file with setup, happy path tests
- **Modified controllers/services/components** → tests for the changed behavior
- **New utility functions** → pure function tests
- **Skip:** HTML templates, CSS/SCSS files, config files, vendor libraries, build scripts, type-only files

---

## Convention Reference — Shared Across All Variants

### Assertions — Jasmine Style
```javascript
// Basic expectations
expect(value).toBe(expected);                 // Strict equality
expect(value).toEqual(expected);              // Deep equality
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeDefined();
expect(value).toBeUndefined();
expect(value).toBeNull();
expect(value).toContain(item);                // Array/string contains
expect(value).toMatch(/regex/);               // Regex match
expect(array.length).toBe(n);

// Spy assertions
expect(spy).toHaveBeenCalled();
expect(spy).toHaveBeenCalledTimes(n);
expect(spy).toHaveBeenCalledWith(arg1, arg2);
expect(spy).not.toHaveBeenCalled();

// Object/Array matching
expect(value).toEqual(jasmine.objectContaining({ prop: val }));
expect(value).toEqual(jasmine.arrayContaining([item1, item2]));
expect(value).toEqual(jasmine.anything());

// Error expectations
expect(() => func()).toThrowError();
```

### Mocking & Spying
```javascript
// Spy on object method
spyOn(obj, 'method').and.returnValue(value);
spyOn(obj, 'method').and.callThrough();
spyOn(obj, 'method').and.callFake(function() { return value; });
spyOn(obj, 'method').and.throwError('error');

// Create standalone spy
var spy = jasmine.createSpy('spyName');
spy.and.returnValue(value);

// Create spy object with multiple methods
var mockService = jasmine.createSpyObj('ServiceName', ['method1', 'method2']);
mockService.method1.and.returnValue(value);
```

### Test Structure
```javascript
describe('Component/Service Name', function() {
    // Shared variables
    var dependency1, dependency2;

    beforeEach(function() {
        // Setup for each test
    });

    afterEach(function() {
        // Cleanup
    });

    describe('Feature Group', function() {
        it('should do something specific', function() {
            // Arrange
            var input = 'value';

            // Act
            var result = target.method(input);

            // Assert
            expect(result).toBe('expected');
        });
    });
});
```

### Method Naming
Use `should [expected behavior]` in `it()` blocks:
- `it('should return true when input is valid', function() { ... })`
- `it('should call the API with correct parameters', function() { ... })`
- `it('should throw error when user is not authenticated', function() { ... })`

---

## Convention Reference — AngularJS Variant

### Setup Preamble
```javascript
describe('ControllerName Tests', function () {
    var $rootScope, $scope, $controller, $httpBackend, dataService;

    // Load AngularJS module
    beforeEach(module('AdminUI.moduleName'));

    // Mock providers
    beforeEach(module(function ($provide) {
        $provide.value('staticLookupData', []);
    }));

    // Mock HTTP expectations
    beforeEach(inject(function (_$httpBackend_) {
        $httpBackend = _$httpBackend_;
        $httpBackend.expectGET('i18n/resources-locale_en-US.js').respond([]);
    }));

    // Inject dependencies
    beforeEach(inject(function (_$rootScope_, _$controller_, _dataService_) {
        $rootScope = _$rootScope_;
        $scope = $rootScope.$new();
        $controller = _$controller_;
        dataService = _dataService_;
        spyOn(dataService, 'method').and.returnValue(value);
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should initialize controller', function () {
        var ctrl = $controller('ControllerName', { $scope: $scope });
        expect(ctrl).toBeDefined();
    });
});
```

### Key Patterns
- **Module loading:** `beforeEach(module('AdminUI.moduleName'))` — load AngularJS module
- **Dependency injection:** `inject(function (_serviceName_) { serviceName = _serviceName_; })` — underscore prefix/suffix convention
- **HTTP mocking:** `$httpBackend.expectGET(url).respond(data)`, `$httpBackend.flush()`, `$httpBackend.verifyNoOutstandingExpectation()`
- **Scope testing:** Direct `$scope` manipulation, `$scope.$digest()` for change detection
- **Promise testing:** `$q.defer()` → `deferred.resolve(data)` → `$scope.$digest()`
- **Provider mocking:** `$provide.value('serviceName', mockService)` in `module()` block
- **Test helpers:** `FlatCrudTestHelper` from `/src/common/testhelpers/` for CRUD controller testing

### Run Command
```bash
gulp karma                          # Run all test groups
karma start karma-unit.*.conf.js    # Individual group
```

---

## Convention Reference — Angular 5+ Variant

### Setup Preamble
```typescript
import { TestBed, async, ComponentFixture, ComponentFixtureAutoDetect } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentName } from './component.component';
import { ServiceName } from './service.service';

let component: ComponentName;
let fixture: ComponentFixture<ComponentName>;
let httpMock: HttpTestingController;
let serviceMock: any;

describe('ComponentName Tests', () => {

    beforeEach(async(() => {
        serviceMock = jasmine.createSpyObj('ServiceName', ['method1', 'method2']);
        serviceMock.method1.and.returnValue(Observable.of({}));

        TestBed.configureTestingModule({
            declarations: [ComponentName],
            imports: [HttpClientTestingModule],
            providers: [
                { provide: ServiceName, useValue: serviceMock },
                { provide: ComponentFixtureAutoDetect, useValue: true }
            ]
        });

        fixture = TestBed.createComponent(ComponentName);
        component = fixture.componentInstance;
        httpMock = TestBed.get(HttpTestingController);
    }));

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should call service on init', async(() => {
        component.ngOnInit();
        expect(serviceMock.method1).toHaveBeenCalled();
    }));

    it('should handle HTTP GET', () => {
        component.fetchData();
        const req = httpMock.expectOne('api/endpoint');
        expect(req.request.method).toEqual('GET');
        req.flush({ data: 'mock' });
    });

    afterEach(() => {
        httpMock.verify();
    });
});
```

### Key Patterns
- **TestBed.configureTestingModule():** Set up testing module with declarations, imports, providers
- **HttpClientTestingModule:** For testing HttpClient services
- **HttpTestingController:** Mock HTTP with `.expectOne()`, `.flush()`, `.verify()`
- **async() / fakeAsync():** Handle asynchronous operations
- **fixture.debugElement:** Access rendered DOM elements
- **ComponentFixture:** Provides component instance and testing utilities
- **jasmine.createSpyObj():** Create mock objects with spy methods
- **Observable:** RxJS `Observable.of()` for mock return values

### Run Command
```bash
npm test                                    # Runs karma with webpack
karma start config/karma.config.js          # Direct karma
```

---

## Convention Reference — Vue 2 Variant

### Setup Preamble
```typescript
import { mount, Wrapper, createLocalVue, shallowMount } from '@vue/test-utils';
import Vue from 'vue';
import ComponentName from '@components/path/ComponentName.vue';
import { MockStore, TestHelper } from '@tests';
import MockAdapter from 'axios-mock-adapter';
import axios from 'axios';
import flushPromises from 'flush-promises';

describe('ComponentName Tests', () => {
    let wrapper: Wrapper<Vue> = null;
    let vm: any = null;
    let apiMock: MockAdapter;
    let mockStore: MockStore;

    function buildComponent(): Wrapper<Vue> {
        const localVue = createLocalVue();

        return mount(ComponentName, {
            propsData: {
                prop1: 'value1',
                action: jasmine.createSpy('action')
            },
            provide: {
                theme: TestHelper.getMockHubConfig().theme
            },
            stubs: {
                'child-component': true
            },
            localVue,
        });
    }

    beforeEach(() => {
        apiMock = new MockAdapter(axios);
        mockStore = new MockStore();

        apiMock.onGet('api/endpoint').reply(() => {
            return new Promise((resolve) => {
                resolve([200, { data: 'mock' }]);
            });
        });

        wrapper = buildComponent();
        vm = wrapper.vm as any;
    });

    afterEach(() => {
        wrapper.destroy();
        apiMock.restore();
        mockStore.reset();
    });

    it('renders the component', () => {
        expect(wrapper.isVueInstance()).toBe(true);
        expect(wrapper.isVisible()).toBe(true);
    });

    it('should call action on button click', async () => {
        await wrapper.find('button').trigger('click');
        expect(vm.action).toHaveBeenCalledTimes(1);
    });

    it('should handle async operations', async () => {
        vm.fetchData();
        await flushPromises();
        expect(vm.data).toBeDefined();
    });
});
```

### Key Patterns
- **mount() / shallowMount():** Mount Vue component from `@vue/test-utils` 1.x
- **createLocalVue():** Create isolated Vue instance for component testing
- **wrapper.find() / wrapper.findAll():** Query DOM elements (CSS selectors)
- **wrapper.vm:** Access component instance
- **propsData:** Set component props (Vue 2 convention, not `props`)
- **stubs:** Mock child components (set to `true` for stub, or provide component)
- **provide:** Inject dependencies
- **wrapper.emitted():** Check emitted events
- **wrapper.setProps() / wrapper.setData():** Update component state
- **wrapper.trigger():** Simulate user events
- **wrapper.destroy():** Clean up in afterEach
- **flushPromises:** Wait for all promises to resolve (from `flush-promises` package)
- **MockAdapter:** Mock axios API requests (from `axios-mock-adapter`)
- **MockStore / TestHelper:** Domain-specific test utilities for WebsiteHub
- **jasmine.createSpy():** Create spy functions for callbacks/actions
- **jasmine.clock().withMock():** Handle timers and intervals

### Mock Data Files
WebsiteHub uses `*-fakes.spec.ts` files for shared mock data:
```typescript
// consumer-data-fakes.spec.ts
export let ConsumerFirstSessionFirstPage: IConsumerData = {
    ConsumerId: 1,
    SessionToken: '12345',
    Lead: null,
    CurrentSession: { TotalPageVisits: 1 },
    Overall: { SessionCount: 1, TotalPageVisits: 1 },
    SavedProducts: [],
    CompletedExperiences: [],
    ConversionCount: 0
};

export function resetMockData() {
    ConsumerFirstSessionFirstPage = { /* reset to defaults */ };
}
```

### Run Command
```bash
npm test                    # Run tests once
npm run test:watch          # Watch mode
npm run test:coverage       # With coverage report
```

---

## Test Generation Phase

### Generation Strategy

For each changed source file that was categorized with a framework variant:

#### 1. Existing Test File Found
- Read the existing file completely
- Identify which new/changed methods/components lack tests
- Generate new `describe`/`it` blocks matching the existing style
- Append new blocks before the closing of the outer describe
- Reuse existing mock setup and helper functions

#### 2. No Existing Test File
- Detect the framework variant from the file path
- Generate a complete test file using the appropriate preamble (AngularJS, Angular 5+, or Vue 2)
- Include proper imports, module loading/TestBed/mount setup
- Create mock/spy setup for all dependencies
- Generate `beforeEach`/`afterEach` blocks
- Generate tests for each new/changed public method or component behavior

#### 3. Test Quality Rules
- Each `it` block tests ONE behavior
- AAA pattern (Arrange-Act-Assert) with clear separation
- Mock only direct dependencies, not transitive ones
- Include at least: happy path, null/empty input, error path
- For controllers/components: test initialization, user interactions, API calls
- For services: test method return values, side effects, error handling
- Clean up in `afterEach` (destroy wrapper, verify HTTP, restore mocks)

---

## Build & Test Verification

After generating all test files, run them to verify correctness using the appropriate runner.

### Bash Shell Notes
Claude Code runs in a bash shell on Windows. For commands that reference Windows-style paths, prefix with `MSYS_NO_PATHCONV=1` to prevent path mangling. For npm/gulp commands, run from the correct working directory.

### Test Runners by Framework

**AngularJS (Platform — AdminUI, WebShared, WebMicrosite):**
```bash
cd /c/dev/platform/AdminUI && gulp karma    # or specific karma config
```

**Angular 5+ (ConsumerTracking):**
```bash
cd /c/dev/platform/ConsumerTracking && npm test
```

**Vue 2 (WebsiteHub):**
```bash
cd /c/dev/websitehub && npm test
```

### Handling Failures

- If tests fail due to code generation errors, fix the generated test code and re-run
- If tests fail due to legitimate bugs discovered in the source code, note these in the summary as "Potential Source Bugs Found" — do NOT modify the source code
- Iterate up to 3 times on failures before stopping and reporting status
- **Report results** in the summary document with test counts and pass/fail status

---

## Output Phase

### Generated Test Files
Write `.spec.js` or `.spec.ts` files co-located with source files. Each file must be immediately runnable by the appropriate Karma config.

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
| File | Test Count | Source File | Framework | Notes |
|------|-----------|-------------|-----------|-------|
| `[path]` | N tests | `[source path]` | AngularJS / Angular 5+ / Vue 2 | {context} |

### Tests Added to Existing Files
| File | New Tests | Source File | Notes |
|------|----------|-------------|-------|
| `[path]` | N tests | `[source path]` | {context} |

### Skipped (Not Testable)
- `[path]` — {reason: template, config, style, etc.}

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
- **Runnable tests:** Every generated test file must pass under its framework's Karma config
- **Correct framework variant:** Detect the framework from the file path and use the matching preamble and patterns
- **Follow conventions exactly:** Use the Convention Reference for the detected variant — Jasmine assertions, correct mock/spy patterns, proper module setup
- **Existing test file awareness:** When adding to existing test files, match the style already present
- **Test verification:** Always attempt to run after generation; fix issues iteratively
- **Source code is read-only:** Never modify source code under test — only generate/modify test files
- **Timeout handling:** Use 30s timeouts for git operations, fall back to individual file reads
- **Idempotent Jira posting:** Each run creates a new comment (does not edit previous ones)
