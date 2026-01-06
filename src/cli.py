#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GLM Coding Plan 配额查询 CLI 工具
支持美观的终端UI展示配额使用情况
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_auth_info():
    """从环境变量或settings.json获取认证信息"""
    base_url = os.environ.get('ANTHROPIC_BASE_URL', '')
    auth_token = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')

    if not auth_token or not base_url:
        home_dir = Path.home()
        settings_file = home_dir / '.claude' / 'settings.json'

        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    env_vars = settings.get('env', {})

                    if not auth_token:
                        auth_token = env_vars.get('ANTHROPIC_AUTH_TOKEN', '')
                    if not base_url:
                        base_url = env_vars.get('ANTHROPIC_BASE_URL', '')
            except Exception:
                pass

    if not auth_token:
        return None, None

    if not base_url:
        base_url = 'https://open.bigmodel.cn/api/anthropic'

    return base_url, auth_token


def determine_platform(base_url):
    """根据base_url确定平台"""
    if 'api.z.ai' in base_url:
        return 'ZAI'
    elif 'open.bigmodel.cn' in base_url or 'dev.bigmodel.cn' in base_url:
        return 'ZHIPU'
    else:
        return 'UNKNOWN'


def make_api_request(url, auth_token, query_params=None):
    """发起API请求"""
    full_url = url
    if query_params:
        full_url += f"?{urllib.parse.urlencode(query_params)}"

    req = urllib.request.Request(full_url)
    req.add_header('Authorization', auth_token)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.HTTPError as e:
        return {'error': f'HTTP {e.code}', 'message': e.read().decode()}
    except Exception as e:
        return {'error': 'Error', 'message': str(e)}


def process_quota_limit(data):
    """处理配额限制数据"""
    if not data or not isinstance(data, dict):
        return []

    limits = data.get('limits', [])
    processed = []

    for item in limits:
        if item.get('type') == 'TOKENS_LIMIT':
            processed.append({
                'type': 'Token使用(5 Hour)',
                'period': '5小时窗口',
                'percentage': item.get('percentage', 0)
            })
        elif item.get('type') == 'TIME_LIMIT':
            processed.append({
                'type': 'MCP使用(1 Month)',
                'period': '1个月',
                'percentage': item.get('percentage', 0),
                'current': item.get('currentValue', 0),
                'total': item.get('usage', 0)
            })

    return processed


def get_progress_color(percentage):
    """根据使用率返回颜色"""
    if percentage >= 90:
        return 'red'
    elif percentage >= 70:
        return 'yellow'
    return 'green'


def render_output(data):
    """渲染输出"""
    console = Console()

    platform = data.get('platform', 'UNKNOWN')
    platform_name = 'ZHIPU (智谱)' if platform == 'ZHIPU' else platform

    # 标题
    console.print()
    title = Text()
    title.append("GLM Coding Plan ", style="bold cyan")
    title.append("使用统计", style="bold white")
    console.print(Align.center(Panel(title, border_style="cyan", box=box.ROUNDED)))
    console.print()

    # 平台信息
    platform_panel = Panel(
        f"[bold]平台:[/bold] {platform_name}\n"
        f"[bold]查询时间:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        title="[yellow]信息[/yellow]",
        border_style="yellow",
        box=box.ROUNDED
    )
    console.print(platform_panel)
    console.print()

    # 模型使用
    model_data = data.get('model_usage', {})
    if model_data and 'error' not in model_data:
        total_usage = model_data.get('totalUsage', {})
        total_calls = total_usage.get('totalModelCallCount', 0)
        total_tokens = total_usage.get('totalTokensUsage', 0)

        model_table = Table(title="[green]模型使用[/green]", show_header=True,
                           header_style="bold magenta", border_style="green", box=box.ROUNDED)
        model_table.add_column("指标", style="cyan")
        model_table.add_column("数值", justify="right")

        model_table.add_row("总调用次数", f"{total_calls:,}")
        model_table.add_row("总Token使用", f"{total_tokens:,}")

        x_times = model_data.get('x_time', [])
        call_counts = model_data.get('modelCallCount', [])

        if x_times and call_counts:
            max_idx = max(range(len(call_counts)), key=lambda i: call_counts[i] if call_counts[i] else 0)
            min_idx = min(range(len(call_counts)), key=lambda i: call_counts[i] if call_counts[i] else float('inf'))

            peak_time = x_times[max_idx]
            peak_calls = call_counts[max_idx] or 0
            low_time = x_times[min_idx]
            low_calls = call_counts[min_idx] or 0

            model_table.add_row("高峰时段", f"{peak_time} ({peak_calls:,}次)")
            model_table.add_row("低谷时段", f"{low_time} ({low_calls:,}次)")

        console.print(model_table)
        console.print()

    # 工具使用
    tool_data = data.get('tool_usage', {})
    if tool_data and 'error' not in tool_data:
        total_usage = tool_data.get('totalUsage', {})

        tool_table = Table(title="[blue]工具使用[/blue]", show_header=True,
                          header_style="bold magenta", border_style="blue", box=box.ROUNDED)
        tool_table.add_column("工具", style="cyan")
        tool_table.add_column("使用次数", justify="right")

        tool_details = total_usage.get('toolDetails', [])
        for tool in tool_details:
            model_name = tool.get('modelName', 'unknown')
            count = tool.get('totalUsageCount', 0)
            display_name = {
                'search-prime': '网络搜索',
                'web-reader': '网页阅读',
                'zread': 'ZRead'
            }.get(model_name, model_name)
            tool_table.add_row(display_name, f"{count:,}")

        tool_table.add_row("---", "---")
        tool_table.add_row("[bold]总计[/bold]", f"[bold]{total_usage.get('totalSearchMcpCount', 0):,}[/bold]")

        console.print(tool_table)
        console.print()

    # 配额状态
    quota_list = data.get('quota_limits', [])
    if quota_list:
        quota_table = Table(title="[yellow]配额状态[/yellow]", show_header=True,
                           header_style="bold magenta", border_style="yellow", box=box.ROUNDED)
        quota_table.add_column("类型")
        quota_table.add_column("周期")
        quota_table.add_column("使用率", justify="right")
        quota_table.add_column("进度", justify="left")

        for item in quota_list:
            percentage = item.get('percentage', 0)
            color = get_progress_color(percentage)
            item_type = item.get('type', '')
            period = item.get('period', '')

            bar_width = 20
            filled = int(bar_width * percentage / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            quota_table.add_row(
                item_type,
                period,
                f"[{color}]{percentage}%[/{color}]",
                f"[{color}]{bar}[/{color}]"
            )

            if item.get('current') is not None:
                quota_table.add_row("", "", f"  {item.get('current'):,} / {item.get('total'):,}", "")

        console.print(quota_table)


def main():
    """主函数"""
    base_url, auth_token = get_auth_info()

    if not auth_token:
        print("[错误] 未找到 API 配置")
        print("\n请确保 Claude Code 已正确配置，或在 ~/.claude/settings.json 中设置:")
        print('  {"env": {"ANTHROPIC_AUTH_TOKEN": "your-token", "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic"}}')
        return 1

    platform = determine_platform(base_url)

    # 确定API域名
    if 'api.z.ai' in base_url:
        base_domain = 'https://api.z.ai'
    elif 'open.bigmodel.cn' in base_url:
        base_domain = 'https://open.bigmodel.cn'
    elif 'dev.bigmodel.cn' in base_url:
        base_domain = 'https://dev.bigmodel.cn'
    else:
        base_domain = base_url.split('/api/')[0]

    model_usage_url = f"{base_domain}/api/monitor/usage/model-usage"
    tool_usage_url = f"{base_domain}/api/monitor/usage/tool-usage"
    quota_limit_url = f"{base_domain}/api/monitor/usage/quota/limit"

    # 计算时间范围
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day - 1, now.hour, 0, 0)
    end_date = datetime(now.year, now.month, now.day, now.hour, 59, 59)

    format_datetime = lambda d: d.strftime('%Y-%m-%d %H:%M:%S')
    query_params = {
        'startTime': format_datetime(start_date),
        'endTime': format_datetime(end_date)
    }

    data = {'platform': platform}

    if RICH_AVAILABLE:
        console = Console()
        with console.status("[bold cyan]正在获取配额数据...[/bold cyan]") as status:
            status.update("[cyan]获取模型使用数据...[/cyan]")
            model_resp = make_api_request(model_usage_url, auth_token, query_params)
            data['model_usage'] = model_resp.get('data', model_resp)

            status.update("[cyan]获取工具使用数据...[/cyan]")
            tool_resp = make_api_request(tool_usage_url, auth_token, query_params)
            data['tool_usage'] = tool_resp.get('data', tool_resp)

            status.update("[cyan]获取配额限制...[/cyan]")
            quota_raw = make_api_request(quota_limit_url, auth_token)
            data['quota_limits'] = process_quota_limit(quota_raw.get('data', quota_raw))
    else:
        print("正在获取配额数据...")
        data['model_usage'] = make_api_request(model_usage_url, auth_token, query_params).get('data', {})
        data['tool_usage'] = make_api_request(tool_usage_url, auth_token, query_params).get('data', {})
        quota_raw = make_api_request(quota_limit_url, auth_token)
        data['quota_limits'] = process_quota_limit(quota_raw.get('data', quota_raw))

    print("\n" * 2)
    if RICH_AVAILABLE:
        render_output(data)
    else:
        print("请安装 rich 库以获得更好的显示效果: pip install rich")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
