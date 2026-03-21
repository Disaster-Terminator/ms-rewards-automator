# WSL/WSLg 下的认证设置指南

本文档说明在 Windows Subsystem for Linux (WSL/WSLg) 环境下正确配置和使用认证预检的完整步骤。

---

## 1. 为什么需要特别关注 WSL 环境？

**WSL/WSLg 常见的认证问题**：

- Windows 文件系统挂载点（`/mnt/c/`, `/cygdrive/`）与 Playwright 存储状态不兼容
- 会话文件（`storage_state.json`）若存放在 Windows 路径下，会导致认证失败或浏览器行为异常
- 预检系统会快速检测并阻止在 Windows 挂载点上运行，避免长时间阻塞

**快速失败保护**：
预检模块会在 15 秒内检测以下问题：
- 文件不存在
- 文件不可读（权限问题）
- **Windows 挂载路径（WSL 特有）**
- JSON 格式错误
- cookies 字段缺失
- 会话过期（可选）

---

## 2. 路径约定

**务必使用 WSL 本地文件系统**：

```bash
# ✅ 推荐：WSL 本地路径
~/storage_state.json          # 主目录下
./storage_state.json          # 当前目录下
/data/msrewards/state.json    # 任意 WSL 本地位置

# ❌ 禁止：Windows 挂载路径
/mnt/c/Users/YourName/storage_state.json
/mnt/d/Projects/storage_state.json
/cygdrive/c/Users/YourName/storage_state.json
```

**配置示例** (`config.yaml`)：

```yaml
account:
  storage_state_path: "storage_state.json"  # 相对路径（推荐）或 ~/storage_state.json
```

---

## 3. 首次登录步骤

### 3.1 环境准备

```bash
# 1. 确保在 WSL 环境中（非 Windows CMD/PowerShell）
pwd  # 应该显示类似 /home/username 的路径

# 2. 安装依赖（在 WSL 中）
pip install -e ".[dev]"
playwright install chromium

# 3. 验证环境
python tools/check_environment.py
```

### 3.2 首次登录流程

```bash
# 1. 使用有头模式登录（非常重要！首次必须显示浏览器窗口）
rscore --user --headless=false

# 2. 在打开的浏览器中手动登录 Microsoft 账户
#    - 输入邮箱和密码
#    - 完成 2FA（如果有）
#    - 处理 "保持登录" 提示（建议选择"是"）

# 3. 程序会自动保存会话到 storage_state.json
#    默认位置：项目根目录下的 storage_state.json
```

### 3.3 验证会话已保存

```bash
# 检查文件是否存在且大小合理（通常 > 1KB）
ls -lh storage_state.json

# 查看文件内容（确认有 cookies 字段）
cat storage_state.json | grep -i cookies

# 示例输出：
# "cookies": [{ "name": "MSPRequ", "value": "...", ... }]
```

---

## 4. 预检 (Preflight) 使用说明

### 4.1 快速验证认证状态

```bash
# 预检模式 - 仅验证文件状态（不验证会话是否有效）
rscore --preflight --dry-run

# E2E 预检模式 - 同时验证会话有效性（启动轻量级浏览器）
E2E_PREFLIGHT=1 rscore --dry-run

# 或使用环境变量
export E2E_PREFLIGHT=1
rscore --preflight --dry-run
```

### 4.2 预检在 CI/CD 中的集成

**GitHub Actions 示例**：

```yaml
- name: Preflight Auth Check
  run: |
    # 预检必须在项目目录中执行（storage_state.json 需提前配置为 secret）
    echo "检查认证状态文件..."
    E2E_PREFLIGHT=1 python -m src.cli --preflight --dry-run
  env:
    # storage_state_path 通过配置文件中指定为绝对路径
    # 在 CI 中，存储文件需要提前部署到 runners 的本地 FS
```

**重点**：在 CI/CD 中，storage_state.json 必须位于 runners 的本地 Linux 文件系统（如 `/home/runner/work/...`），而非挂载的 Windows 路径。

---

## 5. 常见问题排查

### 5.1 "认证状态文件不存在"

**症状**：
```
[MISSING_FILE] 认证状态文件不存在
  Resolution: 运行 'rscore --user' 完成首次登录，或检查 account.storage_state_path 配置
```

**解决方案**：
```bash
# 1. 确认配置文件中的路径
cat config.yaml | grep storage_state_path

# 2. 如果文件不存在，运行首次登录
rscore --user --headless=false
```

### 5.2 "Windows 挂载路径" 错误

**症状**：
```
[WINDOWS_PATH] storage_state 路径在 Windows 挂载点下（WSL/WSLg 不支持）
  Resolution: 将 storage_state.json 移动到 WSL 本地文件系统（如 ~/storage_state.json），更新配置 account.storage_state_path
```

**原因**：
当前配置的 `storage_state_path` 是 `/mnt/c/...` 或 `/cygdrive/...` 这类 Windows 路径。

**解决方案**：
```bash
# 1. 将 storage_state.json 复制到 WSL 本地位置
cp /mnt/c/Users/YourName/storage_state.json ~/storage_state.json

# 2. 修改 config.yaml
sed -i 's|/mnt/c/.*/storage_state.json|storage_state.json|' config.yaml
# 或手动编辑
vim config.yaml
#  account:
#    storage_state_path: "storage_state.json"

# 3. 验证路径正确
rscore --preflight --dry-run
```

### 5.3 文件权限问题

**症状**：
```
[UNREADABLE_FILE] 认证状态文件不可读（权限不足）
  Resolution: 运行 'chmod 600 {path}' 或检查文件权限
```

**解决方案**：
```bash
# 设置正确的权限（仅用户可读写）
chmod 600 storage_state.json

# 验证文件所有者和权限
ls -l storage_state.json
# 输出示例：-rw------- 1 username username 1234 Jan 01 12:00 storage_state.json
```

### 5.4 预检超时（>15秒）

**症状**：
```
预检超时（>15秒），请在 WSL 本地文件系统上运行
```

**原因**：
- storage_state.json 在慢速网络挂载点上（如远程 SMB）
- 浏览器 smoke test 耗时过长（网络慢）

**解决方案**：
```bash
# 1. 确保 storage_state.json 在 WSL 本地（如 ext4 分区）
# 2. 如果只是文件检查，不用 smoke test：
rscore --preflight --dry-run  # 不设置 E2E_PREFLIGHT，不执行浏览器检查

# 3. 如果需要完整检查，确保网络可达
export E2E_PREFLIGHT=1
rscore --preflight --dry-run
```

---

## 6. E2E 测试快速失败说明

**预检的设计目标**：
- **15 秒内**完成所有检查
- **Fast-fail**：任一 blocker 立即返回，不继续耗时操作
- **明确的退出码**：1-6 对应不同 blocker，便于 CI 脚本识别
- **清晰的错误信息**：每个 blocker 提供具体的修复步骤

**退出码对照表**：

| 退出码 | Blocker 类型 | 含义 |
|--------|--------------|------|
| 1 | MISSING_FILE | 文件不存在 |
| 2 | UNREADABLE_FILE | 权限不足 |
| 3 | WINDOWS_PATH | Windows 挂载路径 |
| 4 | INVALID_JSON | JSON 格式错误 |
| 5 | MISSING_COOKIES | 缺少 cookies 字段 |
| 6 | SESSION_EXPIRED | 会话已过期（仅 E2E 模式） |
| 0 | - | 预检通过 |

---

## 7. 完整工作流示例

### 场景 1：新开发者设置 WSL 环境

```bash
# 1. 克隆仓库到 WSL 本地
cd ~
git clone <repo>
cd RewardsCore

# 2. 创建配置文件
cp config.example.yaml config.yaml

# 3. 首次登录（必须用 --headless=false 有头模式）
rscore --user --headless=false

# 4. 验证预检通过
rscore --preflight --dry-run
# 预期：预检通过，退出码 0

# 5. 日常运行（可无头）
rscore --headless
```

### 场景 2：CI/CD 中使用预检

```yaml
# .github/workflows/e2e.yml
jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Deploy storage_state.json
        run: |
          # storage_state.json 作为 GitHub Secret 注入到 $SECRET_STATE_PATH
          echo "$SECRET_STATE_CONTENT" > /home/runner/.msrewards/storage_state.json
        env:
          SECRET_STATE_CONTENT: ${{ secrets.STORAGE_STATE_JSON }}

      - name: Preflight Check
        run: |
          # 在配置文件中设置绝对路径
          echo "account:" >> config.yaml
          echo "  storage_state_path: /home/runner/.msrewards/storage_state.json" >> config.yaml

          # 执行预检（快速失败）
          E2E_PREFLIGHT=1 python -m src.cli --preflight --dry-run

      - name: E2E Test
        if: success()  # 只有预检通过才执行
        run: |
          rscore --dev --headless
```

---

## 8. 故障排查清单

**新项目首次运行**：

- [ ] 在 WSL 环境中（非 Windows CMD）
- [ ] `storage_state.json` 路径是非挂载的 Linux 路径
- [ ] 使用 `rscore --user --headless=false` 首次登录
- [ ] 登录完成后 `storage_state.json` 文件存在且大小 > 1KB
- [ ] 运行 `rscore --preflight --dry-run` 显示预检通过

**CI/CD 管道配置**：

- [ ] runners 为 Linux（如 ubuntu-latest）
- [ ] `storage_state.json` 部署到 runners 的本地 FS（非 `/mnt/`）
- [ ] 配置文件中 `account.storage_state_path` 指向绝对路径
- [ ] 预检步骤在 E2E 测试之前，且失败时阻止后续步骤
- [ ] 设置了 `E2E_PREFLIGHT=1` 环境变量（如需会话验证）

---

## 9. 参考文档

- [WORKFLOW.md](../reference/WORKFLOW.md) - 开发和验收流程
- [CLAUDE.md](../CLAUDE.md) - 项目全局指令和代码规范
- `src/infrastructure/preflight.py` - 预检模块实现

---

**最后更新**：2026-03-21
**维护者**：RewardsCore 社区
