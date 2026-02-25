# Pytest 效率优化 Spec

## Why

当前测试套件运行效率低下：367个测试用例串行执行，所有 fixture 为 function scope 导致重复创建，配置文件重复（pyproject.toml + pytest.ini）。在开发迭代和 CI 流程中，测试耗时成为瓶颈。

## What Changes

- 添加 `pytest-xdist` 依赖支持并行测试执行
- 优化 fixture scope（session/module 级别复用）
- 统一配置文件（删除 pytest.ini，整合到 pyproject.toml）
- 更新 CI workflow 使用并行测试
- 添加快速测试模式（开发时跳过慢速测试）

## Impact

- Affected specs: 测试基础设施
- Affected code: 
  - `pyproject.toml` - 依赖和配置
  - `pytest.ini` - 删除
  - `tests/conftest.py` - fixture scope 优化
  - `.github/workflows/ci_tests.yml` - CI 并行测试
  - `tools/run_tests.py` - 支持并行参数

## ADDED Requirements

### Requirement: 并行测试执行

系统 SHALL 支持 pytest-xdist 并行执行测试用例。

#### Scenario: 本地开发并行测试
- **WHEN** 开发者执行 `pytest -n auto`
- **THEN** 测试用例自动分配到所有 CPU 核心并行执行

#### Scenario: CI 并行测试
- **WHEN** CI 流程运行测试
- **THEN** 使用 `-n auto` 参数并行执行，减少总耗时

### Requirement: Fixture Scope 优化

系统 SHALL 对共享 fixture 使用 session/module scope 以减少重复创建开销。

#### Scenario: Session 级别 fixture
- **WHEN** 多个测试使用同一 fixture（如 mock_config）
- **THEN** 该 fixture 在整个测试会话中只创建一次

#### Scenario: Module 级别 fixture
- **WHEN** 同一模块内多个测试使用同一 fixture
- **THEN** 该 fixture 在模块内只创建一次

### Requirement: 快速测试模式

系统 SHALL 提供快速测试模式供开发时使用。

#### Scenario: 开发快速验证
- **WHEN** 开发者执行 `pytest -m "not slow"`
- **THEN** 跳过标记为 slow 的测试，快速验证核心功能

### Requirement: 配置文件统一

系统 SHALL 将所有 pytest 配置整合到 pyproject.toml，删除冗余的 pytest.ini。

#### Scenario: 配置来源唯一
- **WHEN** pytest 读取配置
- **THEN** 仅从 pyproject.toml 的 `[tool.pytest.ini_options]` 读取

## MODIFIED Requirements

### Requirement: CI 测试流程

CI 测试流程 SHALL 使用并行执行以提升效率。

**原配置**:
```yaml
run: pytest tests/unit/ -v --tb=short --timeout=60 -m "not real"
```

**新配置**:
```yaml
run: pytest tests/unit/ -n auto -v --tb=short --timeout=60 -m "not real"
```

## REMOVED Requirements

### Requirement: pytest.ini 配置文件

**Reason**: 与 pyproject.toml 配置重复，增加维护成本
**Migration**: 将 pytest.ini 中的所有配置迁移到 pyproject.toml
