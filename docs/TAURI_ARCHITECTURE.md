# Tauri + Shadcn/UI 前端架构文档

## 概述

本项目已从传统的 Web 前端升级为 **Tauri 2.0 桌面应用**，采用 **Shadcn/UI** 组件库和 **Framer Motion** 动效系统，实现轻量级原生 EXE 打包。

---

## 架构对比

| 维度 | 原方案 (Web) | 新方案 (Tauri) |
|------|-------------|---------------|
| 交付形式 | 浏览器访问 localhost:3000 | 独立 EXE 程序 |
| 启动方式 | 手动启动 Python + 打开网页 | 双击 EXE 一键启动 |
| 安装包体积 | N/A | ~10MB |
| 内存占用 | 高 (依赖 Chrome) | 极低 (系统原生 WebView2) |
| 视觉效果 | 中等 | 高级 (支持毛玻璃/透明度) |

---

## 目录结构

```
frontend/
├── src/                      # React 前端源码
│   ├── components/
│   │   ├── ui/               # Shadcn/UI 组件库
│   │   │   ├── button.tsx    # 按钮组件
│   │   │   ├── card.tsx      # 卡片组件
│   │   │   ├── tabs.tsx      # 标签页组件
│   │   │   ├── progress.tsx  # 进度条组件
│   │   │   ├── badge.tsx     # 徽章组件
│   │   │   ├── tooltip.tsx   # 工具提示组件
│   │   │   ├── scroll-area.tsx # 滚动区域组件
│   │   │   ├── animated.tsx  # Framer Motion 动画组件
│   │   │   └── index.ts      # 统一导出
│   │   ├── Layout.tsx        # 页面布局
│   │   ├── Sidebar.tsx       # 侧边栏
│   │   └── Header.tsx        # 顶部栏
│   ├── pages/                # 页面组件
│   │   ├── Dashboard.tsx     # 仪表盘
│   │   ├── Tasks.tsx         # 任务控制
│   │   ├── Config.tsx        # 配置管理
│   │   ├── Logs.tsx          # 日志查看
│   │   └── History.tsx       # 历史记录
│   ├── lib/
│   │   └── utils.ts          # 工具函数 (cn)
│   ├── store/
│   │   └── index.ts          # Zustand 状态管理
│   └── api/
│       └── index.ts          # API 请求封装
│
├── src-tauri/                # Tauri 后端 (Rust)
│   ├── src/
│   │   ├── lib.rs            # Tauri 应用入口
│   │   └── main.rs           # Rust main 函数
│   ├── Cargo.toml            # Rust 依赖配置
│   ├── tauri.conf.json       # Tauri 配置文件
│   ├── capabilities/         # 权限配置
│   └── icons/                # 应用图标
│
├── binaries/                 # Sidecar 二进制文件
│   └── backend-*.exe         # Python 后端打包文件
│
├── package.json              # npm 依赖
├── tailwind.config.js        # TailwindCSS 配置
├── vite.config.ts            # Vite 构建配置
└── tsconfig.json             # TypeScript 配置
```

---

## 核心技术栈

### 1. Tauri 2.0

Tauri 是一个使用 Web 技术构建桌面应用的框架，相比 Electron：

- **体积极小**: 使用系统原生 WebView2，打包后仅 ~10MB
- **资源占用低**: 内存消耗仅为 Electron 的 1/3
- **安全性高**: 使用 IPC 进程间通信，不暴露端口

### 2. Shadcn/UI

基于 Radix UI 和 TailwindCSS 的组件库：

- **无依赖锁定**: 组件代码直接复制到项目中，完全可控
- **高度可定制**: 可轻松修改样式和行为
- **暗色模式**: 内置完善的暗色主题支持

### 3. Framer Motion

React 动画库，用于：

- 页面过渡动画
- 列表项入场动画
- 交互动效 (悬停、点击)

---

## 组件使用指南

### Button 按钮

```tsx
import { Button } from '@/components/ui'

// 基础用法
<Button>默认按钮</Button>

// 变体
<Button variant="destructive">删除</Button>
<Button variant="outline">边框按钮</Button>
<Button variant="ghost">幽灵按钮</Button>
<Button variant="success">成功按钮</Button>

// 尺寸
<Button size="sm">小按钮</Button>
<Button size="lg">大按钮</Button>
```

### Card 卡片

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui'

<Card>
  <CardHeader>
    <CardTitle>卡片标题</CardTitle>
  </CardHeader>
  <CardContent>
    卡片内容
  </CardContent>
</Card>
```

### Progress 进度条

```tsx
import { Progress } from '@/components/ui'

<Progress value={75} />
```

### Badge 徽章

```tsx
import { Badge } from '@/components/ui'

<Badge>默认</Badge>
<Badge variant="success">成功</Badge>
<Badge variant="warning">警告</Badge>
<Badge variant="destructive">错误</Badge>
```

### Framer Motion 动画

```tsx
import { motion, AnimatePresence } from 'framer-motion'
import { AnimatedDiv, StaggerContainer, StaggerItem } from '@/components/ui/animated'

// 单元素动画
<AnimatedDiv variant="fadeInUp">
  淡入上升
</AnimatedDiv>

// 列表交错动画
<StaggerContainer>
  {items.map(item => (
    <StaggerItem key={item.id}>
      {item.name}
    </StaggerItem>
  ))}
</StaggerContainer>

// 条件渲染动画
<AnimatePresence>
  {isVisible && (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      内容
    </motion.div>
  )}
</AnimatePresence>
```

---

## 开发命令

### 开发模式

```bash
# 1. 启动 Python 后端 (在项目根目录)
conda activate ms-rewards-bot
python web_server.py

# 2. 启动 Tauri 开发模式 (在 frontend 目录)
cd frontend
npm run tauri:dev
```

### 构建生产版本

```bash
# 构建前端 + Tauri
cd frontend
npm run tauri:build
```

构建产物位于 `src-tauri/target/release/bundle/` 目录。

---

## Python 后端打包 (Sidecar)

### 步骤 1: 安装 PyInstaller

```bash
conda activate ms-rewards-bot
pip install pyinstaller
```

### 步骤 2: 运行打包脚本

```bash
python scripts/build_backend.py
```

打包后的文件位于 `frontend/src-tauri/binaries/` 目录。

### 步骤 3: 启用 Sidecar 配置

编辑 `frontend/src-tauri/tauri.conf.json`:

```json
{
  "bundle": {
    "externalBin": [
      "binaries/backend"
    ]
  }
}
```

### 步骤 4: 更新 Rust 代码

编辑 `frontend/src-tauri/src/lib.rs`，添加 Sidecar 启动逻辑：

```rust
use tauri_plugin_shell::ShellExt;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 仅在发布模式启动 Sidecar
            #[cfg(not(debug_assertions))]
            {
                let shell = app.shell();
                let (mut rx, child) = shell.sidecar("backend")?.spawn()?;
                
                // 监听后端输出
                tauri::async_runtime::spawn(async move {
                    while let Some(event) = rx.recv().await {
                        // 处理事件
                    }
                });
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

---

## 配色方案

项目使用自定义配色，定义在 `tailwind.config.js`:

| 颜色 | 用途 |
|------|------|
| primary | 主色调 (蓝色) |
| success | 成功状态 (绿色) |
| warning | 警告状态 (黄色) |
| danger | 错误状态 (红色) |
| cyan | 信息状态 (青色) |
| purple | 特殊状态 (紫色) |
| dark | 文字颜色层级 |
| surface | 背景颜色层级 |

---

## 窗口配置

窗口设置在 `tauri.conf.json`:

```json
{
  "app": {
    "windows": [{
      "title": "MS Rewards Automator",
      "width": 1280,
      "height": 800,
      "minWidth": 900,
      "minHeight": 600,
      "center": true,
      "resizable": true,
      "shadow": true
    }]
  }
}
```

---

## 常见问题

### Q: 开发模式下前端无法连接后端?

确保 Python 后端在 `localhost:8000` 运行，检查 `vite.config.ts` 中的代理配置。

### Q: Tauri 编译失败?

1. 确保已安装 Rust: `rustc --version`
2. 清理缓存: `cd src-tauri && cargo clean`
3. 重新编译: `cargo check`

### Q: 如何添加新的 UI 组件?

1. 在 `src/components/ui/` 创建新组件文件
2. 使用 `cn()` 函数合并样式
3. 在 `index.ts` 中导出

### Q: 如何自定义主题?

修改 `tailwind.config.js` 中的 `colors` 配置。

---

## 相关文档

- [Tauri 官方文档](https://tauri.app/v2/guides/)
- [Shadcn/UI 文档](https://ui.shadcn.com/)
- [Framer Motion 文档](https://www.framer.com/motion/)
- [TailwindCSS 文档](https://tailwindcss.com/docs)
