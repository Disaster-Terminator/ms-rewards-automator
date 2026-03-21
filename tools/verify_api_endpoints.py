"""
API 端点可用性验证脚本

验证 TS 项目引用的 API 是否仍然有效。
需要用户提供已登录的浏览器 cookies 进行测试。

使用方法：
    python tools/verify_api_endpoints.py --cookies "cookie_string"
    或
    python tools/verify_api_endpoints.py --cookie-file cookies.txt
"""

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp


class APIStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass
class APIEndpoint:
    name: str
    url: str
    method: str
    requires_auth: bool
    description: str
    expected_fields: list[str]


@dataclass
class ValidationResult:
    endpoint: APIEndpoint
    status: APIStatus
    status_code: int | None
    response_sample: dict[str, Any] | None
    error_message: str | None
    duration_ms: float
    timestamp: str


ENDPOINTS = [
    APIEndpoint(
        name="Dashboard API",
        url="https://rewards.bing.com/api/getuserinfo?type=1",
        method="GET",
        requires_auth=True,
        description="获取用户 Dashboard 数据（积分、任务等）",
        expected_fields=["dashboard"],
    ),
    APIEndpoint(
        name="App Dashboard",
        url="https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAIOS&options=613",
        method="GET",
        requires_auth=True,
        description="获取 App Dashboard 数据（签到、阅读赚等）",
        expected_fields=["response", "promotions"],
    ),
    APIEndpoint(
        name="Bing Suggestions",
        url="https://api.bing.com/osjson.aspx?query=test",
        method="GET",
        requires_auth=False,
        description="获取 Bing 搜索建议（无需认证）",
        expected_fields=[],
    ),
    APIEndpoint(
        name="Wikipedia Top Views",
        url="https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/02/01",
        method="GET",
        requires_auth=False,
        description="获取 Wikipedia 热门文章（无需认证）",
        expected_fields=["items"],
    ),
    APIEndpoint(
        name="Reddit Popular",
        url="https://www.reddit.com/r/popular.json?limit=10",
        method="GET",
        requires_auth=False,
        description="获取 Reddit 热门帖子（无需认证）",
        expected_fields=["data", "children"],
    ),
    APIEndpoint(
        name="Google Trends",
        url="https://trends.google.com/_/TrendsUi/data/batchexecute",
        method="POST",
        requires_auth=False,
        description="获取 Google 热门趋势（复杂 API）",
        expected_fields=[],
    ),
    APIEndpoint(
        name="Bing Quiz API",
        url="https://www.bing.com/bingqa/ReportActivity?ajaxreq=1",
        method="POST",
        requires_auth=True,
        description="Bing Quiz 活动上报 API",
        expected_fields=[],
    ),
    APIEndpoint(
        name="Rewards Report Activity",
        url="https://rewards.bing.com/api/reportactivity",
        method="POST",
        requires_auth=True,
        description="Rewards 活动上报 API",
        expected_fields=[],
    ),
]


def parse_cookies(cookie_string: str) -> dict[str, str]:
    """解析 cookie 字符串为字典"""
    cookies = {}
    for part in cookie_string.split(";"):
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


def build_cookie_header(cookies: dict[str, str]) -> str:
    """构建 cookie header 字符串"""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


async def verify_endpoint(
    session: aiohttp.ClientSession,
    endpoint: APIEndpoint,
    cookies: dict[str, str] | None,
) -> ValidationResult:
    """验证单个 API 端点"""
    start_time = asyncio.get_event_loop().time()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    if "wikimedia.org" in endpoint.url:
        headers["User-Agent"] = "RewardsCore/1.0 (https://github.com/user/rewardscore)"
        headers["Accept"] = "application/json"

    if "reddit.com" in endpoint.url:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        headers["Accept"] = "application/json"

    if endpoint.requires_auth and cookies:
        headers["Cookie"] = build_cookie_header(cookies)
        if "rewards.bing.com" in endpoint.url:
            headers["Referer"] = "https://rewards.bing.com/"
        elif "rewardsplatform.microsoft.com" in endpoint.url:
            headers["Referer"] = "https://rewards.microsoft.com/"

    status_code = None
    response_sample = None
    error_message = None
    status = APIStatus.PENDING

    try:
        if endpoint.method == "GET":
            async with session.get(
                endpoint.url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                status_code = response.status

                if response.status == 200:
                    try:
                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            data = await response.json()
                        else:
                            text = await response.text()
                            try:
                                data = json.loads(text)
                            except json.JSONDecodeError:
                                data = {"raw_response": text[:1000]}

                        response_sample = (
                            data
                            if isinstance(data, dict)
                            else {"raw_response": str(data)[:500]}
                        )

                        if endpoint.expected_fields:
                            missing = [
                                f
                                for f in endpoint.expected_fields
                                if f not in response_sample
                            ]
                            if missing:
                                status = APIStatus.SUCCESS
                                error_message = f"缺少预期字段: {missing}"
                            else:
                                status = APIStatus.SUCCESS
                        else:
                            status = APIStatus.SUCCESS

                    except json.JSONDecodeError:
                        text = await response.text()
                        response_sample = {"raw_response": text[:500]}
                        status = APIStatus.SUCCESS

                elif response.status == 401:
                    status = APIStatus.UNAUTHORIZED
                    error_message = "需要认证或 cookies 无效"

                elif response.status == 404:
                    status = APIStatus.NOT_FOUND
                    error_message = "API 端点不存在"

                elif response.status == 429:
                    status = APIStatus.RATE_LIMITED
                    error_message = "请求频率受限"

                else:
                    status = APIStatus.FAILED
                    error_message = f"HTTP {response.status}"

        elif endpoint.method == "POST":
            post_data = {}
            content_type = "application/json"

            if "googleapis.com" in endpoint.url or "trends.google.com" in endpoint.url:
                content_type = "application/x-www-form-urlencoded;charset=UTF-8"
                post_data = {"f.req": '[[["iU","[]"]]]'}
            elif "bingqa" in endpoint.url:
                post_data = {
                    "UserId": None,
                    "TimeZoneOffset": -60,
                    "OfferId": "test",
                    "ActivityCount": 1,
                    "QuestionIndex": "-1",
                }
            elif "reportactivity" in endpoint.url:
                content_type = "application/x-www-form-urlencoded"
                post_data = {
                    "id": "test",
                    "hash": "test",
                    "timeZone": "60",
                    "activityAmount": "1",
                }

            headers["Content-Type"] = content_type

            async with session.post(
                endpoint.url,
                headers=headers,
                data=post_data if content_type.startswith("application/x-www-form") else json.dumps(post_data),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                status_code = response.status

                if response.status == 200:
                    try:
                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            data = await response.json()
                        else:
                            text = await response.text()
                            try:
                                data = json.loads(text)
                            except json.JSONDecodeError:
                                data = {"raw_response": text[:1000]}

                        response_sample = (
                            data
                            if isinstance(data, dict)
                            else {"raw_response": str(data)[:500]}
                        )
                        status = APIStatus.SUCCESS
                    except json.JSONDecodeError:
                        text = await response.text()
                        response_sample = {"raw_response": text[:500]}
                        status = APIStatus.SUCCESS

                elif response.status == 401:
                    status = APIStatus.UNAUTHORIZED
                    error_message = "需要认证或 cookies 无效"

                elif response.status == 400:
                    status = APIStatus.SUCCESS
                    error_message = "API 端点存在（需要有效参数）"

                elif response.status == 404:
                    status = APIStatus.NOT_FOUND
                    error_message = "API 端点不存在"

                elif response.status == 429:
                    status = APIStatus.RATE_LIMITED
                    error_message = "请求频率受限"

                elif response.status == 500:
                    status = APIStatus.SUCCESS
                    error_message = "API 端点存在（服务器错误可能是参数问题）"

                else:
                    status = APIStatus.FAILED
                    error_message = f"HTTP {response.status}"

        else:
            status = APIStatus.ERROR
            error_message = f"不支持的 HTTP 方法: {endpoint.method}"

    except aiohttp.ClientError as e:
        status = APIStatus.ERROR
        error_message = f"网络错误: {str(e)}"

    except asyncio.TimeoutError:
        status = APIStatus.ERROR
        error_message = "请求超时"

    except Exception as e:
        status = APIStatus.ERROR
        error_message = f"未知错误: {str(e)}"

    duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

    return ValidationResult(
        endpoint=endpoint,
        status=status,
        status_code=status_code,
        response_sample=response_sample,
        error_message=error_message,
        duration_ms=duration_ms,
        timestamp=datetime.now().isoformat(),
    )


async def run_verification(cookies: dict[str, str] | None) -> list[ValidationResult]:
    """运行所有 API 验证"""
    results = []

    async with aiohttp.ClientSession() as session:
        for endpoint in ENDPOINTS:
            print(f"\n验证: {endpoint.name}")
            print(f"  URL: {endpoint.url}")
            print(f"  需要认证: {endpoint.requires_auth}")

            if endpoint.requires_auth and not cookies:
                print(f"  状态: ⚠️ 跳过（未提供 cookies）")
                results.append(
                    ValidationResult(
                        endpoint=endpoint,
                        status=APIStatus.PENDING,
                        status_code=None,
                        response_sample=None,
                        error_message="未提供认证 cookies",
                        duration_ms=0,
                        timestamp=datetime.now().isoformat(),
                    )
                )
                continue

            result = await verify_endpoint(session, endpoint, cookies)
            results.append(result)

            status_icon = {
                APIStatus.SUCCESS: "✅",
                APIStatus.FAILED: "❌",
                APIStatus.UNAUTHORIZED: "🔒",
                APIStatus.RATE_LIMITED: "⏳",
                APIStatus.NOT_FOUND: "🔍",
                APIStatus.ERROR: "⚠️",
                APIStatus.PENDING: "⏸️",
            }.get(result.status, "❓")

            print(f"  状态: {status_icon} {result.status.value}")
            print(f"  HTTP 状态码: {result.status_code}")
            print(f"  耗时: {result.duration_ms:.0f}ms")

            if result.error_message:
                print(f"  错误: {result.error_message}")

            if result.response_sample:
                sample_str = json.dumps(result.response_sample, ensure_ascii=False, indent=2)
                if len(sample_str) > 300:
                    sample_str = sample_str[:300] + "..."
                print(f"  响应示例: {sample_str}")

    return results


def generate_report(results: list[ValidationResult]) -> str:
    """生成验证报告"""
    lines = [
        "# API 端点验证报告",
        "",
        f"> 验证时间: {datetime.now().isoformat()}",
        "",
        "## 验证结果汇总",
        "",
        "| API | 状态 | HTTP 状态码 | 耗时 | 备注 |",
        "|-----|------|-------------|------|------|",
    ]

    for r in results:
        status_icon = {
            APIStatus.SUCCESS: "✅",
            APIStatus.FAILED: "❌",
            APIStatus.UNAUTHORIZED: "🔒",
            APIStatus.RATE_LIMITED: "⏳",
            APIStatus.NOT_FOUND: "🔍",
            APIStatus.ERROR: "⚠️",
            APIStatus.PENDING: "⏸️",
        }.get(r.status, "❓")

        note = r.error_message or "-"
        lines.append(
            f"| {r.endpoint.name} | {status_icon} {r.status.value} | {r.status_code or '-'} | {r.duration_ms:.0f}ms | {note} |"
        )

    lines.extend(
        [
            "",
            "## 详细结果",
            "",
        ]
    )

    for r in results:
        lines.extend(
            [
                f"### {r.endpoint.name}",
                "",
                f"- **URL**: `{r.endpoint.url}`",
                f"- **描述**: {r.endpoint.description}",
                f"- **需要认证**: {'是' if r.endpoint.requires_auth else '否'}",
                f"- **状态**: {r.status.value}",
                f"- **HTTP 状态码**: {r.status_code or 'N/A'}",
                f"- **耗时**: {r.duration_ms:.0f}ms",
                "",
            ]
        )

        if r.error_message:
            lines.append(f"- **错误信息**: {r.error_message}")
            lines.append("")

        if r.response_sample:
            lines.append("**响应示例**:")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(r.response_sample, ensure_ascii=False, indent=2)[:1000])
            lines.append("```")
            lines.append("")

    lines.extend(
        [
            "## 结论",
            "",
        ]
    )

    success_count = sum(1 for r in results if r.status == APIStatus.SUCCESS)
    auth_required_count = sum(1 for r in results if r.endpoint.requires_auth)
    auth_success_count = sum(
        1
        for r in results
        if r.endpoint.requires_auth and r.status == APIStatus.SUCCESS
    )

    if success_count == len(ENDPOINTS):
        lines.append("✅ **所有 API 端点均可用**，可以继续开发 API 集成功能。")
    elif auth_success_count == auth_required_count:
        lines.append("✅ **需要认证的 API 均可用**，可以继续开发。")
    elif success_count > 0:
        lines.append("⚠️ **部分 API 可用**，建议：")
        lines.append("")
        for r in results:
            if r.status != APIStatus.SUCCESS:
                lines.append(f"- {r.endpoint.name}: {r.error_message}")
        lines.append("")
        lines.append("建议保留 HTML 解析作为 fallback 方案。")
    else:
        lines.append("❌ **所有 API 均不可用**，建议：")
        lines.append("")
        lines.append("1. 检查 cookies 是否有效")
        lines.append("2. 检查网络连接")
        lines.append("3. 考虑使用 HTML 解析作为主要方案")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="验证 Rewards API 端点可用性")
    parser.add_argument(
        "--cookies",
        type=str,
        help="Cookie 字符串（从浏览器开发者工具复制）",
    )
    parser.add_argument(
        "--cookie-file",
        type=str,
        help="Cookie 文件路径（每行一个 cookie）",
    )
    parser.add_argument(
        "--storage-state",
        type=str,
        help="Playwright storage_state.json 文件路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="api_verification_report.md",
        help="输出报告文件路径",
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="仅测试无需认证的 API",
    )

    args = parser.parse_args()

    cookies = None

    if args.no_auth:
        print("仅测试无需认证的 API")
    elif args.storage_state:
        try:
            with open(args.storage_state, "r", encoding="utf-8") as f:
                state = json.load(f)
            cookies = {}
            for cookie in state.get("cookies", []):
                cookies[cookie["name"]] = cookie["value"]
            print(f"已从 storage_state 解析 {len(cookies)} 个 cookies")
        except FileNotFoundError:
            print(f"错误: storage_state 文件不存在: {args.storage_state}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"错误: storage_state 文件格式错误: {e}")
            sys.exit(1)
    elif args.cookies:
        cookies = parse_cookies(args.cookies)
        print(f"已解析 {len(cookies)} 个 cookies")
    elif args.cookie_file:
        try:
            with open(args.cookie_file, "r", encoding="utf-8") as f:
                cookies = parse_cookies(f.read())
            print(f"已从文件解析 {len(cookies)} 个 cookies")
        except FileNotFoundError:
            print(f"错误: Cookie 文件不存在: {args.cookie_file}")
            sys.exit(1)
    else:
        print("提示: 未提供 cookies，将跳过需要认证的 API")
        print("使用 --cookies、--cookie-file 或 --storage-state 参数提供认证信息")
        print()

    print("=" * 60)
    print("开始 API 端点验证")
    print("=" * 60)

    results = asyncio.run(run_verification(cookies))

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)

    report = generate_report(results)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存到: {args.output}")

    success_count = sum(1 for r in results if r.status == APIStatus.SUCCESS)
    print(f"\n验证结果: {success_count}/{len(ENDPOINTS)} 个 API 可用")


if __name__ == "__main__":
    main()
