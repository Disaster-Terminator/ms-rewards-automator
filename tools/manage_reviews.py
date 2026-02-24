#!/usr/bin/env python3
"""
AI 审查评论管理工具 CLI

用法:
    python tools/manage_reviews.py fetch --owner OWNER --repo REPO --pr PR_NUMBER
    python tools/manage_reviews.py resolve --thread-id THREAD_ID --type RESOLUTION_TYPE [--reply "回复内容"]
    python tools/manage_reviews.py list [--status STATUS] [--source SOURCE] [--format FORMAT]
    python tools/manage_reviews.py overviews
    python tools/manage_reviews.py stats

环境变量:
    GITHUB_TOKEN: GitHub Personal Access Token (也可通过 .env 文件配置)
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.review import ReviewManager, ReviewResolver
from src.review.models import ReviewThreadState

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

MUST_FIX_TYPES = {"Bug", "Security", "Rule violation", "Reliability", "bug_risk", "security"}

TYPE_ABBREVIATIONS = {
    "Bug": "Bug",
    "Security": "Sec",
    "Rule violation": "Rule",
    "Reliability": "Rel",
    "Correctness": "Cor",
    "suggestion": "Sug",
    "bug_risk": "Bug",
    "performance": "Perf",
}


def load_env_file() -> None:
    """从 .env 文件加载环境变量"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value


def get_token() -> str:
    """从环境变量获取 GitHub Token"""
    load_env_file()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            json.dumps(
                {
                    "success": False,
                    "message": "错误: 未设置 GITHUB_TOKEN 环境变量，请在 .env 文件中配置",
                }
            )
        )
        sys.exit(1)
    return token


def get_db_path() -> Path:
    """获取数据库路径"""
    return Path(__file__).parent.parent / ".trae" / "data" / "review_threads.json"


def get_type_abbreviation(issue_type: str) -> str:
    """获取类型缩写"""
    for type_name, abbrev in TYPE_ABBREVIATIONS.items():
        if type_name.lower() in issue_type.lower():
            return abbrev
    return "Sug"


def is_must_fix(issue_type: str) -> bool:
    """判断是否为必须修复类型"""
    for type_name in MUST_FIX_TYPES:
        if type_name.lower() in issue_type.lower():
            return True
    return False


def print_threads_table(threads: list[ReviewThreadState], title: str = "审查评论") -> None:
    """使用 rich 打印线程表格"""
    if not RICH_AVAILABLE:
        print(
            json.dumps(
                {
                    "success": True,
                    "count": len(threads),
                    "threads": [
                        {
                            "id": t.id,
                            "source": t.source,
                            "local_status": t.local_status,
                            "is_resolved": t.is_resolved,
                            "file_path": t.file_path,
                            "line_number": t.line_number,
                            "enriched_context": t.enriched_context.model_dump()
                            if t.enriched_context
                            else None,
                        }
                        for t in threads
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    console = Console()

    table = Table(title=f"[bold blue]{title} ({len(threads)})[/bold blue]")

    table.add_column("ID", style="dim", width=12)
    table.add_column("Source", width=10)
    table.add_column("Status", width=10)
    table.add_column("Enriched", width=12)
    table.add_column("Location", width=30)

    for thread in threads:
        short_id = thread.id[:8] + "..." if len(thread.id) > 8 else thread.id

        status_display = thread.local_status
        if thread.is_resolved:
            status_display = "[green]resolved[/green]"
        elif thread.local_status == "pending":
            status_display = "[yellow]pending[/yellow]"

        enriched_display = ""
        row_style = None

        if thread.enriched_context:
            issue_type = thread.enriched_context.issue_type
            abbrev = get_type_abbreviation(issue_type)
            enriched_display = f"[green]✅ {abbrev}[/green]"

            if is_must_fix(issue_type):
                row_style = "red"
            else:
                row_style = "yellow"

        location = f"{thread.file_path}:{thread.line_number}" if thread.file_path else "-"

        if row_style == "red":
            table.add_row(
                short_id, thread.source, status_display, enriched_display, location, style="red"
            )
        elif row_style == "yellow":
            table.add_row(
                short_id, thread.source, status_display, enriched_display, location, style="yellow"
            )
        else:
            table.add_row(short_id, thread.source, status_display, enriched_display, location)

    console.print(table)


def cmd_fetch(args: argparse.Namespace) -> None:
    """执行 fetch 子命令"""
    resolver = ReviewResolver(token=get_token(), owner=args.owner, repo=args.repo)

    result = resolver.fetch_threads(args.pr)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_resolve(args: argparse.Namespace) -> None:
    """执行 resolve 子命令"""
    db_path = get_db_path()
    resolver = ReviewResolver(token=get_token(), owner=args.owner, repo=args.repo, db_path=db_path)

    result = resolver.resolve_thread(
        thread_id=args.thread_id, resolution_type=args.type, reply_text=args.reply
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_list(args: argparse.Namespace) -> None:
    """执行 list 子命令"""
    db_path = get_db_path()
    manager = ReviewManager(db_path)

    threads = manager.get_all_threads()

    if args.status:
        threads = [t for t in threads if t.local_status == args.status]

    if args.source:
        threads = [t for t in threads if t.source == args.source]

    if args.format == "table" and RICH_AVAILABLE:
        title = "待处理评论" if args.status == "pending" else "审查评论"
        print_threads_table(threads, title)
    else:
        result = {
            "success": True,
            "count": len(threads),
            "threads": [
                {
                    "id": t.id,
                    "source": t.source,
                    "local_status": t.local_status,
                    "is_resolved": t.is_resolved,
                    "file_path": t.file_path,
                    "line_number": t.line_number,
                    "primary_comment_body": t.primary_comment_body,
                    "comment_url": t.comment_url,
                    "enriched_context": t.enriched_context.model_dump()
                    if t.enriched_context
                    else None,
                }
                for t in threads
            ],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_overviews(args: argparse.Namespace) -> None:
    """执行 overviews 子命令 - 列出总览意见"""
    db_path = get_db_path()
    manager = ReviewManager(db_path)

    overviews = manager.get_all_overviews()
    issue_comment_overviews = manager.get_all_issue_comment_overviews()

    if args.format == "table" and RICH_AVAILABLE:
        console = Console()

        if overviews:
            table = Table(title="[bold blue]Review 级别总览意见[/bold blue]")
            table.add_column("ID", style="dim", width=12)
            table.add_column("Source", width=10)
            table.add_column("Status", width=12)
            table.add_column("Has Prompt", width=10)
            table.add_column("Feedback Count", width=12)

            for o in overviews:
                short_id = o.id[:8] + "..." if len(o.id) > 8 else o.id
                status_display = (
                    "[green]acknowledged[/green]"
                    if o.local_status == "acknowledged"
                    else "[yellow]pending[/yellow]"
                )
                table.add_row(
                    short_id,
                    o.source,
                    status_display,
                    "[green]Yes[/green]" if o.has_prompt_for_ai else "[dim]No[/dim]",
                    str(len(o.high_level_feedback)),
                )

            console.print(table)

        if issue_comment_overviews:
            table2 = Table(title="[bold blue]Issue Comment 级别总览意见[/bold blue]")
            table2.add_column("ID", style="dim", width=12)
            table2.add_column("Source", width=10)
            table2.add_column("User", width=20)

            for o in issue_comment_overviews:
                short_id = str(o.id)[:8] + "..." if len(str(o.id)) > 8 else str(o.id)
                table2.add_row(short_id, o.source, o.user_login or "-")

            console.print(table2)
    else:
        result = {
            "success": True,
            "overviews": [
                {
                    "id": o.id,
                    "source": o.source,
                    "local_status": o.local_status,
                    "has_prompt_for_ai": o.has_prompt_for_ai,
                    "high_level_feedback": o.high_level_feedback,
                    "prompt_overall_comments": o.prompt_overall_comments,
                }
                for o in overviews
            ],
            "issue_comment_overviews": [
                {
                    "id": o.id,
                    "source": o.source,
                    "user_login": o.user_login,
                }
                for o in issue_comment_overviews
            ],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_acknowledge(args: argparse.Namespace) -> None:
    """执行 acknowledge 子命令 - 确认总览意见"""
    db_path = get_db_path()
    manager = ReviewManager(db_path)

    if args.all:
        acknowledged_ids = manager.acknowledge_all_overviews()
        result = {
            "success": True,
            "message": f"已确认 {len(acknowledged_ids)} 个总览意见",
            "acknowledged_ids": acknowledged_ids,
        }
    elif args.id:
        success = manager.acknowledge_overview(args.id)
        if success:
            result = {
                "success": True,
                "message": f"总览意见 {args.id} 已确认",
                "acknowledged_ids": [args.id],
            }
        else:
            result = {
                "success": False,
                "message": f"未找到总览意见 {args.id}",
                "acknowledged_ids": [],
            }
    else:
        result = {
            "success": False,
            "message": "请指定 --id 或 --all",
            "acknowledged_ids": [],
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_stats(args: argparse.Namespace) -> None:
    """执行 stats 子命令"""
    db_path = get_db_path()
    manager = ReviewManager(db_path)

    stats = manager.get_statistics()

    if args.format == "table" and RICH_AVAILABLE:
        console = Console()

        panel = Panel(
            f"[bold]Total:[/bold] {stats.get('total', 0)}\n"
            f"[bold]By Status:[/bold] {stats.get('by_status', {})}\n"
            f"[bold]By Source:[/bold] {stats.get('by_source', {})}\n"
            f"[bold]Overviews:[/bold] {stats.get('overviews_count', 0)}",
            title="[bold blue]统计信息[/bold blue]",
        )
        console.print(panel)
    else:
        result = {"success": True, "statistics": stats}
        print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI 审查评论管理工具", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    parser_fetch = subparsers.add_parser("fetch", help="获取 PR 的评论线程")
    parser_fetch.add_argument("--owner", required=True, help="仓库所有者")
    parser_fetch.add_argument("--repo", required=True, help="仓库名称")
    parser_fetch.add_argument("--pr", type=int, required=True, help="PR 编号")
    parser_fetch.set_defaults(func=cmd_fetch)

    parser_resolve = subparsers.add_parser("resolve", help="解决评论线程")
    parser_resolve.add_argument("--owner", required=True, help="仓库所有者")
    parser_resolve.add_argument("--repo", required=True, help="仓库名称")
    parser_resolve.add_argument("--thread-id", required=True, help="Thread ID")
    parser_resolve.add_argument(
        "--type",
        required=True,
        choices=["code_fixed", "adopted", "rejected", "false_positive", "outdated"],
        help="解决依据类型",
    )
    parser_resolve.add_argument("--reply", help="可选的回复内容")
    parser_resolve.set_defaults(func=cmd_resolve)

    parser_list = subparsers.add_parser("list", help="列出评论线程")
    parser_list.add_argument(
        "--status", choices=["pending", "resolved", "ignored"], help="按状态过滤"
    )
    parser_list.add_argument("--source", choices=["Sourcery", "Qodo", "Copilot"], help="按来源过滤")
    parser_list.add_argument(
        "--format", choices=["table", "json"], default="table", help="输出格式 (默认: table)"
    )
    parser_list.set_defaults(func=cmd_list)

    parser_overviews = subparsers.add_parser("overviews", help="列出总览意见")
    parser_overviews.add_argument(
        "--format", choices=["table", "json"], default="table", help="输出格式 (默认: table)"
    )
    parser_overviews.set_defaults(func=cmd_overviews)

    parser_acknowledge = subparsers.add_parser("acknowledge", help="确认总览意见")
    parser_acknowledge.add_argument("--id", help="总览意见 ID")
    parser_acknowledge.add_argument("--all", action="store_true", help="确认所有总览意见")
    parser_acknowledge.set_defaults(func=cmd_acknowledge)

    parser_stats = subparsers.add_parser("stats", help="显示统计信息")
    parser_stats.add_argument(
        "--format", choices=["table", "json"], default="table", help="输出格式 (默认: table)"
    )
    parser_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print(json.dumps({"success": False, "message": "操作已取消"}))
        sys.exit(130)
    except Exception as e:
        print(json.dumps({"success": False, "message": f"错误: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
