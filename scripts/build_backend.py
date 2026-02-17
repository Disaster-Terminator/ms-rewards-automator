"""
MS Rewards Automator - Backend Build Script
用于将 Python 后端打包为独立可执行文件，供 Tauri Sidecar 使用
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SRC_TAURI_DIR = FRONTEND_DIR / "src-tauri"
BINARIES_DIR = SRC_TAURI_DIR / "binaries"

def get_target_triple():
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        if machine in ["amd64", "x86_64"]:
            return "x86_64-pc-windows-msvc"
        elif machine in ["arm64", "aarch64"]:
            return "aarch64-pc-windows-msvc"
    elif system == "darwin":
        if machine in ["arm64", "aarch64"]:
            return "aarch64-apple-darwin"
        else:
            return "x86_64-apple-darwin"
    elif system == "linux":
        if machine in ["arm64", "aarch64"]:
            return "aarch64-unknown-linux-gnu"
        else:
            return "x86_64-unknown-linux-gnu"

    raise RuntimeError(f"Unsupported platform: {system} {machine}")

def build_backend():
    target = get_target_triple()

    BINARIES_DIR.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        exe_name = f"backend-{target}.exe"
    else:
        exe_name = f"backend-{target}"

    output_path = BINARIES_DIR / exe_name

    print(f"Building backend for {target}...")
    print(f"Output: {output_path}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", f"backend-{target}",
        "--distpath", str(BINARIES_DIR),
        "--workpath", str(PROJECT_ROOT / "build" / "backend_build"),
        "--specpath", str(PROJECT_ROOT / "build"),
        str(PROJECT_ROOT / "web_server.py"),
    ]

    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "starlette.responses",
        "starlette.routing",
        "starlette.middleware",
        "starlette.middleware.cors",
        "starlette.staticfiles",
        "websockets",
        "websockets.legacy",
        "websockets.legacy.server",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    collect_data = ["playwright", "uvicorn", "starlette"]
    for data in collect_data:
        cmd.extend(["--collect-data", data])

    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print(f"Build failed with code {result.returncode}")
        sys.exit(1)

    print(f"Backend built successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    build_backend()
