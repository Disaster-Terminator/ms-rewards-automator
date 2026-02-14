# 📖 使用指南

## 🚀 快速开始

### 首次使用

**1. 环境准备**
```bash
# Windows用户（推荐）
git clone https://github.com/yourusername/ms-rewards-automator.git
cd ms-rewards-automator
conda env create -f environment.yml
conda activate ms-rewards-bot

# Linux/macOS用户
git clone https://github.com/yourusername/ms-rewards-automator.git
cd ms-rewards-automator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**2. 首次运行**
```bash
# 开发模式（推荐首次使用）
python main.py --dev --headless

# 或使用脚本
# Windows: quick_start.bat
# Linux: ./scripts/unix/quick_start.sh
```

**首次运行会**：
- ✅ 打开浏览器，需要手动登录Microsoft账号
- 💾 自动保存登录会话（storage_state.json）
- 🔄 后续运行自动使用保存的会话

## 🎯 基本使用

### 常用命令

```bash
# 立即执行一次任务
python main.py

# 无头模式运行（后台）
python main.py --headless

# 快速模式（减少等待时间）
python main.py --mode fast

# 仅执行桌面搜索
python main.py --desktop-only

# 仅执行移动搜索
python main.py --mobile-only

# 测试通知功能
python main.py --test-notification

# 调度模式（每天自动执行）
python main.py --schedule

# 立即执行一次后进入调度
python main.py --schedule --schedule-now
```

### 配置文件编辑

编辑 `config.yaml`：

```yaml
# 搜索任务
search:
  desktop_count: 30    # 桌面搜索次数
  mobile_count: 20     # 移动搜索次数
  wait_interval: 5     # 搜索间隔（秒）

# 浏览器
browser:
  headless: false     # 是否无头模式
  type: "chromium"    # 浏览器类型

# 登录方式（二选一）
login:
  # 方式1：手动登录（推荐）
  auto_login:
    enabled: false    # 使用手动登录

  # 方式2：自动登录（不推荐）
  # auto_login:
  #   enabled: true
  #   email: "your_email@example.com"
  #   password: "your_password"
  #   totp_secret: "your_totp_secret"

# 任务系统
task_system:
  enabled: true       # 是否完成每日任务
  debug_mode: false   # 是否保存调试截图

# 通知（可选）
notification:
  enabled: false      # 是否启用通知
  telegram:
    bot_token: ""
    chat_id: ""
```

## ⚠️ 重要提示

1. **首次使用必须手动登录**，保存会话后才能自动运行
2. **建议使用手动登录**，自动登录经常失败
3. **确保网络连接正常**，WSL2可能需要配置代理
4. **脚本在WSL2中可能无法访问Microsoft服务**，建议在Windows运行

## 🔧 故障排除

### 常见问题

**Q: 无法连接到Microsoft服务**
- A: 在WSL2环境中常见，建议在Windows运行或配置代理

**Q: 浏览器打开后无法登录**
- A: 检查网络连接，可能需要手动完成2FA验证

**Q: 任务执行不完整**
- A: 检查配置文件，确保task_system.enabled: true

**Q: 积分没有增长**
- A: 检查搜索是否正常完成，查看日志文件

### 日志文件

- 日志位置：`logs/automator.log`
- 调试模式：`python main.py --dev` 生成详细日志

## 📊 数据监控

### 实时状态
- 运行时会显示实时状态更新
- 显示当前操作、运行时间、进度

### 积分监控
- 自动监控积分变化
- 如果积分异常会记录警告

### 健康检查
- 内置健康监控
- 检查网络状态和系统资源

---

## 📞 支持

如有问题，请：
1. 查看 [故障排除](docs/guides/TROUBLESHOOTING.md)
2. 检查日志文件
3. 提交 Issue 并提供错误信息