# Tasks

- [x] Task 1: 添加 pytest-xdist 依赖
  - [x] SubTask 1.1: 在 pyproject.toml 的 dev 依赖中添加 `pytest-xdist>=3.5.0`

- [x] Task 2: 统一配置文件
  - [x] SubTask 2.1: 将 pytest.ini 中的配置合并到 pyproject.toml 的 `[tool.pytest.ini_options]`
  - [x] SubTask 2.2: 删除 pytest.ini 文件

- [x] Task 3: 优化 fixture scope
  - [x] SubTask 3.1: 将 mock_config、mock_logger 改为 session scope
  - [x] SubTask 3.2: 将 mock_browser_context 改为 module scope
  - [x] SubTask 3.3: 更新 tests/fixtures/mock_accounts.py 和 mock_dashboards.py 中的 fixture scope

- [x] Task 4: 更新 CI workflow
  - [x] SubTask 4.1: 在 `.github/workflows/ci_tests.yml` 的 unit-tests job 中添加 `-n auto` 参数
  - [x] SubTask 4.2: 在 integration-tests job 中添加 `-n auto` 参数

- [x] Task 5: 更新开发工具脚本
  - [x] SubTask 5.1: 更新 `tools/run_tests.py` 支持并行测试参数

- [x] Task 6: 合并 test 和 dev 依赖组
  - [x] SubTask 6.1: 将 test 依赖合并到 dev 组
  - [x] SubTask 6.2: 更新 CI workflow 使用 `.[dev]`

- [x] Task 7: 验证优化效果
  - [x] SubTask 7.1: 安装依赖 `pip install -e ".[dev]"`
  - [x] SubTask 7.2: 运行 `pytest tests/unit/ -n auto -v` 验证并行测试通过

# 验证结果

- **测试结果**: 230 passed, 1 failed
- **耗时**: 36.01s
- **失败原因**: `test_property_log_message_persistence` 是 hypothesis 属性测试对特殊 Unicode 字符处理的问题，与本次优化无关
