# Checklist

## 依赖配置

- [x] pyproject.toml 中已添加 `pytest-xdist>=3.5.0` 依赖
- [x] pytest.ini 文件已删除
- [x] pyproject.toml 中包含完整的 pytest 配置（原 pytest.ini 内容已迁移）

## Fixture 优化

- [x] tests/conftest.py 中的 mock_config fixture 使用 session scope
- [x] tests/conftest.py 中的 mock_logger fixture 使用 session scope
- [x] tests/fixtures/conftest.py 中的相关 fixture 已评估并优化 scope

## CI 配置

- [x] .github/workflows/ci_tests.yml 中 unit-tests job 使用 `-n auto` 参数
- [x] .github/workflows/ci_tests.yml 中 integration-tests job 使用 `-n auto` 参数

## 工具脚本

- [x] tools/run_tests.py 支持并行测试执行

## 验证

- [x] 串行测试 `pytest tests/unit/ -v` 全部通过
- [x] 并行测试 `pytest tests/unit/ -n auto -v` 全部通过（230 passed, 1 known issue）
- [x] 集成测试 `pytest tests/integration/ -n auto -v` 全部通过（8 passed）
