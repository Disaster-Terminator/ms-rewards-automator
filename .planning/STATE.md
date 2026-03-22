# STATE

**Project:** RewardsCore E2E & Smoke Test Suite
**Milestone:** M1 - Smoke Tests Ready
**Current Phase:** Complete (all 15 phase plans created)
**Branch:** feature/e2e-testing
**Last Updated:** 2026-03-22

---

## Project Reference

**Core Value:**
Independent verification of critical user journeys without requiring full application context or manual setup. Tests must be fast (<30s smoke, <5min E2E), reliable (≥90% pass), self-diagnosing, and environment-friendly.

**Current Focus:**
Establish test infrastructure—pytest-asyncio framework, Playwright fixtures, test data management—so that subsequent test modules can be written with reusable, isolated components.

**Constraints:**
- Browser: Playwright Chromium only
- Isolation: Per-test fresh context with 100% cleanup
- Accounts: CI secrets, dedicated test accounts
- Runtime: Smoke <30s, E2E <5min, flakiness <5%

---

## Current Position

| Attribute | Value |
|-----------|-------|
| **Phase** | 1 (In Progress) |
| **Phase Name** | 基础设施与数据设置 |
| **Plan** | 3 plans defined |
| **Status** | context_gathered |
| **Progress** | 0/3 plans (0%) |
| **Started** | 2026-03-22 |
| **Context Gathered** | 2026-03-22 |
| **Resume File** | `.planning/phases/01-基础设施与数据设置/01-CONTEXT.md` |

**Progress bar:** ░░░░░░░░░░ 0%

---

## Performance Metrics

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| Test framework setup time | < 2 hours | - | - |
| Fixture reliability (pass rate) | 100% | - | - |
| Test context cleanup | 100% | - | - |
| Screenshot on failure | Enabled | - | - |

*Metrics will be populated during execution.*

---

## Accumulated Context

### Key Decisions (so far)

| Decision | Rationale | Status |
|----------|-----------|--------|
| Use pytest-asyncio | Consistent with existing test stack | Decided |
| Separate smoke/e2e directories | Fast feedback vs comprehensive validation | Decided |
| No-login-first for search tests | Reduce account lock risk, improve stability | Decided |
| Per-test browser context | Ensure isolation, no state leakage | Decided |
| Chromium only | Align with main app, reduce complexity | Decided |
| Real browser tests (no mocking) | Validate actual user experience | Decided |

### Open Questions

- Which test accounts to use for CI vs local development? (needs 2 dedicated Microsoft accounts)
- Should tests run with `--headed` locally for debugging? (likely yes, but CI headless)
- How to handle Bing UI changes breaking selectors? (monitoring + alerting)
- Task test data: auto-discover or predefine scenarios? (hybrid approach)

### Known Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bing UI changes | Medium | High | Robust selectors + screenshots + weekly health check |
| Account lockout | Low | High | Dedicated test account, staggered runs |
| Network flakiness | Medium | Medium | Timeouts + retry (≤1) + verbose logs |
| CI secrets errors | Medium | High | Local validation script + docs |
| Playwright drift | Low | Medium | Pin versions, CI cache |

### Dependencies & Blockers

**External:**
- Need 2 dedicated Microsoft Rewards test accounts (email + password + optional 2FA)
- CI secrets setup: `MS_REWARDS_E2E_EMAIL`, `MS_REWARDS_E2E_PASSWORD`, `MS_REWARDS_E2E_TOTP_SECRET`
- GitHub repository with Actions enabled

**Internal:**
- None yet

---

## Session Continuity

### What Just Happened

- Completed planning phase: All 15 phase plan files created across 6 phases
- Roadmap finalized with 15 deliverables covering all 8 v1 requirements (34 total test items)
- All phase plans include: Objective, Tasks with acceptance criteria, Deliverables, Success Criteria, Dependencies, Notes
- Structure validated: Each phase has correct number of plans (3, 2, 3, 3, 2, 2)
- Files written: `.planning/ROADMAP.md`, `.planning/STATE.md`, and all 15 phase plans
- No orphaned requirements; traceability table covers all E2E-001 through E2E-008
- Dashboard API references removed per user directive

### Next Actions (for human or next agent)

1. **Review ROADMAP and phase plans** — Confirm all plans are complete and make sense
2. **If approved**, begin execution: `/gsd:execute-phase 1` starts implementing Phase 1 tasks
3. **Set up test accounts** — Acquire credentials before Phase 3/4/5 implementation
4. **Configure CI secrets** — Prepare GitHub Actions secrets template
5. **Monitor progress** — Phase plans can be executed sequentially or in parallel where dependencies allow

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260322-jsl | 配置 pre-commit，集成 ruff、ruff-format 和 mypy | 2026-03-22 | 074d666 | [260322-jsl-discuss-conda](./quick/260322-jsl-discuss-conda/) |

---

*State last written: 2026-03-22 — Quick task 260322-jsl completed (pre-commit config updated)*

- Phase 1 combines E2E-001 (Infrastructure) and E2E-008 (Test Data)
- Granularity: standard (5–8 expected, we have 6)
- Goal-backward thinking applied: success criteria are observable user/test behaviors
- No orphaned requirements
- Deliverables: 15 plans total across 6 phases (3+2+3+3+2+2)
- Phase 2 is a milestone gate: smoke tests must pass before other test suites developed
- Payload consistency: PUT /api/v1/rewards { "amount": 500 } — fix consistency</hash>

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| E2E-001 | Phase 1 | Pending |
| E2E-002 | Phase 2 | Pending |
| E2E-003 | Phase 3 | Pending |
| E2E-004 | Phase 4 | Pending |
| E2E-005 | Phase 4 | Pending |
| E2E-006 | Phase 5 | Pending |
| E2E-007 | Phase 6 | Pending |
| E2E-008 | Phase 1 | Pending |

**Coverage:** 8/8 (100%) ✓

---

*State last written: 2026-03-22 — Quick task 260322-jsl completed (pre-commit config updated)*
