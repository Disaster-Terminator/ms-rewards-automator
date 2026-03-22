# Requirements: RewardsCore E2E & Smoke Test Suite

**Defined:** 2026-03-21
**Core Value:** Independent, fast, reliable end-to-end testing for login and search flows

---

## v1 Requirements

### E2E-001: Test Infrastructure

- [x] **E2E-001-01**: Provide isolated browser contexts via pytest fixtures
- [x] **E2E-001-02**: Provide reusable page fixtures with auto-cleanup
- [x] **E2E-001-03**: Support configurable headless/headed modes
- [x] **E2E-001-04**: Auto-capture screenshot on test failure with page context
- [x] **E2E-001-05**: Provide test-specific config override mechanism
- [ ] **E2E-001-06**: Support pytest markers for test categorization (smoke, e2e, slow)
- [x] **E2E-001-07**: Ensure 100% browser context and storage cleanup after each test

---

### E2E-002: Smoke Test Suite

- [ ] **E2E-002-01**: Browser launch and basic navigation test (Bing homepage)
- [ ] **E2E-002-02**: Verify Bing search page loads and accepts input
- [ ] **E2E-002-03**: Execute basic search and verify results page (< 10s)
- [ ] **E2E-002-04**: Total smoke suite execution time < 30 seconds
- [ ] **E2E-002-05**: Smoke suite pass rate ≥ 95% on stable environment

---

### E2E-003: Login E2E Tests

- [ ] **E2E-003-01**: Standard email/password login flow completes successfully
- [ ] **E2E-003-02**: Logout flow terminates session and clears cookies
- [ ] **E2E-003-03**: Session recovery using saved storage_state.json works
- [ ] **E2E-003-04**: 2FA/TOTP login flow (when account has 2FA enabled)
- [ ] **E2E-003-05**: Invalid password displays error and does not lock account
- [ ] **E2E-003-06**: Network timeout triggers retry with graceful failure
- [ ] **E2E-003-07**: Login test success rate ≥ 90% across 10 consecutive runs

---

### E2E-004: Search E2E Tests (No-Login Mode)

- [ ] **E2E-004-01**: Access Bing homepage without authentication (public access)
- [ ] **E2E-004-02**: Execute search and verify results container present
- [ ] **E2E-004-03**: Complete 5 consecutive searches with different terms
- [ ] **E2E-004-04**: Search interval timing respects config (3-5s between searches)
- [ ] **E2E-004-05**: Anti-detection behaviors active (random delays, mouse movements)
- [ ] **E2E-004-06**: Search no-login mode pass rate ≥ 85%

---

### E2E-005: Search E2E Tests (With-Login Mode)

- [ ] **E2E-005-01**: Login followed by search sequence (integration)
- [ ] **E2E-005-02**: Points accumulation verified after 5 searches (if account eligible)
- [ ] **E2E-005-03**: Search with valid session cookie (from storage_state)

---

### E2E-006: Task E2E Tests

- [ ] **E2E-006-01**: Task discovery parser finds all available tasks
- [ ] **E2E-006-02**: Completed tasks are correctly filtered out
- [ ] **E2E-006-03**: URL reward task navigates and completes successfully
- [ ] **E2E-006-04**: Quiz task completes all steps and rewards points
- [ ] **E2E-006-05**: Task execution errors handled gracefully (no crash)

---

### E2E-007: CI/CD Integration

- [ ] **E2E-007-01**: GitHub Actions workflow for smoke tests (on PR)
- [ ] **E2E-007-02**: GitHub Actions workflow for full E2E suite (daily)
- [ ] **E2E-007-03**: Pytest HTML report generation on failure
- [ ] **E2E-007-04**: Artifact upload (screenshots, logs, reports) on failure
- [ ] **E2E-007-05**: Matrix testing across Python 3.10-3.13
- [ ] **E2E-007-06**: Scheduled daily runs via cron

---

### E2E-008: Test Data Management

- [ ] **E2E-008-01**: Test account credentials stored in CI secrets (not in repo)
- [ ] **E2E-008-02**: Pre-generated test storage_state.json for fast login
- [ ] **E2E-008-03**: Test account health check (skip tests if account locked)
- [ ] **E2E-008-04**: Isolated test environment detection (avoid prod污染)

---

## v2 Requirements (Future)

- **E2E-009**: Mobile search simulation (viewport + user-agent)
- **E2E-010**: Notification delivery verification
- **E2E-011**: Scheduler-based task execution validation
- **E2E-012**: Performance benchmarking with regression detection
- **E2E-013**: Flaky test automatic retry and quarantine

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Unit tests | Already exist in `tests/unit/`, separate concern |
| Performance/load testing | Requires separate tooling and infrastructure |
| Mobile browser testing | Only desktop Chromium in scope |
| Third-party API mocking | Use existing pytest fixtures for isolation |
| Cross-browser testing | Chromium only, consistent with main app |
| Dashboard API testing | API integration verified via unit tests in `tests/unit/test_dashboard_client.py` |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| E2E-001-01 | Phase 1 | ✅ Completed (01-02) |
| E2E-001-02 | Phase 1 | ✅ Completed (01-02) |
| E2E-001-03 | Phase 1 | ⏳ Pending (01-03) |
| E2E-001-04 | Phase 1 | ✅ Completed (01-02) |
| E2E-001-05 | Phase 1 | ✅ Completed (01-02) |
| E2E-001-06 | Phase 1 | ⏳ Pending (01-03) |
| E2E-001-07 | Phase 1 | ✅ Completed (01-02) |
| E2E-002-01 | Phase 2 | Pending |
| E2E-002-02 | Phase 2 | Pending |
| E2E-002-03 | Phase 2 | Pending |
| E2E-002-04 | Phase 2 | Pending |
| E2E-002-05 | Phase 2 | Pending |
| E2E-003-01 | Phase 3 | Pending |
| E2E-003-02 | Phase 3 | Pending |
| E2E-003-03 | Phase 3 | Pending |
| E2E-003-04 | Phase 3 | Pending |
| E2E-003-05 | Phase 3 | Pending |
| E2E-003-06 | Phase 3 | Pending |
| E2E-003-07 | Phase 3 | Pending |
| E2E-004-01 | Phase 4 | Pending |
| E2E-004-02 | Phase 4 | Pending |
| E2E-004-03 | Phase 4 | Pending |
| E2E-004-04 | Phase 4 | Pending |
| E2E-004-05 | Phase 4 | Pending |
| E2E-004-06 | Phase 4 | Pending |
| E2E-005-01 | Phase 5 | Pending |
| E2E-005-02 | Phase 5 | Pending |
| E2E-005-03 | Phase 5 | Pending |
| E2E-006-01 | Phase 6 | Pending |
| E2E-006-02 | Phase 6 | Pending |
| E2E-006-03 | Phase 6 | Pending |
| E2E-006-04 | Phase 6 | Pending |
| E2E-006-05 | Phase 6 | Pending |
| E2E-007-01 | Phase 6 | Pending |
| E2E-007-02 | Phase 6 | Pending |
| E2E-007-03 | Phase 6 | Pending |
| E2E-007-04 | Phase 6 | Pending |
| E2E-007-05 | Phase 6 | Pending |
| E2E-007-06 | Phase 6 | Pending |
| E2E-008-01 | Phase 1 | Pending |
| E2E-008-02 | Phase 1 | Pending |
| E2E-008-03 | Phase 1 | Pending |
| E2E-008-04 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 34 total (7+5+7+6+3+5+6+4)
- Mapped to phases: 34
- Unmapped: 0 ✓

---

*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after roadmap creation*
