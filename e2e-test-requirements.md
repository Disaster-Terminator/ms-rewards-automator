# E2E & Smoke Test Suite - 需求文档

## 项目概述

为 RewardsCore 构建高质量、解耦、可独立运行的端到端测试套件，确保核心功能（登录、搜索、任务）的稳定性和可靠性。

**项目类型**：质量保证专项（非功能开发）

---

## 核心目标

1. **独立验证**：测试可单独运行，不依赖完整上下文
2. **真实场景**：基于 Playwright 的真实浏览器测试
3. **快速反馈**：冒烟测试 < 30秒，E2E 测试 < 5分钟
4. **环境友好**：支持真实账户和模拟环境，避免平台封禁风险

---

## 主要特性

### ✅ 解耦设计
- 登录测试和搜索测试**完全独立**，可单独运行
- 搜索测试默认**无痕模式**（不登录）

### ✅ 分层测试
- **冒烟测试**：快速验证（<30s），核心路径
- **E2E 测试**：完整业务流程验证

### ✅ 测试模块
- 登录流程测试（标准、2FA、会话恢复、错误处理）
- 搜索流程测试（无痕+登录双模式）
- 任务执行测试（URL奖励、问答、投票）

---

## 非功能性要求

| 指标 | 目标 |
|------|------|
| 冒烟测试执行时间 | < 30秒 |
| 单个 E2E 场景 | < 5分钟 |
| 登录成功率 | ≥ 90% |
| 搜索成功率 | ≥ 85% |
| 冒烟测试通过率 | ≥ 95% |

---

## 技术约束

- **测试框架**：pytest + pytest-asyncio
- **浏览器自动化**：Playwright（与主代码一致）
- **环境隔离**：每个测试独立浏览器上下文，100% 清理
- **CI/CD**：支持 GitHub Actions，每日自动执行
- **数据管理**：专用测试账户，凭据通过 CI Secrets 管理

---

## 范围

### In Scope
- 冒烟测试套件（5-8个测试）
- 登录 E2E 测试（10-15个测试）
- 搜索 E2E 测试（12-18个测试，含无痕和登录模式）
- 任务 E2E 测试（8-12个测试）
- 测试基础设施（fixtures、报告、CI 集成）

### Out of Scope
- 单元测试（已有）
- 性能压力测试
- 移动端测试
- 第三方 API mock 服务器

---

## 成功标准

✅ 冒烟测试套件 < 30秒，通过率 ≥ 95%
✅ 所有 E2E 测试独立可运行
✅ 搜索测试默认无痕，通过率 ≥ 85%
✅ 登录测试独立，成功率 ≥ 90%
✅ CI 集成完成，每日自动执行
✅ 测试失败自动保存截图和日志

---

## 交付物

```
tests/e2e/
├── conftest.py              # E2E fixtures
├── smoke/                   # 冒烟测试
│   ├── test_browser_launch.py
│   ├── test_basic_navigation.py
│   ├── test_login_smoke.py
│   ├── test_search_smoke.py
│   └── test_api_health.py
├── login/                   # 登录 E2E 测试
│   ├── test_standard_login.py
│   ├── test_2fa_login.py
│   ├── test_session_recovery.py
│   ├── test_login_errors.py
│   └── test_logout.py
├── search/                  # 搜索 E2E 测试
│   ├── test_desktop_search.py      # 无痕
│   ├── test_mobile_search.py       # 移动模拟
│   ├── test_search_with_login.py   # 登录模式
│   ├── test_search_verification.py
│   └── test_search_errors.py
├── tasks/                   # 任务 E2E 测试
│   ├── test_task_discovery.py
│   ├── test_url_rewards.py
│   ├── test_quiz_tasks.py
│   └── test_task_errors.py
└── conftest.py              # 共享 fixtures

.github/workflows/
├── e2e-smoke.yml           # 冒烟测试 CI
└── e2e-full.yml            # 完整 E2E 测试 CI

tests/fixtures/
├── test_accounts.py        # 测试账户管理
├── test_storage_state.json # 预保存会话
└── test_data.py            # 测试数据
```

---

## 路线图（概览）

- **M1 (Week 1)**: 冒烟测试就绪
- **M2 (Week 2)**: 登录 E2E 测试完成
- **M3 (Week 3)**: 搜索 E2E 测试完成
- **M4 (Week 4)**: 任务测试 + CI 集成

---

## 优先级

**P0（立即）**：基础设施 + 冒烟测试
**P1（Week 2）**：登录测试
**P2（Week 3）**：搜索测试（重点）
**P3（Week 4）**：任务测试 + CI

---

**现在开始执行 GSD 流程，生成详细计划和任务分解。**
