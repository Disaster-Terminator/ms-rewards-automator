# 多Agent框架隔离与单Agent工作流重构计划

## 目标

1. 将多agent框架隔离到归档目录
2. 创建单agent工作流，整合dev/test/docs/Master的能力
3. 配置MCP工具（上限40个）

## 一、归档方案

### 目标结构

```
.trae/
├── archive/
│   └── multi-agent/
│       ├── agents/          # dev-agent, test-agent, docs-agent
│       ├── skills/          # 8个skill定义
│       ├── specs/           # 6个spec目录
│       ├── prompts/         # master.md
│       ├── documents/       # 多agent分析文档
│       └── artifacts/       # current_task.md等通信媒介
└── rules/
    └── project_rules.md     # 新建单agent规则
```

### 移动清单

| 源路径                            | 目标路径                                   |
| ------------------------------ | -------------------------------------- |
| `.trae/agents/*`               | `.trae/archive/multi-agent/agents/`    |
| `.trae/skills/*`               | `.trae/archive/multi-agent/skills/`    |
| `.trae/specs/*`                | `.trae/archive/multi-agent/specs/`     |
| `.trae/prompts/master.md`      | `.trae/archive/multi-agent/prompts/`   |
| `.trae/documents/*`            | `.trae/archive/multi-agent/documents/` |
| `.trae/blocked_reason.md`      | `.trae/archive/multi-agent/artifacts/` |
| `.trae/current_task.md`        | `.trae/archive/multi-agent/artifacts/` |
| `.trae/test_report.md`         | `.trae/archive/multi-agent/artifacts/` |
| `.trae/rules/project_rules.md` | `.trae/archive/multi-agent/rules/`     |

***

## 二、单Agent工作流设计

### 核心理念

将多agent的职责整合到单一agent：

* **代码修改** ← dev-agent

* **测试执行** ← test-agent（含Playwright E2E）

* **文档更新** ← docs-agent

* **Git/PR管理** ← Master Agent

* **知识归档** ← Memory MCP

### 工作流程

```
用户请求
    │
    ▼
┌─────────────────────────────────────┐
│           Solo Agent                │
├─────────────────────────────────────┤
│ 1. 理解任务                          │
│ 2. 检索Memory知识库                  │
│ 3. 修改代码                          │
│ 4. 局部验证（ruff/mypy/pytest）      │
│ 5. E2E验收（Playwright）             │
│ 6. 更新文档（如需要）                │
│ 7. Git提交 & 创建PR                  │
│ 8. 处理AI审查                        │
│ 9. 知识归档（Memory MCP）            │
└─────────────────────────────────────┘
    │
    ▼
任务完成
```

***

## 三、MCP工具配置（39/40）

### Memory MCP（9个，全部保留）

| 工具                   | 用途         |
| -------------------- | ---------- |
| read\_graph          | 读取知识图谱     |
| search\_nodes        | 搜索节点       |
| open\_nodes          | 打开节点       |
| create\_entities     | 创建实体（知识归档） |
| create\_relations    | 创建关系       |
| add\_observations    | 添加观察       |
| delete\_entities     | 删除实体       |
| delete\_observations | 删除观察       |
| delete\_relations    | 删除关系       |

### GitHub MCP（14个）

#### 只读工具（9个）

| 工具                           | 用途        |
| ---------------------------- | --------- |
| get\_file\_contents          | 获取文件内容    |
| search\_code                 | 搜索代码      |
| get\_pull\_request           | 获取PR详情    |
| get\_pull\_request\_files    | 获取PR文件列表  |
| get\_pull\_request\_status   | 获取PR CI状态 |
| get\_pull\_request\_comments | 获取PR评论    |
| get\_pull\_request\_reviews  | 获取PR审查    |
| list\_pull\_requests         | 列出PR      |
| list\_commits                | 列出提交      |

#### 写入工具（5个）

| 工具                       | 用途      |
| ------------------------ | ------- |
| create\_or\_update\_file | 创建/更新文件 |
| push\_files              | 推送多文件   |
| create\_branch           | 创建分支    |
| create\_pull\_request    | 创建PR    |
| merge\_pull\_request     | 合并PR    |

### Playwright MCP（16个）

#### 基础导航（6个）

| 工具                     | 用途 |
| ---------------------- | -- |
| playwright\_navigate   | 导航 |
| playwright\_click      | 点击 |
| playwright\_fill       | 填充 |
| playwright\_select     | 选择 |
| playwright\_hover      | 悬停 |
| playwright\_press\_key | 按键 |

#### 页面控制（4个）

| 工具                      | 用途   |
| ----------------------- | ---- |
| playwright\_screenshot  | 截图   |
| playwright\_close       | 关闭页面 |
| playwright\_go\_back    | 后退   |
| playwright\_go\_forward | 前进   |

#### 内容获取（4个）

| 工具                             | 用途     |
| ------------------------------ | ------ |
| playwright\_get\_visible\_text | 获取文本   |
| playwright\_get\_visible\_html | 获取HTML |
| playwright\_console\_logs      | 控制台日志  |
| playwright\_evaluate           | 执行JS   |

#### API测试（2个）

| 工具               | 用途     |
| ---------------- | ------ |
| playwright\_get  | GET请求  |
| playwright\_post | POST请求 |

***

## 四、新建文件内容

### 4.1 project\_rules.md（单Agent版）

````markdown
# 项目规则

## 仓库信息

| 属性 | 值 |
|------|-----|
| owner | `Disaster-Terminator` |
| repo | `RewardsCore` |
| default_branch | `main` |

## 环境安全

- 零污染：禁止在 global/base 环境执行 pip install 或 conda install
- 依赖缺失：停止并报告给用户，禁止自行安装

## 文件操作

- 移动/重命名：使用 Move-Item 命令
- 批量删除：使用 Remove-Item 命令

## 工作流程

### 任务执行序列

1. 理解任务需求
2. 检索 Memory MCP 历史知识
3. 修改代码（如需要）
4. 局部验证（ruff/mypy/pytest）
5. E2E 验收（Playwright，如需要）
6. 更新文档（如需要）
7. Git 提交 & 创建 PR
8. 处理 AI 审查评论
9. 知识归档到 Memory MCP

### 验证阶段

| 阶段 | 命令 | 说明 |
|------|------|------|
| 静态检查 | `ruff check . && ruff format --check .` | 必须通过 |
| 类型检查 | `mypy src/ --strict` | 必须通过 |
| 单元测试 | `pytest tests/unit/ -v` | 必须通过 |
| 集成测试 | `pytest tests/integration/ -v` | 必须通过 |
| E2E验收 | `rscore --dev --headless` | 按需执行 |

### E2E 验收降级策略

```bash
# 步骤1：尝试 rscore
rscore --dev --headless

# 步骤2：失败则降级
python main.py --dev --headless
````

### AI 审查处理

| 类型                            | 处理方式 |
| ----------------------------- | ---- |
| `bug_risk`, `Bug`, `security` | 必须修复 |
| `suggestion`, `performance`   | 自主决断 |

### PR 合并限制

* Sourcery 评论可自动检测 `✅ Addressed`

* Copilot/Qodo 评论需人工在 GitHub 网页标记解决

* **Agent 无法自主合并**，需通知人工确认

### Memory MCP 归档

PR 合并后，将关键知识写入 Memory MCP：

```json
{
  "name": "<规则名称>",
  "entityType": "Rewards_Target_Node",
  "observations": [
    "[DOM_Rule] 选择器：<选择器>",
    "[Anti_Bot] 绕过策略：<策略描述>",
    "update_date: <日期>"
  ]
}
```

## 熔断机制

| 条件         | 动作           |
| ---------- | ------------ |
| 连续 3 次验证失败 | 停止执行，向用户报告   |
| 缺少必要上下文    | 停止执行，向用户请求信息 |
| 依赖缺失       | 停止执行，向用户报告   |

## 禁止事项

* 禁止自行安装依赖

* 禁止猜测 DOM 选择器（需从 Memory 或实际页面获取）

* 禁止保存完整 HTML（仅精简取证）

* 禁止在 E2E 测试后不关闭 Playwright 页面

````

---

## 五、执行命令清单

```powershell
# 1. 创建归档目录
$archivePath = ".trae\archive\multi-agent"
New-Item -ItemType Directory -Force -Path "$archivePath\agents"
New-Item -ItemType Directory -Force -Path "$archivePath\skills"
New-Item -ItemType Directory -Force -Path "$archivePath\specs"
New-Item -ItemType Directory -Force -Path "$archivePath\prompts"
New-Item -ItemType Directory -Force -Path "$archivePath\documents"
New-Item -ItemType Directory -Force -Path "$archivePath\artifacts"
New-Item -ItemType Directory -Force -Path "$archivePath\rules"

# 2. 移动文件
Move-Item -Path ".trae\agents\*" -Destination "$archivePath\agents\" -Force
Move-Item -Path ".trae\skills\*" -Destination "$archivePath\skills\" -Force
Move-Item -Path ".trae\specs\*" -Destination "$archivePath\specs\" -Force
Move-Item -Path ".trae\prompts\master.md" -Destination "$archivePath\prompts\" -Force
Move-Item -Path ".trae\documents\*" -Destination "$archivePath\documents\" -Force
Move-Item -Path ".trae\blocked_reason.md" -Destination "$archivePath\artifacts\" -Force
Move-Item -Path ".trae\current_task.md" -Destination "$archivePath\artifacts\" -Force
Move-Item -Path ".trae\test_report.md" -Destination "$archivePath\artifacts\" -Force
Move-Item -Path ".trae\rules\project_rules.md" -Destination "$archivePath\rules\" -Force

# 3. 删除空目录
Remove-Item -Path ".trae\agents" -Force -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path ".trae\skills" -Force -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path ".trae\specs" -Force -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path ".trae\prompts" -Force -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path ".trae\documents" -Force -Recurse -ErrorAction SilentlyContinue

# 4. 创建新的 project_rules.md（内容见4.1节）
````

***

## 六、最终结构

```
.trae/
├── archive/
│   └── multi-agent/
│       ├── agents/
│       ├── skills/
│       ├── specs/
│       ├── prompts/
│       ├── documents/
│       ├── artifacts/
│       └── rules/
└── rules/
    └── project_rules.md  (单Agent版)
```

***

## 七、文档更新

### 7.1 MCP\_WORKFLOW\.md 更新

更新 `docs/reference/MCP_WORKFLOW.md`，移除多agent相关内容，改为单agent工作流：

**主要变更**：

* 移除"阶段6-7执行者分工"（原Master Agent/test-agent分工）

* 更新为单Agent执行全流程

* 保留7阶段验收流程

* 保留MCP工具矩阵

* 保留AI审查系统

* 保留安全边界

### 7.2 BRANCH\_GUIDE.md 更新

更新 `docs/reference/BRANCH_GUIDE.md`，移除多agent相关引用：

**主要变更**：

* 保留分支结构

* 保留开发工作流

* 保留验收标准

* 更新验收流程描述为单Agent模式

***

## 八、风险评估

| 风险      | 缓解措施              |
| ------- | ----------------- |
| 文件丢失    | 所有文件仅移动，不删除       |
| 工作流不完整  | 从多agent抽象，保留核心能力  |
| MCP工具超限 | 精简至39个，留1个余量      |
| 文档不一致   | 同步更新docs目录下的工作流文档 |

