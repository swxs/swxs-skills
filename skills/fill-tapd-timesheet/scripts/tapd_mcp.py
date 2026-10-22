#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""TAPD 工时管理脚本 - 支持查询、分析、填写工时。

用法:
  # 分析缺失工时
  python3 tapd_mcp.py analyze --start 2026-06-01 --end 2026-07-14

  # 查找任务
  python3 tapd_mcp.py find-task --story-id 1157942251001099170

  # 创建任务
  python3 tapd_mcp.py create-task --story-id STORY_ID --name "任务名"

  # 填写工时（单条）
  python3 tapd_mcp.py fill --task-id TASK_ID --date 2026-06-29 --hours 8

  # 批量填写（交互确认）
  python3 tapd_mcp.py batch-fill --task-id TASK_ID --start 2026-06-01 --end 2026-07-14
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, timedelta

# ---- 配置 ----
API_BASE_URL = "https://api.tapd.cn"
TAPD_BASE_URL = "https://www.tapd.cn"
DEFAULT_WS = "57942251"
DEFAULT_OWNER = "居晓仁"


def tapd_env() -> dict:
    token = os.environ.get("SWXSSKILL_TAPD_ACCESS_TOKEN", "").strip()
    if not token:
        print("缺少环境变量 SWXSSKILL_TAPD_ACCESS_TOKEN", file=sys.stderr)
        sys.exit(1)
    return {
        "TAPD_ACCESS_TOKEN": token,
        "TAPD_API_BASE_URL": API_BASE_URL,
        "TAPD_BASE_URL": TAPD_BASE_URL,
        "PATH": "/home/swxs/.local/bin:/usr/local/bin:/usr/bin:/bin",
    }


def mcp_call(tool_name: str, arguments: dict) -> dict | None:
    """单次 MCP 调用，返回解析后的 data 部分"""
    proc = subprocess.Popen(
        ["uvx", "mcp-server-tapd"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=tapd_env(),
        text=True,
    )
    try:
        proc.stdin.write(
            json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "tapd_mcp", "version": "1"}}
            }) + "\n"
        )
        proc.stdin.flush()
        time.sleep(1.5)
        proc.stdout.readline()
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()
        time.sleep(0.5)
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}}) + "\n")
        proc.stdin.flush()
        time.sleep(5)
        proc.stdin.close()
        out = proc.stdout.read()
    finally:
        proc.terminate()

    for line in out.strip().split("\n"):
        try:
            d = json.loads(line)
            if "result" in d:
                for c in d["result"].get("content", []):
                    if c.get("type") == "text":
                        parsed = json.loads(c["text"])
                        # 有些 API 返回的 data 字段是 JSON 字符串，需要二次解析
                        if isinstance(parsed.get("data"), str):
                            try:
                                parsed["data"] = json.loads(parsed["data"])
                                # data 里可能还有嵌套
                                if isinstance(parsed["data"], dict) and isinstance(parsed["data"].get("data"), str):
                                    parsed["data"]["data"] = json.loads(parsed["data"]["data"])
                            except json.JSONDecodeError:
                                pass
                        return parsed
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def get_workdays(start: str, end: str) -> list[str]:
    """返回日期范围内的所有工作日 (YYYY-MM-DD)"""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    result = []
    d = s
    while d <= e:
        if d.weekday() < 5:  # Mon-Fri
            result.append(d.isoformat())
        d += timedelta(days=1)
    return result


# ---- 子命令 ----

def cmd_analyze(args):
    """分析缺失工时"""
    target_dates = get_workdays(args.start, args.end)
    workspace_id = args.workspace or DEFAULT_WS

    result = mcp_call("get_timesheets", {
        "workspace_id": workspace_id,
        "options": {
            "owner": args.owner or DEFAULT_OWNER,
            "spentdate": f"{args.start}~{args.end}",
            "limit": 100,
        }
    })

    filled_dates = {}
    if result and result.get("data"):
        for item in result["data"]:
            t = item.get("Timesheet", item)
            d = t.get("spentdate", "")
            h = int(t.get("timespent", 0))
            filled_dates[d] = filled_dates.get(d, 0) + h

    missing = []
    partial = []
    for d in target_dates:
        cur = filled_dates.get(d, 0)
        if cur < 8:
            entry = {"date": d, "current": cur, "need": 8 - cur}
            if cur > 0:
                partial.append(entry)
            else:
                missing.append(entry)

    if args.json:
        print(json.dumps({
            "total_workdays": len(target_dates),
            "filled": len([d for d in target_dates if filled_dates.get(d, 0) >= 8]),
            "missing": missing,
            "partial": partial,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"日期范围: {args.start} ~ {args.end}")
        print(f"工作日: {len(target_dates)} 天")
        print(f"已填满 8h: {len(target_dates) - len(missing) - len(partial)} 天")
        if missing:
            print(f"\n完全缺失 ({len(missing)} 天):")
            for e in missing:
                wd = date.fromisoformat(e["date"]).strftime("%a")
                print(f"  {e['date']} ({wd}) → 需补 {e['need']}h")
        if partial:
            print(f"\n部分缺失 ({len(partial)} 天):")
            for e in partial:
                wd = date.fromisoformat(e["date"]).strftime("%a")
                print(f"  {e['date']} ({wd}) 现有 {e['current']}h → 需补 {e['need']}h")


def cmd_find_task(args):
    """查找 TAPD 任务"""
    workspace_id = args.workspace or DEFAULT_WS

    opts = {"entity_type": "tasks", "limit": 99}
    if args.story_id:
        opts["story_id"] = args.story_id
    if args.owner:
        opts["owner"] = args.owner
    if args.name:
        opts["name"] = args.name

    result = mcp_call("get_stories_or_tasks", {"workspace_id": workspace_id, "options": opts})

    if not result or not result.get("data"):
        print("未找到匹配的任务")
        return []

    tasks = []
    for item in result["data"]:
        t = item.get("Task", item)
        if args.json:
            tasks.append({"id": t.get("id"), "name": t.get("name"), "status": t.get("status"), "story_id": t.get("story_id"), "owner": t.get("owner")})
        else:
            print(f"[{t.get('status')}] {t.get('name')}")
            print(f"  ID: {t.get('id')} | Story: {t.get('story_id')} | Owner: {t.get('owner')}")

    if args.json:
        print(json.dumps(tasks, ensure_ascii=False, indent=2))
    return tasks


def cmd_create_task(args):
    """创建 TAPD 任务（含重复检查和响应丢失回查）"""
    workspace_id = args.workspace or DEFAULT_WS
    owner = args.owner or DEFAULT_OWNER

    # 步骤 1: 先查是否已存在同名任务（防止重复创建）
    existing = mcp_call("get_stories_or_tasks", {
        "workspace_id": workspace_id,
        "options": {
            "entity_type": "tasks",
            "story_id": args.story_id,
            "owner": owner,
            "limit": 50,
        }
    })

    if existing and existing.get("data"):
        for item in existing["data"]:
            t = item.get("Task", item)
            if t.get("name") == args.name:
                print(f"⏭ 任务已存在，跳过创建: {args.name}")
                print(f"  ID: {t.get('id')} | Story: {args.story_id}")
                return t.get("id")

    # 步骤 2: 创建新任务
    result = mcp_call("create_story_or_task", {
        "workspace_id": workspace_id,
        "name": args.name,
        "options": {
            "entity_type": "tasks",
            "story_id": args.story_id,
            "owner": owner,
            "priority_label": args.priority or "normal",
        }
    })

    if result:
        data = result.get("data", {})
        if isinstance(data, str):
            print(f"❌ 创建失败: {data}")
            return None
        t = data.get("Task", data) if isinstance(data, dict) else {}
        tid = t.get("id", "unknown")
        print(f"✅ 任务已创建: {args.name}")
        print(f"  ID: {tid} | Story: {args.story_id}")
        return tid

    # 步骤 3: 响应丢失，回查确认是否实际已创建（防止重试创建重复）
    print("⚠ 创建响应丢失，回查确认是否已写入...")
    time.sleep(2)
    check = mcp_call("get_stories_or_tasks", {
        "workspace_id": workspace_id,
        "options": {
            "entity_type": "tasks",
            "story_id": args.story_id,
            "owner": owner,
            "limit": 50,
        }
    })

    if check and check.get("data"):
        for item in check["data"]:
            t = item.get("Task", item)
            if t.get("name") == args.name:
                print(f"✅ 任务已创建（响应丢失但已写入）: {args.name}")
                print(f"  ID: {t.get('id')} | Story: {args.story_id}")
                return t.get("id")

    print("❌ 创建失败: 无响应且回查未找到（请勿重试，先手动确认 TAPD 中是否已创建）")
    return None


def cmd_fill(args):
    """填写单条工时"""
    workspace_id = args.workspace or DEFAULT_WS
    date_str = args.date
    hours = str(args.hours)

    # 先查是否已有记录
    check = mcp_call("get_timesheets", {
        "workspace_id": workspace_id,
        "options": {
            "entity_type": "task",
            "entity_id": args.task_id,
            "spentdate": date_str,
            "limit": 5,
        }
    })

    existing = []
    if check and check.get("data"):
        for item in check["data"]:
            t = item.get("Timesheet", item)
            if t.get("spentdate") == date_str:
                existing.append(t)

    if existing:
        ts = existing[0]
        current_h = ts.get("timespent", "0")
        if current_h == hours:
            print(f"⏭ {date_str}: 已有 {hours}h，跳过 (id={ts.get('id')})")
            return ts.get("id")
        else:
            # 更新
            result = mcp_call("update_timesheets", {
                "workspace_id": workspace_id,
                "options": {
                    "id": ts.get("id"),
                    "timespent": hours,
                }
            })
            if result:
                print(f"✅ {date_str}: {current_h}h → {hours}h (updated)")
            return ts.get("id")

    # 新增
    result = mcp_call("add_timesheets", {
        "workspace_id": workspace_id,
        "options": {
            "entity_type": "task",
            "entity_id": args.task_id,
            "timespent": hours,
            "spentdate": date_str,
            "owner": args.owner or DEFAULT_OWNER,
            "memo": args.memo or "",
        }
    })

    if result:
        ts = result.get("data", {}).get("Timesheet", {})
        tid = ts.get("id", "unknown")
        print(f"✅ {date_str}: {hours}h (id={tid})")
        return tid
    else:
        # 检查是否实际已写入
        check2 = mcp_call("get_timesheets", {
            "workspace_id": workspace_id,
            "options": {"entity_type": "task", "entity_id": args.task_id, "spentdate": date_str, "limit": 5}
        })
        if check2 and check2.get("data"):
            ts = check2["data"][0].get("Timesheet", check2["data"][0])
            print(f"✅ {date_str}: {hours}h (已写入但响应丢失, id={ts.get('id')})")
            return ts.get("id")
        print(f"❌ {date_str}: 填写失败")
        return None


def cmd_batch_fill(args):
    """批量填写（需确认）"""
    task_id = args.task_id
    workspace_id = args.workspace or DEFAULT_WS
    target_dates = get_workdays(args.start, args.end)

    # 先查该任务已有的工时
    result = mcp_call("get_timesheets", {
        "workspace_id": workspace_id,
        "options": {
            "entity_type": "task",
            "entity_id": task_id,
            "spentdate": f"{args.start}~{args.end}",
            "limit": 100,
        }
    })

    existing_dates = set()
    if result and result.get("data"):
        for item in result["data"]:
            t = item.get("Timesheet", item)
            existing_dates.add(t.get("spentdate", ""))

    # 同时查全局限额
    global_result = mcp_call("get_timesheets", {
        "workspace_id": workspace_id,
        "options": {
            "owner": args.owner or DEFAULT_OWNER,
            "spentdate": f"{args.start}~{args.end}",
            "limit": 100,
        }
    })

    daily_totals = {}
    if global_result and global_result.get("data"):
        for item in global_result["data"]:
            t = item.get("Timesheet", item)
            d = t.get("spentdate", "")
            daily_totals[d] = daily_totals.get(d, 0) + int(t.get("timespent", 0))

    to_fill = []
    for d in target_dates:
        if d in existing_dates:
            continue  # 该任务已有此日工时
        cur = daily_totals.get(d, 0)
        if cur >= int(args.max_hours or 8):
            continue  # 当日已满
        need = min(int(args.hours or 8), int(args.max_hours or 8) - cur)
        to_fill.append({"date": d, "hours": need})

    if not to_fill:
        print("没有需要填写的日期")
        return

    print(f"待填写 {len(to_fill)} 天，共 {sum(e['hours'] for e in to_fill)}h:\n")
    for e in to_fill:
        wd = date.fromisoformat(e["date"]).strftime("%a")
        print(f"  {e['date']} ({wd})  {e['hours']}h")

    if not args.yes:
        resp = input("\n确认填写? [y/N]: ")
        if resp.lower() != "y":
            print("已取消")
            return

    # 逐条填写
    filled = []
    for e in to_fill:
        tid = cmd_fill(argparse.Namespace(
            task_id=task_id, date=e["date"], hours=e["hours"],
            workspace=workspace_id, owner=args.owner, memo=args.memo
        ))
        if tid:
            filled.append(e)
        time.sleep(1)

    print(f"\n✅ 完成: {len(filled)}/{len(to_fill)} 条, 共 {sum(e['hours'] for e in filled)}h")


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description="TAPD 工时管理脚本")
    sub = parser.add_subparsers(dest="cmd")

    # analyze
    p = sub.add_parser("analyze", help="分析缺失工时")
    p.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    p.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    p.add_argument("--workspace", help=f"TAPD 项目 ID (默认 {DEFAULT_WS})")
    p.add_argument("--owner", help=f"用户 (默认 {DEFAULT_OWNER})")
    p.add_argument("--json", action="store_true", help="JSON 输出")

    # find-task
    p = sub.add_parser("find-task", help="查找任务")
    p.add_argument("--story-id", help="Story ID")
    p.add_argument("--owner", help="任务负责人")
    p.add_argument("--name", help="任务名称关键词")
    p.add_argument("--workspace", help=f"TAPD 项目 ID")
    p.add_argument("--json", action="store_true", help="JSON 输出")

    # create-task
    p = sub.add_parser("create-task", help="创建任务")
    p.add_argument("--story-id", required=True, help="Story ID")
    p.add_argument("--name", required=True, help="任务名称")
    p.add_argument("--workspace", help=f"TAPD 项目 ID")
    p.add_argument("--owner", help="任务负责人")
    p.add_argument("--priority", help="优先级")

    # fill
    p = sub.add_parser("fill", help="填写单条工时")
    p.add_argument("--task-id", required=True, help="TAPD 任务 ID")
    p.add_argument("--date", required=True, help="日期 YYYY-MM-DD")
    p.add_argument("--hours", type=int, default=8, help="工时数 (默认 8)")
    p.add_argument("--workspace", help=f"TAPD 项目 ID")
    p.add_argument("--owner", help="工时记录人")
    p.add_argument("--memo", help="备注")

    # batch-fill
    p = sub.add_parser("batch-fill", help="批量填写工时")
    p.add_argument("--task-id", required=True, help="TAPD 任务 ID")
    p.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    p.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    p.add_argument("--hours", type=int, default=8, help="每天工时 (默认 8)")
    p.add_argument("--max-hours", type=int, default=8, help="每日工时上限 (默认 8)")
    p.add_argument("--workspace", help=f"TAPD 项目 ID")
    p.add_argument("--owner", help="工时记录人")
    p.add_argument("--memo", help="备注")
    p.add_argument("--yes", action="store_true", help="跳过确认")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    cmds = {
        "analyze": cmd_analyze,
        "find-task": cmd_find_task,
        "create-task": cmd_create_task,
        "fill": cmd_fill,
        "batch-fill": cmd_batch_fill,
    }
    cmds[args.cmd](args)


if __name__ == "__main__":
    main()
