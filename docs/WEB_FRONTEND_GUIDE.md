# Web 前端开发指南

## 一、项目概述

MS Rewards Automator 前端是一个基于 **Tauri 2.0** 构建的桌面应用，采用 React + TypeScript + Vite + TailwindCSS 技术栈，提供原生桌面体验。

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Tauri | 2.x | 桌面应用框架 |
| React | 18.x | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| TailwindCSS | 3.x | 样式框架 |
| Zustand | 4.x | 状态管理 |
| Axios | 1.x | HTTP 客户端 |
| Lucide React | 0.x | 图标库 |
| Sonner | 1.x | Toast 通知 |
| Framer Motion | 11.x | 动画库 |

### 项目结构

```
frontend/
├── src/                        # React 前端源码
│   ├── api/                    # API 调用模块
│   │   └── index.ts            # API 函数、WebSocket、Tauri 事件
│   ├── components/             # UI 组件
│   │   ├── ui/                 # 基础 UI 组件
│   │   │   ├── button.tsx      # 按钮组件
│   │   │   ├── card.tsx        # 卡片组件
│   │   │   ├── skeleton.tsx    # 骨架屏组件
│   │   │   ├── sonner.tsx      # Toast 通知组件
│   │   │   └── index.ts        # 统一导出
│   │   ├── Layout.tsx          # 页面布局
│   │   ├── Sidebar.tsx         # 侧边栏导航
│   │   └── Header.tsx          # 顶部状态栏
│   ├── pages/                  # 页面组件
│   │   ├── Dashboard.tsx       # 仪表盘
│   │   ├── Tasks.tsx           # 任务控制
│   │   ├── Config.tsx          # 配置管理
│   │   ├── Logs.tsx            # 日志查看
│   │   └── History.tsx         # 历史记录
│   ├── store/                  # 状态管理
│   │   └── index.ts            # Zustand store
│   ├── lib/
│   │   └── utils.ts            # 工具函数
│   ├── App.tsx                 # 根组件
│   ├── main.tsx                # 入口文件
│   └── index.css               # 全局样式
│
├── src-tauri/                  # Tauri 后端 (Rust)
│   ├── src/
│   │   ├── lib.rs              # Tauri 应用入口
│   │   └── main.rs             # Rust main 函数
│   ├── Cargo.toml              # Rust 依赖配置
│   ├── tauri.conf.json         # Tauri 配置文件
│   ├── capabilities/           # 权限配置
│   └── icons/                  # 应用图标
│
├── package.json                # npm 依赖
├── tailwind.config.js          # TailwindCSS 配置
├── vite.config.ts              # Vite 构建配置
└── tsconfig.json               # TypeScript 配置
```

---

## 二、开发环境设置

### 前置要求

- Node.js 18.x 或更高版本
- Rust 1.70+ (Tauri 依赖)
- Python 3.10+ (后端依赖)

### 安装步骤

```bash
# 1. 安装前端依赖
cd frontend
npm install

# 2. 启动 Python 后端 (开发模式需要手动启动)
conda activate ms-rewards-bot
python web_server.py --host 127.0.0.1 --port 8000

# 3. 启动 Tauri 开发模式
npm run tauri:dev
```

开发服务器将在 `http://localhost:3000` 启动，Tauri 窗口会自动打开。

### 构建生产版本

```bash
# 构建 Tauri 应用
npm run tauri:build
```

构建产物位于 `src-tauri/target/release/bundle/` 目录。

---

## 三、Tauri 架构

### 3.1 进程通信

```
┌─────────────────────────────────────────────────────────────┐
│                     Tauri 主进程 (Rust)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  lib.rs                                              │   │
│  │  - 动态端口分配 (portpicker)                          │   │
│  │  - Sidecar 进程管理                                   │   │
│  │  - 事件发射 (py-log, py-error)                        │   │
│  │  - 窗口生命周期管理                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           │ IPC (invoke / emit)             │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              WebView2 (前端渲染)                      │   │
│  │  React + TypeScript + Vite                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python 后端 (FastAPI)                       │
│  - REST API 端点                                            │
│  - WebSocket 实时通信                                        │
│  - 任务调度与执行                                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 动态端口分配

生产模式下，Tauri 使用 `portpicker` 自动分配可用端口：

```rust
// src-tauri/src/lib.rs
use portpicker::pick_unused_port;

let port = pick_unused_port().expect("No free port");
BACKEND_PORT.store(port, Ordering::SeqCst);
```

前端通过 Tauri 命令获取端口：

```typescript
// src/api/index.ts
const port = await invoke<number>('get_backend_port');
```

### 3.3 Sidecar 进程管理

生产模式下，Python 后端作为 Sidecar 进程启动：

```rust
// 仅在发布模式启动 Sidecar
#[cfg(not(debug_assertions))]
{
    let shell = app.shell();
    let (mut rx, child) = shell.sidecar("backend")?.spawn()?;
    
    // 监听后端输出
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            if let CommandEvent::Stdout(line) = event {
                app.emit("py-log", line)?;
            }
        }
    });
}
```

### 3.4 Tauri 事件系统

前端监听 Rust 发出的事件：

```typescript
// src/api/index.ts
import { listen } from '@tauri-apps/api/event';

// 监听 Python 日志
await listen<string>('py-log', (event) => {
    console.log('Python:', event.payload);
});

// 监听后端终止
await listen<void>('backend-terminated', () => {
    toast.error('后端进程已终止');
});
```

---

## 四、后端 API 服务

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/status` | GET | 获取任务状态 |
| `/api/task/start` | POST | 启动任务 |
| `/api/task/stop` | POST | 停止任务 |
| `/api/config` | GET/PUT | 配置管理 |
| `/api/health` | GET | 健康状态 |
| `/api/points` | GET | 积分信息 |
| `/api/logs/recent` | GET | 最近日志 |
| `/api/logs/stream` | GET | 日志流 (SSE) |
| `/api/history` | GET | 历史记录 |
| `/api/dashboard` | GET | 仪表盘数据 |
| `/ws` | WebSocket | 实时通信 |

### WebSocket 消息类型

```typescript
// 状态更新
{ type: "status_update", timestamp: string, data: TaskStatus }

// 健康状态更新
{ type: "health_update", timestamp: string, data: Health }

// 积分更新
{ type: "points_update", timestamp: string, data: Points }

// 日志消息
{ type: "log", timestamp: string, data: string }

// 任务事件
{ type: "task_event", event: string, message: string, details: object }
```

---

## 五、状态管理

### Store 结构

```typescript
// src/store/index.ts
interface Store {
  // 任务状态
  taskStatus: TaskStatus | null
  
  // 健康状态
  health: Health | null
  
  // 配置
  config: Config | null
  
  // 主题
  darkMode: boolean
  
  // 后端状态
  backendReady: boolean
  backendPort: number | null
  lastHeartbeat: number | null
  
  // 操作方法
  setTaskStatus: (status: TaskStatus) => void
  setHealth: (health: Health) => void
  toggleDarkMode: () => void
  // ...
}
```

### 心跳机制

前端定期检测后端存活状态：

```typescript
// src/api/index.ts
export function startHeartbeat() {
  setInterval(async () => {
    try {
      const health = await fetchHealth();
      useStore.getState().setHealth(health);
      useStore.getState().setLastHeartbeat(Date.now());
    } catch {
      useStore.getState().setBackendReady(false);
    }
  }, 5000);
}
```

---

## 六、UI 组件

### 6.1 Toast 通知 (Sonner)

```tsx
import { toast } from 'sonner';

// 成功通知
toast.success('任务启动成功');

// 错误通知
toast.error('连接后端失败');

// 带操作的通知
toast('配置已保存', {
  action: {
    label: '撤销',
    onClick: () => console.log('撤销')
  }
});
```

### 6.2 骨架屏 (Skeleton)

```tsx
import { Skeleton } from '@/components/ui';

// 基础骨架
<Skeleton className="h-4 w-48" />

// 卡片骨架
<div className="space-y-3">
  <Skeleton className="h-4 w-3/4" />
  <Skeleton className="h-4 w-1/2" />
  <Skeleton className="h-4 w-2/3" />
</div>
```

### 6.3 Toggle 开关

```tsx
// 使用 flexbox 居中指示器
<div className="w-10 h-6 rounded-full flex items-center">
  <div className="w-4 h-4 rounded-full transition-all" />
</div>
```

---

## 七、主题系统

### 暗色/亮色模式

```typescript
// 切换主题
const { darkMode, toggleDarkMode } = useStore()
toggleDarkMode()
```

### 条件样式

```tsx
<div className={clsx(
  'rounded-xl p-5 border',
  darkMode 
    ? 'bg-surface-300/80 border-dark-600/50' 
    : 'bg-white border-gray-200 shadow-sm'
)}>
```

### 颜色映射

| 暗色模式 | 亮色模式 | 用途 |
|---------|---------|------|
| `bg-dark-900` | `bg-gray-100` | 页面背景 |
| `bg-surface-300/80` | `bg-white` | 卡片背景 |
| `text-dark-100` | `text-gray-900` | 主要文本 |
| `text-dark-400` | `text-gray-500` | 次要文本 |

---

## 八、窗口效果

### Mica 效果 (Windows 11)

```json
// tauri.conf.json
{
  "app": {
    "windows": [{
      "transparent": true,
      "shadow": true,
      "windowEffects": {
        "effects": ["mica"],
        "state": "active"
      }
    }]
  }
}
```

### 拖拽区域

```tsx
// Header.tsx
<div data-tauri-drag-region className="flex items-center gap-3">
  {/* 可拖拽区域 */}
</div>
```

---

## 九、常见问题

### Q: 开发模式下前端无法连接后端?

确保 Python 后端在 `localhost:8000` 运行。开发模式下 Tauri 不启动 Sidecar，需要手动启动后端。

### Q: Tauri 编译失败?

1. 确保已安装 Rust: `rustc --version`
2. 清理缓存: `cd src-tauri && cargo clean`
3. 重新编译: `cargo check`

### Q: 如何调试 Rust 代码?

使用 `println!` 或 `eprintln!` 输出到控制台，或使用 `log` crate 配合 `tauri-plugin-log`。

### Q: Sidecar 启动失败?

检查 `src-tauri/binaries/` 目录下是否存在对应的二进制文件。

---

## 十、部署指南

### 构建发布版本

```bash
cd frontend
npm run tauri:build
```

### 构建产物

| 文件 | 说明 |
|------|------|
| `.msi` | Windows 安装包 |
| `.exe` | 便携版可执行文件 |
| `.nsis.zip` | NSIS 安装包 |

### 自动更新

Tauri 支持自动更新功能，配置 `tauri.conf.json`:

```json
{
  "plugins": {
    "updater": {
      "endpoints": ["https://your-domain.com/updates/{{target}}/{{arch}}/{{current_version}}"],
      "pubkey": "your-public-key"
    }
  }
}
```

---

## 相关文档

- [Tauri 架构文档](./TAURI_ARCHITECTURE.md)
- [验收方案](./FRONTEND_ACCEPTANCE.md)
- [用户指南](./guides/用户指南.md)
