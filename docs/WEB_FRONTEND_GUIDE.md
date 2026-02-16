# Web 前端开发指南

## 一、项目概述

MS Rewards Automator Web 前端是一个基于 React + TypeScript + Vite + TailwindCSS 构建的现代化 Web 界面，用于管理和监控 Microsoft Rewards 自动化任务。

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| TailwindCSS | 3.x | 样式框架 |
| Zustand | 4.x | 状态管理 |
| Axios | 1.x | HTTP 客户端 |
| Lucide React | 0.x | 图标库 |

### 项目结构

```
frontend/
├── src/
│   ├── api/                    # API 调用模块
│   │   └── index.ts            # API 函数和 WebSocket 连接
│   ├── components/             # UI 组件
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
│   ├── App.tsx                 # 根组件
│   ├── main.tsx                # 入口文件
│   └── index.css               # 全局样式
├── public/                     # 静态资源
├── package.json                # 依赖配置
├── vite.config.ts              # Vite 配置
├── tailwind.config.js          # TailwindCSS 配置
└── tsconfig.json               # TypeScript 配置
```

## 二、开发环境设置

### 前置要求

- Node.js 18.x 或更高版本
- npm 9.x 或更高版本
- Python 3.10+ (后端依赖)

### 安装步骤

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动，并自动代理 API 请求到后端。

### 构建生产版本

```bash
# 构建前端
npm run build

# 预览构建结果
npm run preview
```

## 三、后端 API 服务

### 启动后端

```bash
# 在项目根目录
python web_server.py
```

后端服务将在 `http://localhost:8000` 启动。

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

## 四、开发注意事项

### 4.1 样式规范

项目使用 TailwindCSS，遵循以下规范：

```css
/* 使用预定义的颜色变量 */
.text-primary-400    /* 主色调 */
.text-success-400    /* 成功状态 */
.text-warning-400    /* 警告状态 */
.text-danger-400     /* 错误状态 */
.text-dark-400       /* 次要文本 */

/* 使用预定义的组件类 */
.card                /* 卡片容器 */
.btn-primary         /* 主按钮 */
.btn-secondary       /* 次要按钮 */
.input               /* 输入框 */
.badge-success       /* 成功徽章 */
```

### 4.2 状态管理

使用 Zustand 进行状态管理，遵循以下规范：

```typescript
// 在 store/index.ts 中定义状态
interface Store {
  // 状态
  taskStatus: TaskStatus | null
  health: Health | null
  
  // 操作
  setTaskStatus: (status: TaskStatus) => void
  setHealth: (health: Health) => void
}

// 在组件中使用
const { taskStatus, setTaskStatus } = useStore()
```

### 4.3 API 调用

```typescript
// 使用 async/await 处理 API 调用
const handleStart = async () => {
  try {
    await startTask(options)
  } catch (error) {
    console.error('Failed to start task:', error)
  }
}
```

### 4.4 WebSocket 连接

```typescript
// 在组件挂载时连接
useEffect(() => {
  connectWebSocket()
  return () => disconnectWebSocket()
}, [])

// WebSocket 会自动更新 store 中的状态
```

## 五、功能模块说明

### 5.1 仪表盘 (Dashboard)

- 显示当前积分和今日获得积分
- 显示桌面/移动搜索进度（默认桌面30次、移动20次）
- 显示运行时间和健康状态
- 显示任务提示（未完成任务、错误、积分获取失败等）

### 5.2 任务控制 (Tasks)

- 选择执行模式 (正常/用户/开发)
- 配置执行选项 (无头模式、仅桌面/移动、跳过任务)
- 启动/停止任务
- 实时显示任务进度和积分变化

### 5.3 配置管理 (Config)

- 搜索设置 (搜索次数、间隔时间)
- 浏览器设置 (类型、无头模式)
- 登录设置 (自动登录、2FA)
- 通知设置 (Telegram)
- 调度器设置
- 监控设置

### 5.4 日志查看 (Logs)

- 实时日志流
- 按级别过滤 (INFO/WARNING/ERROR/DEBUG)
- 关键词搜索
- 导出日志

### 5.5 历史记录 (History)

- 执行历史列表
- 积分趋势图表
- 统计数据 (总积分、日均、搜索次数)

## 六、主题系统

### 6.1 暗色/亮色模式

项目支持暗色和亮色两种主题模式，通过 Zustand store 管理：

```typescript
// 切换主题
const { darkMode, toggleDarkMode } = useStore()
toggleDarkMode()
```

### 6.2 主题适配规范

所有组件应支持暗色/亮色模式切换：

```typescript
// 使用 clsx 进行条件样式
<div className={clsx(
  'rounded-xl p-5 border',
  darkMode 
    ? 'bg-surface-300/80 border-dark-600/50' 
    : 'bg-white border-gray-200 shadow-sm'
)}>
```

### 6.3 颜色映射

| 暗色模式 | 亮色模式 | 用途 |
|---------|---------|------|
| `bg-dark-900` | `bg-gray-100` | 页面背景 |
| `bg-surface-300/80` | `bg-white` | 卡片背景 |
| `text-dark-100` | `text-gray-900` | 主要文本 |
| `text-dark-400` | `text-gray-500` | 次要文本 |
| `bg-dark-700` | `bg-gray-200` | 进度条背景 |

## 七、常见问题

### Q: 前端无法连接后端？

检查以下几点：

1. 后端服务是否已启动 (`python web_server.py`)
2. 后端端口是否正确 (默认 8000)
3. 防火墙是否阻止连接

### Q: WebSocket 连接失败？

1. 确保后端 WebSocket 端点 `/ws` 可访问
2. 检查浏览器控制台是否有错误
3. WebSocket 会自动重连，等待几秒

### Q: 构建失败？

1. 检查 TypeScript 类型错误
2. 确保所有依赖已安装 (`npm install`)
3. 清除缓存重新构建 (`rm -rf node_modules && npm install`)

### Q: 样式不生效？

1. 确保 TailwindCSS 类名正确
2. 检查 `tailwind.config.js` 中的 content 配置
3. 重启开发服务器

## 八、部署指南

### 8.1 构建前端

```bash
cd frontend
npm run build
```

构建产物将生成在 `frontend/dist` 目录。

### 8.2 启动生产服务

```bash
python web_server.py --host 0.0.0.0 --port 8000
```

后端会自动服务前端静态文件。

### 8.3 环境变量

可以通过环境变量配置：

```bash
# 设置监听地址
export HOST=0.0.0.0
export PORT=8000

python web_server.py
```

## 九、已知问题

### 9.1 停止任务功能问题

**现象**：停止任务按钮无法点击，任务启动后 `is_running` 状态未正确更新。

**原因**：`task_service.py` 中 `asyncio.current_task()` 在 `start_task` 函数开始时调用，但此时任务尚未真正开始执行。需要在任务真正开始后获取 task 引用。

**临时解决方案**：
- 后端需要修复 `task_service.py` 中的任务跟踪逻辑
- 确保 `is_running` 状态通过 WebSocket 正确广播到前端

### 9.2 积分获取失败

**现象**：前端显示"当前积分获取失败"。

**原因**：`main` 分支的积分获取模块选择器可能存在问题，导致无法正确获取积分数据。

**影响范围**：影响前端仪表盘的积分显示和任务提示功能。

**解决方案**：需要在 `main` 分支修复积分获取逻辑后再同步到前端分支。

### 9.3 进度显示问题

**现象**：任务进度显示为 "0 / 0"。

**已修复**：使用 `||` 运算符替代 `??` 运算符，确保 0 值能正确触发默认值回退。

```typescript
// 修复前（错误）
total={taskStatus?.desktop_searches_total ?? config?.search.desktop_count ?? 30}

// 修复后（正确）
total={taskStatus?.desktop_searches_total || config?.search.desktop_count || 30}
```

## 十、扩展开发

### 添加新页面

1. 在 `src/pages/` 创建新组件
2. 在 `src/App.tsx` 添加路由
3. 在 `src/components/Sidebar.tsx` 添加导航项

### 添加新 API

1. 在 `src/api/index.ts` 添加 API 函数
2. 在 `src/store/index.ts` 添加状态类型
3. 在后端 `src/api/routes.py` 添加端点

### 添加新组件

1. 在 `src/components/` 创建组件文件
2. 使用 TailwindCSS 类进行样式
3. 通过 props 和 store 进行数据交互
