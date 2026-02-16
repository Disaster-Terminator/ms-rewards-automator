#!/usr/bin/env python3
"""
前端自动化验收脚本
执行阶段1-5的自动化验收
"""

import subprocess
import sys
import json
import time
import os
from pathlib import Path

try:
    import requests
except ImportError:
    print("正在安装 requests...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests


class FrontendVerifier:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.server_process = None
        self.base_dir = Path(__file__).parent.parent
        
    def run_command(self, cmd, cwd=None):
        """运行命令并返回结果"""
        if cwd is None:
            cwd = self.base_dir
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    
    def check(self, name, condition, message=""):
        """记录检查结果"""
        if condition:
            print(f"  [PASS] {name}")
            self.passed += 1
        else:
            print(f"  [FAIL] {name}: {message}")
            self.failed += 1
        return condition
    
    def stage1_dependencies(self):
        """阶段1: 依赖检查"""
        print("\n[阶段1] 依赖检查")
        print("-" * 40)
        
        code, _, err = self.run_command(
            'python -c "import fastapi, uvicorn, websockets"'
        )
        self.check("Python 依赖 (fastapi, uvicorn, websockets)", code == 0, err.strip() if err else "")
        
        code, _, err = self.run_command(
            'python -c "import yaml, psutil"'
        )
        self.check("Python 依赖 (yaml, psutil)", code == 0, err.strip() if err else "")
        
        frontend_dir = self.base_dir / "frontend"
        node_modules = frontend_dir / "node_modules"
        
        if node_modules.exists():
            self.check("Node.js 依赖 (node_modules 存在)", True)
        else:
            print("  正在安装 Node.js 依赖...")
            code, _, err = self.run_command("npm install", cwd=frontend_dir)
            self.check("Node.js 依赖安装", code == 0, err.strip() if err else "")
        
        return self.failed == 0
    
    def stage2_typecheck(self):
        """阶段2: 类型检查"""
        print("\n[阶段2] 类型检查")
        print("-" * 40)
        
        frontend_dir = self.base_dir / "frontend"
        
        if not (frontend_dir / "node_modules").exists():
            print("  跳过: node_modules 不存在")
            return True
        
        code, out, err = self.run_command("npx tsc --noEmit", cwd=frontend_dir)
        
        if code == 0:
            self.check("TypeScript 类型检查", True)
        else:
            error_lines = err.strip().split('\n')[:5] if err else out.strip().split('\n')[:5]
            self.check("TypeScript 类型检查", False, '\n'.join(error_lines))
        
        return self.failed == 0
    
    def stage3_build(self):
        """阶段3: 构建验证"""
        print("\n[阶段3] 构建验证")
        print("-" * 40)
        
        frontend_dir = self.base_dir / "frontend"
        dist_dir = frontend_dir / "dist"
        
        if dist_dir.exists():
            import shutil
            shutil.rmtree(dist_dir)
        
        code, out, err = self.run_command("npm run build", cwd=frontend_dir)
        
        if code == 0:
            self.check("前端构建命令执行", True)
        else:
            error_lines = err.strip().split('\n')[:5] if err else out.strip().split('\n')[:5]
            self.check("前端构建命令执行", False, '\n'.join(error_lines))
            return False
        
        self.check("dist/index.html 存在", (dist_dir / "index.html").exists())
        self.check("dist/assets 目录存在", (dist_dir / "assets").exists())
        
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            js_files = list(assets_dir.glob("*.js"))
            css_files = list(assets_dir.glob("*.css"))
            self.check(f"JS 文件生成 ({len(js_files)} 个)", len(js_files) > 0)
            self.check(f"CSS 文件生成 ({len(css_files)} 个)", len(css_files) > 0)
        
        return self.failed == 0
    
    def stage4_backend(self):
        """阶段4: 后端 API 验证"""
        print("\n[阶段4] 后端 API 验证")
        print("-" * 40)
        
        self._start_server()
        if not self.server_process:
            self.check("服务器启动", False, "无法启动服务器进程")
            return False
        
        time.sleep(5)
        
        base_url = "http://127.0.0.1:8000"
        
        try:
            endpoints = [
                ("/api/health", ["overall", "system", "network"]),
                ("/api/status", ["is_running", "progress"]),
                ("/api/config", ["search", "browser"]),
                ("/api/dashboard", ["status", "health"]),
                ("/api/points", ["current_points", "points_gained_today"]),
            ]
            
            for endpoint, required_keys in endpoints:
                try:
                    resp = requests.get(f"{base_url}{endpoint}", timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        missing = [k for k in required_keys if k not in data]
                        self.check(
                            f"GET {endpoint}", 
                            len(missing) == 0,
                            f"Missing keys: {missing}" if missing else ""
                        )
                    else:
                        self.check(f"GET {endpoint}", False, f"Status: {resp.status_code}")
                except requests.exceptions.ConnectionError:
                    self.check(f"GET {endpoint}", False, "Connection refused")
                except Exception as e:
                    self.check(f"GET {endpoint}", False, str(e))
            
            try:
                resp = requests.get(base_url, timeout=10)
                self.check("前端页面可访问", "MS Rewards" in resp.text or "React" in resp.text)
            except Exception as e:
                self.check("前端页面可访问", False, str(e))
                
        finally:
            self._stop_server()
        
        return self.failed == 0
    
    def stage5_frontend(self):
        """阶段5: 前端功能验证"""
        print("\n[阶段5] 前端功能验证")
        print("-" * 40)
        
        self._start_server()
        if not self.server_process:
            self.check("服务器启动", False, "无法启动服务器进程")
            return False
        
        time.sleep(5)
        
        base_url = "http://127.0.0.1:8000"
        
        try:
            try:
                resp = requests.put(
                    f"{base_url}/api/config",
                    json={"search": {"desktop_count": 35}},
                    timeout=10
                )
                self.check("PUT /api/config (配置更新)", resp.status_code == 200)
            except Exception as e:
                self.check("PUT /api/config (配置更新)", False, str(e))
            
            try:
                resp = requests.get(f"{base_url}/api/logs/recent?lines=10", timeout=10)
                data = resp.json()
                self.check("GET /api/logs/recent (日志获取)", "logs" in data)
            except Exception as e:
                self.check("GET /api/logs/recent (日志获取)", False, str(e))
            
            try:
                resp = requests.get(f"{base_url}/api/history?days=7", timeout=10)
                data = resp.json()
                self.check("GET /api/history (历史记录)", "history" in data)
            except Exception as e:
                self.check("GET /api/history (历史记录)", False, str(e))
            
            try:
                resp = requests.post(
                    f"{base_url}/api/task/start",
                    json={"mode": "dev", "headless": True},
                    timeout=10
                )
                self.check("POST /api/task/start (启动任务)", 
                          resp.status_code in [200, 400])
            except Exception as e:
                self.check("POST /api/task/start (启动任务)", False, str(e))
            
            try:
                resp = requests.get(f"{base_url}/docs", timeout=10)
                self.check("GET /docs (API 文档)", resp.status_code == 200)
            except Exception as e:
                self.check("GET /docs (API 文档)", False, str(e))
                
        finally:
            self._stop_server()
        
        return self.failed == 0
    
    def _start_server(self):
        """启动服务器"""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.base_dir / "src")
        
        self.server_process = subprocess.Popen(
            [sys.executable, "web_server.py", "--host", "127.0.0.1", "--port", "8000"],
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
    
    def _stop_server(self):
        """停止服务器"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            except Exception:
                pass
            finally:
                self.server_process = None
    
    def run(self):
        """运行所有验收阶段"""
        print("=" * 60)
        print("MS Rewards Automator - 前端自动化验收")
        print("=" * 60)
        
        stages = [
            ("阶段1: 依赖检查", self.stage1_dependencies),
            ("阶段2: 类型检查", self.stage2_typecheck),
            ("阶段3: 构建验证", self.stage3_build),
            ("阶段4: 后端 API 验证", self.stage4_backend),
            ("阶段5: 前端功能验证", self.stage5_frontend),
        ]
        
        for stage_name, stage_func in stages:
            initial_failed = self.failed
            if not stage_func():
                print(f"\n[STOP] 验收在 {stage_name} 阶段失败")
                self._stop_server()
                self._print_summary()
                return False
            if self.failed > initial_failed:
                print(f"\n[WARN] {stage_name} 有失败项，继续执行...")
        
        self._print_summary()
        
        if self.failed == 0:
            print("\n[SUCCESS] 自动化验收通过!")
            print("请执行阶段6: 人工验收")
            print("  1. 运行: python web_server.py")
            print("  2. 浏览器打开: http://localhost:8000")
            return True
        else:
            print("\n[FAILED] 自动化验收失败，请修复问题后重试")
            return False
    
    def _print_summary(self):
        """打印验收摘要"""
        print("\n" + "=" * 60)
        print("验收摘要")
        print("=" * 60)
        print(f"  通过: {self.passed}")
        print(f"  失败: {self.failed}")
        print(f"  总计: {self.passed + self.failed}")
        print("=" * 60)


if __name__ == "__main__":
    verifier = FrontendVerifier()
    success = verifier.run()
    sys.exit(0 if success else 1)
