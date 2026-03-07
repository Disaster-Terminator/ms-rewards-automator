# Project Memory

This file contains persistent memory for the RewardsCore project, loaded into every conversation.

- 

---

## Project-Specific Context

### Conda Environment
- **Project environment:** `rewards-core`
- **Config file:** `environment.yml`
- **Python version:** 3.10

### Common Commands
```bash
# Activate correct environment
conda activate rewards-core

# Verify environment
python -m pytest --version
python --version

# Run tests
python -m pytest tests/unit/ -v
```

---

## Refactoring Progress

### Completed Phases
- **Phase 1:** Dead code removal ✅ (commit 381dc9c, ~1,084 lines saved)
- **Phase 2:** UI & Diagnosis simplification ✅ (commit dafdac0, ~302 lines saved)

### Current Status
- Branch: `refactor/test-cleanup`
- Tests: ✅ 285 unit tests passing
- Total lines saved: ~1,386 net

---

## Key Architecture Notes

### Entry Points
- CLI: `src/cli.py` → uses argparse
- Main app: `src/infrastructure/ms_rewards_app.py` (facade pattern)

### Critical Files
- Config: `config.yaml` (from `config.example.yaml`)
- Environment: `environment.yml` (conda spec)
- Tests: `tests/unit/` (285 tests, use pytest)

### Avoid Modifying
- `src/login/` - Complex state machine, Phase 5 target
- `src/browser/` - Browser automation, Phase 5 target
- `src/infrastructure/container.py` - Unused DI system, Phase 4 target

---

## Development Workflow

1. **Always activate correct conda env first:**
   ```bash
   conda activate rewards-core
   ```

2. **Run tests after changes:**
   ```bash
   python -m pytest tests/unit/ -v -q
   ```

3. **Check code quality:**
   ```bash
   ruff check . && ruff format --check .
   ```

4. **Commit with descriptive messages:**
   - Use conventional commits format
   - Reference phase/task numbers

---

*Last updated: 2026-03-06*
*Memory version: 1.0*