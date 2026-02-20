# 任务文档：搜索次数调整与项目重命名

## 元数据

| 项目 | 值 |
|------|-----|
| 分支名 | `fix/search-count-rename` |
| 任务类型 | fix + chore |
| 优先级 | 高 |
| 预估工作量 | 小 |
| 创建时间 | 2026-02-20 |

---

## 一、背景

### 1.1 搜索次数调整

微软 Rewards 改版后，积分机制变化：
- **改版前**：PC 30次 + 移动 20次 = 150分/天
- **改版后**：统一 20次 = 60分/天（每次+3分）

移动搜索已无必要，改为仅桌面搜索 20 次。

### 1.2 项目重命名

当前名称 `MS-Rewards-Automator` 包含 `MS`（Microsoft 缩写），存在商标风险。

新名称：**RewardsCore**

---

## 二、改动清单

### 2.1 搜索次数调整

| 文件 | 改动内容 | 行数 |
|------|----------|------|
| `src/infrastructure/config_manager.py` | 默认值 30+20 → 20+0，dev 2+2 → 2+0，user 3+3 → 3+0 | 4行 |
| `src/infrastructure/app_config.py` | 默认值 30+20 → 20+0 | 2行 |
| `src/infrastructure/models.py` | 默认值 30+20 → 20+0 | 2行 |
| `src/infrastructure/task_coordinator.py` | mobile_count=0 时跳过移动搜索 | 3行 |
| `config.example.yaml` | 示例配置更新 | 2行 |
| `tests/unit/test_config_manager.py` | 默认值测试更新 | 2行 |
| `tests/unit/test_config_validator.py` | 默认值测试更新 | 2行 |

**总计：约 17 行**

### 2.2 项目重命名

| 文件 | 改动内容 |
|------|----------|
| `pyproject.toml` | name: ms-rewards-automator → rewards-core |
| `environment.yml` | name: ms-rewards-bot → rewards-core |
| `README.md` | 标题和描述 |
| `main.py` | 文档字符串 |
| `config.example.yaml` | 注释 |
| `docs/**/*.md` | 项目名称引用 |
| `.trae/rules/project_rules.md` | 规则文件 |

---

## 三、详细改动

### 3.1 config_manager.py

```python
# 默认配置 (第 36-37 行)
"desktop_count": 20,  # 改为 20
"mobile_count": 0,    # 改为 0

# dev_mode 配置 (第 179-180 行)
"desktop_count": 2,
"mobile_count": 0,    # 改为 0

# user_mode 配置 (第 213-214 行)
"desktop_count": 3,
"mobile_count": 0,    # 改为 0
```

### 3.2 task_coordinator.py

```python
# 在 _execute_mobile_searches 方法开头添加
async def _execute_mobile_searches(self, page, health_monitor=None):
    mobile_count = self.config.get("search.mobile_count", 0)
    
    # 新增：mobile_count=0 时直接返回
    if mobile_count <= 0:
        self.logger.info("移动搜索已禁用 (mobile_count=0)")
        return
    
    # ... 现有逻辑 ...
```

### 3.3 pyproject.toml

```toml
[project]
name = "rewards-core"  # 改名
version = "1.0.0"
description = "Automated daily rewards collection tool"
```

### 3.4 environment.yml

```yaml
name: rewards-core  # 改名
```

---

## 四、测试计划

### 4.1 单元测试

```bash
pytest tests/unit/test_config_manager.py -v
pytest tests/unit/test_config_validator.py -v
```

### 4.2 实战测试

```bash
# 验证 dev 模式（2次桌面搜索）
python main.py --dev

# 验证 user 模式（3次桌面搜索）
python main.py --user
```

### 4.3 验证点

- [ ] 默认配置 desktop_count=20, mobile_count=0
- [ ] dev 模式 desktop_count=2, mobile_count=0
- [ ] user 模式 desktop_count=3, mobile_count=0
- [ ] 移动搜索被跳过，日志显示 "移动搜索已禁用"
- [ ] 项目名称已更新为 RewardsCore

---

## 五、执行步骤

### Step 1：创建分支
```bash
git branch fix/search-count-rename main
git worktree add ../RewardsCore fix/search-count-rename
```

### Step 2：修改搜索次数
- 修改 config_manager.py 默认值
- 修改 app_config.py 默认值
- 修改 models.py 默认值
- 修改 task_coordinator.py 添加跳过逻辑
- 修改 config.example.yaml

### Step 3：修改测试
- 更新 test_config_manager.py
- 更新 test_config_validator.py

### Step 4：重命名项目
- 修改 pyproject.toml
- 修改 environment.yml
- 修改 README.md
- 修改 main.py 文档字符串
- 修改其他文档中的项目名称

### Step 5：测试验证
- 运行单元测试
- 运行 --dev 验证
- 运行 --user 验证

---

## 六、DoD (Definition of Done)

### 第一阶段：代码质量
- [ ] `ruff check .` 通过
- [ ] `ruff format . --check` 通过

### 第二阶段：自动化测试
- [ ] `pytest tests/ -v -m "not slow and not real"` 通过

### 第三阶段：实战测试
- [ ] `python main.py --dev` 无报错
- [ ] 日志显示 "移动搜索已禁用"
- [ ] `python main.py --user` 无报错

### 第四阶段：交付确认
- [ ] 向用户展示改动摘要
- [ ] 等待用户确认"本地审查通过"
