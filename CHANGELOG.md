# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **多智能体协作框架**: 添加 MCP 驱动的多智能体架构
  - `master-agent`: 主控调度，负责任务路由、Memory 知识管理、PR 交付
  - `dev-agent`: 开发智能体，负责业务代码编写与局部验证
  - `test-agent`: 测试智能体，负责 E2E 验收与 Playwright 自动化
  - `docs-agent`: 文档智能体，负责 README/CHANGELOG/API 文档同步

- **MCP 驱动工作流**: 添加基于 Model Context Protocol 的自动化工作流
  - Memory MCP: 跨会话知识持久化
  - GitHub MCP: PR 管理与版本交付自动化
  - Playwright MCP: 无头浏览器验收测试

- **Skills 系统**: 添加可复用的技能模块
  - `mcp-acceptance`: 7 阶段验收流程自动化
  - `pr-review`: PR 审查与 AI 审查机器人交互

### Changed

- **验收流程优化**: 删除"本地审查阻塞点"，简化验收流程
  - 阶段 5 后不再等待本地审查
  - 阶段 6 后直接等待在线 AI 审查（Copilot、Sourcery、Qodo）

- **PR 合并策略**: 细化合并确认规则
  - 常规 Bugfix/Feature: 自动合并
  - 核心/大规模变更: 需人工确认

### Fixed

- 修复 Sourcery AI 审查发现的问题

---

## 版本说明

- **Added**: 新功能
- **Changed**: 现有功能的变更
- **Deprecated**: 即将废弃的功能
- **Removed**: 已移除的功能
- **Fixed**: Bug 修复
- **Security**: 安全相关的修复
