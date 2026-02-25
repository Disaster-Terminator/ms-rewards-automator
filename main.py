"""
RewardsCore - 主程序入口（向后兼容）

推荐使用 rscore 命令行工具：
  rscore --dev      # 开发模式
  rscore --user     # 用户模式
  rscore --help     # 查看帮助
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli import main

if __name__ == "__main__":
    main()
