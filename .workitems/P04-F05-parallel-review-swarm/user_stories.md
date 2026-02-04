# P04-F05: Parallel Review Swarm - User Stories

## Epic Summary

As a development team, we want a multi-agent parallel code review system so that we can get comprehensive feedback from multiple specialized perspectives (security, performance, style) simultaneously, reducing review time and improving code quality.

---

## User Stories

### US-01: Trigger Parallel Review Swarm

**As a** developer,
**I want to** trigger a code review swarm via API,
**So that** I can get comprehensive feedback from multiple reviewers in parallel.

**Acceptance Criteria:**

1. POST `/api/swarm/review` accepts `target_path` parameter specifying code to review
2. Response includes `swarm_id` for tracking and `status` indicating review has started
3. Default reviewers (security, performance, style) are spawned if not specified
4. Optional `reviewer_types` parameter allows selecting specific reviewers
5. Response includes `poll_url` for status checking
6. Request validation rejects invalid paths (outside project root)
7. Rate limiting prevents more than 5 concurrent swarms per tenant

**Test Cases:**

```gherkin
Scenario: Trigger swarm with default reviewers
  Given the API is available
  When I POST to /api/swarm/review with target_path "src/workers/"
  Then I receive 202 Accepted
  And the response contains a swarm_id
  And the response status is "in_progress"
  And the response contains poll_url

Scenario: Trigger swarm with specific reviewers
  Given the API is available
  When I POST to /api/swarm/review with:
    | target_path    | src/workers/            |
    | reviewer_types | ["security", "style"]   |
  Then I receive 202 Accepted
  And exactly 2 reviewers are spawned

Scenario: Reject invalid path
  Given the API is available
  When I POST to /api/swarm/review with target_path "/etc/passwd"
  Then I receive 400 Bad Request
  And the error message indicates invalid path

Scenario: Rate limiting active swarms
  Given 5 swarms are already in progress
  When I POST to /api/swarm/review with target_path "src/"
  Then I receive 429 Too Many Requests
```

---

### US-02: Parallel Reviewer Execution

**As a** system operator,
**I want** reviewer agents to execute truly in parallel,
**So that** total review time is close to single-reviewer time rather than cumulative.

**Acceptance Criteria:**

1. All 3 reviewers start within 500ms of swarm dispatch
2. Reviewers execute independently without blocking each other
3. Each reviewer writes results to Redis upon completion
4. Individual reviewer timeout (300s) does not affect other reviewers
5. Partial results are preserved if one reviewer fails

**Test Cases:**

```gherkin
Scenario: Parallel execution timing
  Given a swarm is triggered with 3 reviewers
  When all reviewers complete successfully
  Then total duration is less than 1.5x the slowest reviewer
  And all 3 reviewers show start times within 500ms of each other

Scenario: Independent failure handling
  Given a swarm is triggered with 3 reviewers
  When the security reviewer times out after 300s
  But performance and style reviewers complete in 60s
  Then the swarm completes with partial results
  And performance and style findings are included
  And security reviewer is marked as "timeout"

Scenario: Result storage on completion
  Given a reviewer completes analysis
  Then the result is stored in Redis at swarm:results:{swarm_id}
  And the progress set is updated
  And a SWARM_REVIEWER_COMPLETE message is published
```

---

### US-03: Security Reviewer Specialization

**As a** security-conscious developer,
**I want** the security reviewer to focus specifically on security concerns,
**So that** I get targeted feedback on vulnerabilities.

**Acceptance Criteria:**

1. Security reviewer checks for authentication issues
2. Security reviewer checks for authorization bypass
3. Security reviewer checks for input validation gaps
4. Security reviewer checks for secrets exposure
5. Security reviewer checks for injection vulnerabilities (SQL, command, etc.)
6. Security reviewer checks for cryptography misuse
7. Findings include specific CVE references where applicable
8. Severity ratings follow CVSS-like scale

**Test Cases:**

```gherkin
Scenario: Detect SQL injection
  Given code containing unparameterized SQL query
  When the security reviewer analyzes the code
  Then a finding is created with category "security/injection"
  And severity is HIGH or CRITICAL
  And recommendation includes parameterized query example

Scenario: Detect exposed secrets
  Given code containing hardcoded API key
  When the security reviewer analyzes the code
  Then a finding is created with category "security/secrets_exposure"
  And the finding does not include the actual secret value

Scenario: Security-specific checklist
  Given a security reviewer is spawned
  Then its checklist includes all security focus areas
  And its system prompt emphasizes security analysis
```

---

### US-04: Performance Reviewer Specialization

**As a** performance-focused developer,
**I want** the performance reviewer to focus on efficiency concerns,
**So that** I can identify bottlenecks and optimization opportunities.

**Acceptance Criteria:**

1. Performance reviewer checks for algorithmic complexity issues (O(n^2) loops, etc.)
2. Performance reviewer checks for memory inefficiencies
3. Performance reviewer checks for N+1 database query patterns
4. Performance reviewer checks for missing caching opportunities
5. Performance reviewer checks for async/await misuse
6. Performance reviewer checks for resource leaks
7. Findings include Big-O analysis where applicable
8. Recommendations include specific optimization techniques

**Test Cases:**

```gherkin
Scenario: Detect N+1 query pattern
  Given code with a loop that queries database per iteration
  When the performance reviewer analyzes the code
  Then a finding is created with category "performance/n+1_query"
  And recommendation suggests batch querying or prefetching

Scenario: Detect algorithmic inefficiency
  Given code with nested loops over same collection
  When the performance reviewer analyzes the code
  Then a finding is created with category "performance/complexity"
  And description includes Big-O analysis

Scenario: Performance-specific checklist
  Given a performance reviewer is spawned
  Then its checklist includes all performance focus areas
  And its system prompt emphasizes efficiency analysis
```

---

### US-05: Style Reviewer Specialization

**As a** team lead maintaining code quality,
**I want** the style reviewer to focus on maintainability,
**So that** code follows team conventions and best practices.

**Acceptance Criteria:**

1. Style reviewer checks naming conventions
2. Style reviewer checks code organization and structure
3. Style reviewer checks documentation completeness
4. Style reviewer checks type hint coverage
5. Style reviewer checks error handling patterns
6. Style reviewer checks test coverage gaps
7. Findings reference project coding standards
8. Recommendations include specific refactoring suggestions

**Test Cases:**

```gherkin
Scenario: Detect missing type hints
  Given a function without type annotations
  When the style reviewer analyzes the code
  Then a finding is created with category "style/type_hints"
  And severity is LOW or INFO
  And recommendation shows proper type annotation

Scenario: Detect inconsistent naming
  Given variables using mixed camelCase and snake_case
  When the style reviewer analyzes the code
  Then a finding is created with category "style/naming"
  And recommendation references PEP 8 conventions

Scenario: Style-specific checklist
  Given a style reviewer is spawned
  Then its checklist includes all style focus areas
  And its system prompt emphasizes maintainability
```

---

### US-06: Result Aggregation

**As a** developer reviewing findings,
**I want** results from all reviewers merged into a unified report,
**So that** I can see all issues in one place without duplicates.

**Acceptance Criteria:**

1. Unified report includes all findings from all reviewers
2. Findings are sorted by severity (Critical > High > Medium > Low > Info)
3. Duplicate findings (same file/line/type) are merged
4. Each finding shows which reviewer(s) identified it
5. Report includes summary statistics (counts by severity, by reviewer, by category)
6. Report includes list of files reviewed
7. Report indicates which reviewers succeeded/failed

**Test Cases:**

```gherkin
Scenario: Merge duplicate findings
  Given security and style reviewers both find missing input validation
  When results are aggregated
  Then one finding appears in the unified report
  And the finding shows both reviewers as sources
  And duplicates_removed count is incremented

Scenario: Sort findings by severity
  Given findings with mixed severities
  When results are aggregated
  Then critical_findings appear first
  And info_findings appear last

Scenario: Generate summary statistics
  Given completed swarm with 10 findings
  When results are aggregated
  Then report.total_findings equals 10
  And findings_by_reviewer shows correct counts
  And findings_by_category shows correct counts
```

---

### US-07: Swarm Status Polling

**As a** developer waiting for review,
**I want to** poll for swarm status,
**So that** I know when results are ready.

**Acceptance Criteria:**

1. GET `/api/swarm/review/{swarm_id}` returns current status
2. Status progresses: pending -> in_progress -> aggregating -> complete
3. Response includes completed reviewer count while in_progress
4. Response includes full unified report when complete
5. Response includes error details if failed
6. Response includes duration_seconds when complete

**Test Cases:**

```gherkin
Scenario: Poll while in progress
  Given a swarm is in progress with 1 of 3 reviewers complete
  When I GET /api/swarm/review/{swarm_id}
  Then status is "in_progress"
  And reviewers_completed is ["performance"]
  And reviewers_pending is ["security", "style"]

Scenario: Poll when complete
  Given a swarm has completed successfully
  When I GET /api/swarm/review/{swarm_id}
  Then status is "complete"
  And unified_report is present
  And duration_seconds shows total time

Scenario: Poll failed swarm
  Given a swarm where all reviewers failed
  When I GET /api/swarm/review/{swarm_id}
  Then status is "failed"
  And error_details shows failure reasons
```

---

### US-08: Redis Result Persistence

**As a** system operator,
**I want** swarm results persisted in Redis,
**So that** results survive restarts and can be retrieved later.

**Acceptance Criteria:**

1. Swarm session stored in Redis hash (swarm:session:{id})
2. Individual results stored in Redis hash (swarm:results:{id})
3. Progress tracked in Redis set (swarm:progress:{id})
4. All keys have TTL of 24 hours
5. Results retrievable across API restarts
6. Atomic operations prevent partial writes

**Test Cases:**

```gherkin
Scenario: Result persistence across restart
  Given a swarm completed before API restart
  When the API restarts
  And I GET /api/swarm/review/{swarm_id}
  Then the unified report is still available

Scenario: TTL expiration
  Given a swarm completed 25 hours ago
  When I GET /api/swarm/review/{swarm_id}
  Then I receive 404 Not Found

Scenario: Atomic result storage
  Given a reviewer completes
  When storing result to Redis
  Then session, results, and progress are updated in single pipeline
```

---

## Definition of Done

- [ ] All user stories implemented and tested
- [ ] Unit test coverage > 80%
- [ ] Integration tests pass
- [ ] API documentation updated (OpenAPI)
- [ ] No security findings in SAST scan
- [ ] Performance: swarm dispatch < 100ms
- [ ] Performance: parallel execution verified
- [ ] Code review completed (by reviewer agent)
