# 前端分支验收方案

## 一、验收概述

由于前端是一个相对独立的模块，采用与主项目不同的技术栈（React + TypeScript），因此设计一套适合前端特性的自动化验收方案。

### 验收原则

1. **自动化优先** - 除最后一步人工验收外，其余步骤由 Agent 自查自纠
2. **快速失败** - 发现问题立即停止，不浪费时间
3. **分层验收** - 从代码质量到功能完整性逐层验证
4. **可重复执行** - 验收脚本可多次运行

## 二、验收流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    前端自动化验收 (阶段1-5)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  阶段1: 依赖检查 ──→ 阶段2: 类型检查 ──→ 阶段3: 构建验证                  │
│                              ↓                                          │
│         阶段4: 后端 API 验证 (失败立即停止)                               │
│                              ↓ 通过                                     │
│         阶段5: 前端功能验证 (自动化测试)                                  │
│                              ↓ 通过                                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              阶段6: 有头模式人工验收 (必须人工)                            │
└─────────────────────────────────────────────────────────────────────────┘
```

## 三、验收阶段详解

### 阶段1: 依赖检查

**目的**: 确保所有依赖正确安装

**验收命令**:
```bash
# 检查 Python 依赖
pip install -r requirements.txt
python -c "import fastapi, uvicorn, websockets; print('Python dependencies OK')"

# 检查 Node.js 依赖
cd frontend
npm install
npm ls --depth=0
```

**通过条件**:
- [ ] Python 依赖无缺失
- [ ] Node.js 依赖无缺失
- [ ] 无安全漏洞警告 (npm audit)

**失败处理**: 安装缺失依赖

---

### 阶段2: 类型检查

**目的**: 确保 TypeScript 类型安全

**验收命令**:
```bash
cd frontend
npm run build  # tsc 会自动执行类型检查
```

**通过条件**:
- [ ] TypeScript 编译无错误
- [ ] 无隐式 any 类型警告
- [ ] 无未使用变量警告

**失败处理**: 修复类型错误

---

### 阶段3: 构建验证

**目的**: 确保前端构建产物正确

**验收命令**:
```bash
cd frontend
npm run build

# 验证构建产物
ls -la dist/
ls -la dist/assets/
```

**通过条件**:
- [ ] dist/index.html 存在
- [ ] dist/assets/ 目录存在
- [ ] JS 文件生成正确
- [ ] CSS 文件生成正确
- [ ] 无构建警告

**失败处理**: 检查构建日志，修复问题

---

### 阶段4: 后端 API 验证

**目的**: 确保后端 API 服务正常

**验收命令**:
```bash
# 启动后端服务 (后台运行)
python web_server.py --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
sleep 5

# 测试 API 端点
curl -s http://127.0.0.1:8000/api/health | python -c "import sys,json; d=json.load(sys.stdin); exit(0 if d['overall'] else 1)"
curl -s http://127.0.0.1:8000/api/status | python -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'is_running' in d else 1)"
curl -s http://127.0.0.1:8000/api/config | python -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'search' in d else 1)"

# 测试前端页面
curl -s http://127.0.0.1:8000/ | grep -q "MS Rewards Automator"

# 停止服务
kill $SERVER_PID
```

**通过条件**:
- [ ] 服务器启动成功
- [ ] /api/health 返回有效 JSON
- [ ] /api/status 返回有效 JSON
- [ ] /api/config 返回有效 JSON
- [ ] 前端页面可访问

**失败处理**: 检查服务器日志，修复 API 问题

---

### 阶段5: 前端功能验证

**目的**: 验证前端核心功能

**验收命令**:
```bash
# 启动服务器
python web_server.py --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
sleep 5

# 测试 API 端点响应
echo "Testing API endpoints..."

# 1. 测试仪表盘数据
curl -s http://127.0.0.1:8000/api/dashboard | python -c "
import sys, json
d = json.load(sys.stdin)
required = ['status', 'health', 'config_summary', 'points']
missing = [k for k in required if k not in d]
if missing:
    print(f'FAIL: Missing keys: {missing}')
    exit(1)
print('PASS: Dashboard API')
"

# 2. 测试配置更新
curl -s -X PUT http://127.0.0.1:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"search": {"desktop_count": 35}}' | python -c "
import sys, json
d = json.load(sys.stdin)
if d.get('message') != '配置已更新':
    print('FAIL: Config update failed')
    exit(1)
print('PASS: Config update')
"

# 3. 测试日志获取
curl -s "http://127.0.0.1:8000/api/logs/recent?lines=10" | python -c "
import sys, json
d = json.load(sys.stdin)
if 'logs' not in d or 'count' not in d:
    print('FAIL: Logs API failed')
    exit(1)
print('PASS: Logs API')
"

# 4. 测试历史记录
curl -s "http://127.0.0.1:8000/api/history?days=7" | python -c "
import sys, json
d = json.load(sys.stdin)
if 'history' not in d:
    print('FAIL: History API failed')
    exit(1)
print('PASS: History API')
"

# 5. 测试静态资源
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/assets/index-1mMtJJXy.js | python -c "
import sys
code = sys.stdin.read().strip()
if code != '200':
    print(f'FAIL: Static assets returned {code}')
    exit(1)
print('PASS: Static assets')
"

# 停止服务
kill $SERVER_PID
```

**通过条件**:
- [ ] Dashboard API 正常
- [ ] Config API 正常
- [ ] Logs API 正常
- [ ] History API 正常
- [ ] 静态资源可访问

**失败处理**: 检查 API 响应，修复问题

---

### 阶段6: 有头模式人工验收 (必须)

**目的**: 人工确认 UI 交互和视觉效果

**验收命令**:
```bash
# 启动服务器
python web_server.py --host 127.0.0.1 --port 8000
```

**验收检查项**:

#### 6.1 页面加载
- [ ] 打开 http://localhost:8000 页面正常加载
- [ ] 无 JavaScript 控制台错误
- [ ] 样式正确渲染 (深色主题)

#### 6.2 仪表盘页面
- [ ] 积分信息正确显示
- [ ] 搜索进度条正确显示（默认桌面30次、移动20次）
- [ ] 任务提示区域正确显示（未完成任务、错误、积分获取失败等）
- [ ] 运行时间和健康状态正确显示

#### 6.3 任务控制页面
- [ ] 执行模式选择正常
- [ ] 选项开关正常工作
- [ ] 启动按钮响应正常
- [ ] 停止按钮响应正常（任务运行时可停止）
- [ ] 实时进度和积分变化正确显示

#### 6.4 主题切换功能
- [ ] 主题切换按钮正常工作
- [ ] 暗色模式样式正确
- [ ] 亮色模式样式正确
- [ ] 所有页面主题切换一致

#### 6.5 配置管理页面
- [ ] 各配置项正确显示
- [ ] 保存配置功能正常
- [ ] 表单验证正常

#### 6.6 日志查看页面
- [ ] 日志正确显示
- [ ] 过滤功能正常
- [ ] 搜索功能正常

#### 6.7 历史记录页面
- [ ] 历史列表正确显示
- [ ] 图表正确渲染

#### 6.8 WebSocket 连接
- [ ] 实时状态更新正常
- [ ] 无连接断开警告

**验收签字**:
```
验收人: ____________    日期: ____________
备注: _______________________________________________
```

## 四、自动化验收脚本

创建 `scripts/verify_frontend.py`:

```python
#!/usr/bin/env python3
"""
前端自动化验收脚本
执行阶段1-5的自动化验收
"""

import subprocess
import sys
import json
import time
import requests
from pathlib import Path


class FrontendVerifier:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.server_process = None
        
    def run_command(self, cmd, cwd=None):
        """运行命令并返回结果"""
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    
    def check(self, name, condition, message=""):
        """记录检查结果"""
        if condition:
            print(f"  ✅ {name}")
            self.passed += 1
        else:
            print(f"  ❌ {name}: {message}")
            self.failed += 1
        return condition
    
    def stage1_dependencies(self):
        """阶段1: 依赖检查"""
        print("\n[阶段1] 依赖检查")
        
        # Python 依赖
        code, _, err = self.run_command(
            "python -c 'import fastapi, uvicorn, websockets'"
        )
        self.check("Python 依赖", code == 0, err)
        
        # Node.js 依赖
        frontend_dir = Path("frontend")
        if (frontend_dir / "node_modules").exists():
            self.check("Node.js 依赖", True)
        else:
            code, _, err = self.run_command("npm install", cwd=frontend_dir)
            self.check("Node.js 依赖安装", code == 0, err)
        
        return self.failed == 0
    
    def stage2_typecheck(self):
        """阶段2: 类型检查"""
        print("\n[阶段2] 类型检查")
        
        frontend_dir = Path("frontend")
        code, out, err = self.run_command("npx tsc --noEmit", cwd=frontend_dir)
        self.check("TypeScript 类型检查", code == 0, err or out)
        
        return self.failed == 0
    
    def stage3_build(self):
        """阶段3: 构建验证"""
        print("\n[阶段3] 构建验证")
        
        frontend_dir = Path("frontend")
        code, out, err = self.run_command("npm run build", cwd=frontend_dir)
        self.check("前端构建", code == 0, err)
        
        dist_dir = frontend_dir / "dist"
        self.check("dist/index.html 存在", (dist_dir / "index.html").exists())
        self.check("dist/assets 存在", (dist_dir / "assets").exists())
        
        return self.failed == 0
    
    def stage4_backend(self):
        """阶段4: 后端 API 验证"""
        print("\n[阶段4] 后端 API 验证")
        
        # 启动服务器
        self.server_process = subprocess.Popen(
            ["python", "web_server.py", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(5)
        
        base_url = "http://127.0.0.1:8000"
        
        try:
            # 测试各端点
            endpoints = [
                ("/api/health", "overall"),
                ("/api/status", "is_running"),
                ("/api/config", "search"),
                ("/api/dashboard", "status"),
            ]
            
            for endpoint, key in endpoints:
                try:
                    resp = requests.get(f"{base_url}{endpoint}", timeout=5)
                    data = resp.json()
                    self.check(f"GET {endpoint}", key in data, f"Missing key: {key}")
                except Exception as e:
                    self.check(f"GET {endpoint}", False, str(e))
            
            # 测试前端页面
            try:
                resp = requests.get(base_url, timeout=5)
                self.check("前端页面可访问", "MS Rewards" in resp.text)
            except Exception as e:
                self.check("前端页面可访问", False, str(e))
                
        finally:
            self.stop_server()
        
        return self.failed == 0
    
    def stage5_frontend(self):
        """阶段5: 前端功能验证"""
        print("\n[阶段5] 前端功能验证")
        
        # 启动服务器
        self.server_process = subprocess.Popen(
            ["python", "web_server.py", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(5)
        
        base_url = "http://127.0.0.1:8000"
        
        try:
            # 测试配置更新
            try:
                resp = requests.put(
                    f"{base_url}/api/config",
                    json={"search": {"desktop_count": 35}},
                    timeout=5
                )
                self.check("PUT /api/config", resp.status_code == 200)
            except Exception as e:
                self.check("PUT /api/config", False, str(e))
            
            # 测试日志
            try:
                resp = requests.get(f"{base_url}/api/logs/recent?lines=10", timeout=5)
                data = resp.json()
                self.check("GET /api/logs/recent", "logs" in data)
            except Exception as e:
                self.check("GET /api/logs/recent", False, str(e))
            
            # 测试历史
            try:
                resp = requests.get(f"{base_url}/api/history?days=7", timeout=5)
                data = resp.json()
                self.check("GET /api/history", "history" in data)
            except Exception as e:
                self.check("GET /api/history", False, str(e))
                
        finally:
            self.stop_server()
        
        return self.failed == 0
    
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
    
    def run(self):
        """运行所有验收阶段"""
        print("=" * 60)
        print("MS Rewards Automator - 前端自动化验收")
        print("=" * 60)
        
        stages = [
            self.stage1_dependencies,
            self.stage2_typecheck,
            self.stage3_build,
            self.stage4_backend,
            self.stage5_frontend,
        ]
        
        for stage in stages:
            if not stage():
                print(f"\n❌ 验收在 {stage.__name__} 阶段失败")
                self.stop_server()
                return False
        
        print("\n" + "=" * 60)
        print(f"验收结果: 通过 {self.passed} / 失败 {self.failed}")
        print("=" * 60)
        
        if self.failed == 0:
            print("\n✅ 自动化验收通过，请进行阶段6人工验收")
            return True
        else:
            print("\n❌ 自动化验收失败，请修复问题后重试")
            return False


if __name__ == "__main__":
    verifier = FrontendVerifier()
    success = verifier.run()
    sys.exit(0 if success else 1)
```

## 五、验收命令汇总

```bash
# 完整自动化验收
python scripts/verify_frontend.py

# 单独执行各阶段
# 阶段1: 依赖检查
pip install -r requirements.txt && cd frontend && npm install

# 阶段2: 类型检查
cd frontend && npx tsc --noEmit

# 阶段3: 构建验证
cd frontend && npm run build

# 阶段4-5: 启动服务器并测试
python web_server.py &
curl http://127.0.0.1:8000/api/health

# 阶段6: 人工验收
python web_server.py
# 浏览器打开 http://localhost:8000
```

## 六、注意事项

1. **验收顺序** - 必须按阶段顺序执行，不可跳过
2. **失败处理** - 任何阶段失败立即停止，修复后重新开始
3. **环境要求** - 需要 Python 3.10+ 和 Node.js 18+
4. **端口占用** - 确保 8000 端口未被占用
5. **人工验收** - 阶段6必须由开发者亲自执行
