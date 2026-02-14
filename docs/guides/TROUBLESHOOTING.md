# 🔧 故障排除指南

## 目录
- [常见问题](#常见问题)
- [已修复问题](#已修复问题)
- [错误解决](#错误解决)
- [使用建议](#使用建议)

---

## 常见问题

### 无头模式看不到浏览器

**设计行为**：程序会自动检测登录状态，首次运行会显示浏览器，后续运行会自动切换到无头模式（后台运行）。

如果想强制显示浏览器：
```cmd
python main.py --headless=false
```

### 会话过期需要重新登录

**解决方法**：
1. 删除 `storage_state.json` 文件
2. 运行 `quick_start.bat`
3. 手动完成登录

### 积分没有增加

**可能原因**：
- 已达到每日搜索上限（桌面30次，移动20次）
- 积分延迟更新
- 网络问题

**解决方法**：
- 查看数据面板确认今天的任务完成情况
- 等待几分钟后再检查
- 使用慢速模式：`python main.py --mode slow`

---

## 已修复问题

### 搜索计数为 0 的问题

**问题**: 报告显示桌面搜索和移动搜索都是 0 次，但实际搜索已成功执行  
**原因**: `state_monitor.check_points_after_searches` 在监控禁用时直接返回，不更新搜索计数  
**修复**: 将搜索计数更新移到监控检查之前  
**文件**: `src/infrastructure/state_monitor.py`

### 状态显示 NoneType 比较错误

**问题**: `'>' not supported between instances of 'NoneType' and 'int'`  
**原因**: `current_points` 可能为 `None`，直接与 `0` 比较导致错误  
**修复**: 添加 `None` 检查  
**文件**: `src/ui/real_time_status.py`

### 积分检测错误（提取礼品卡面值）

**问题**: 积分检测返回 150,000，实际积分是 915  
**原因**: 正则表达式匹配了页面上所有带 "points" 的数字，包括礼品卡面值  
**修复**: 优先使用选择器定位用户积分区域，使用更精确的正则模式  
**文件**: `src/account/points_detector.py`

### OAuth 页面导航增强

**问题**: 任务发现时页面停留在 OAuth 授权页面  
**原因**: `_wait_for_dashboard` 导航失败后没有进一步处理  
**修复**: 添加页面内容检查和强制导航逻辑

---

## 错误解决

### Python 未找到

```
'python' is not recognized as an internal or external command
```

**解决**：确认 Python 已安装并添加到 PATH，或尝试使用 `py` 命令。

### 模块未找到

```
ModuleNotFoundError: No module named 'xxx'
```

**解决**：
```cmd
pip install -r requirements.txt
```

### 浏览器启动失败

```
Executable doesn't exist at xxx
```

**解决**：
```cmd
playwright install chromium
```

### 端口被占用（数据面板）

```
Address already in use
```

**解决**：关闭其他占用 8501 端口的程序，或重启电脑。

## 使用建议

### 安全使用

- ✅ 使用慢速模式：`python main.py --mode slow`
- ✅ 启用调度器随机时间运行
- ✅ 不要频繁手动运行
- ❌ 不要在短时间内多次运行

### 查看日志

出现问题时，查看日志文件：
```cmd
notepad logs\automator.log
```

### 获取帮助

如果问题仍未解决，查看日志文件并提交 GitHub Issue。

---

**现在可以正常使用了！** 🎉