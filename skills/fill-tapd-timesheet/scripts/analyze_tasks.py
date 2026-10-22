#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""分析本地任务笔记，提取活跃任务及 TAPD 信息。

从 我的笔记/项目/众言/任务计划/ 下读取 markdown 文件，
提取 frontmatter 中的 tapd_url、status、dateModified 等字段，
输出最近活跃的任务列表供填写工时使用。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, date


def parse_frontmatter(content: str) -> dict:
    """解析 markdown frontmatter"""
    m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return {}
    fm_text = m.group(1)
    result = {}
    for line in fm_text.strip().split('\n'):
        kv = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if kv:
            key = kv.group(1)
            val = kv.group(2).strip()
            result[key] = val
    return result


def extract_tapd_info(tapd_url: str) -> dict | None:
    """从 TAPD URL 提取 workspace_id 和 story_id"""
    if not tapd_url:
        return None
    # https://www.tapd.cn/tapd_fe/57942251/story/detail/1157942251001099170
    m = re.search(r'tapd_fe/(\d+)/story/detail/(\d+)', tapd_url)
    if m:
        return {
            'workspace_id': m.group(1),
            'story_id': m.group(2),
            'url': tapd_url,
        }
    return None


def find_task_files(task_dir: str) -> list[dict]:
    """扫描任务目录，返回所有任务信息"""
    tasks = []
    if not os.path.isdir(task_dir):
        print(f"错误：目录不存在 - {task_dir}", file=sys.stderr)
        return tasks

    for fname in sorted(os.listdir(task_dir)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(task_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"警告：无法读取 {fpath}: {e}", file=sys.stderr)
            continue

        fm = parse_frontmatter(content)
        tapd_info = extract_tapd_info(fm.get('tapd_url', ''))

        # Parse dateModified
        date_mod = None
        dm_str = fm.get('dateModified', '')
        if dm_str:
            try:
                # Handle ISO format like 2026-07-15T15:05:22.893+08:00
                dm_str = dm_str.split('T')[0] if 'T' in dm_str else dm_str[:10]
                date_mod = dm_str
            except Exception:
                pass

        tasks.append({
            'file': fname,
            'path': fpath,
            'status': fm.get('status', 'unknown'),
            'scheduled': fm.get('scheduled', ''),
            'dateModified': date_mod,
            'tapd': tapd_info,
            'wiki_url': fm.get('wiki_url', ''),
            'completedDate': fm.get('completedDate', ''),
        })

    return tasks


def main():
    parser = argparse.ArgumentParser(description='分析本地任务笔记，提取活跃任务')
    parser.add_argument('--task-dir', default='我的笔记/项目/众言/任务计划',
                        help='任务笔记目录路径')
    parser.add_argument('--days', type=int, default=14,
                        help='最近 N 天内修改过的任务视为活跃 (默认 14)')
    parser.add_argument('--json', action='store_true',
                        help='以 JSON 格式输出')
    args = parser.parse_args()

    tasks = find_task_files(args.task_dir)

    today = date.today()
    cutoff = today - timedelta(days=args.days)
    cutoff_str = cutoff.isoformat()

    # Categorize tasks
    in_progress = [t for t in tasks if t['status'] == 'in-progress']
    open_tasks = [t for t in tasks if t['status'] == 'open']
    # Recently modified tasks
    recent = [
        t for t in tasks
        if t['dateModified'] and t['dateModified'] >= cutoff_str
    ]
    # Tasks with TAPD URL
    with_tapd = [t for t in tasks if t['tapd']]

    if not args.json:
        print(f"任务目录: {args.task_dir}")
        print(f"总任务数: {len(tasks)}")
        print(f"进行中: {len(in_progress)} | 未开始: {len(open_tasks)} | 有 TAPD: {len(with_tapd)}")
        print(f"最近 {args.days} 天修改: {len(recent)}")
        print()

    # Output active tasks (in-progress + recently modified open tasks)
    # Deduplicate by file
    seen = set()
    active = []
    for t in in_progress + open_tasks:
        if t['file'] not in seen:
            seen.add(t['file'])
            active.append(t)

    # Sort by dateModified descending
    active.sort(key=lambda t: t['dateModified'] or '', reverse=True)

    if args.json:
        output = {
            'total': len(tasks),
            'in_progress': len(in_progress),
            'open': len(open_tasks),
            'recent_count': len(recent),
            'with_tapd': len(with_tapd),
            'active_tasks': [],
        }
        for t in active[:20]:
            entry = {
                'file': t['file'],
                'status': t['status'],
                'dateModified': t['dateModified'],
                'tapd': t['tapd'],
            }
            output['active_tasks'].append(entry)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("=== 活跃任务（用于工时填写）===\n")
        for i, t in enumerate(active[:15]):
            name = t['file'].replace('.md', '')
            tapd_str = ''
            if t['tapd']:
                tapd_str = f"ws={t['tapd']['workspace_id']} story={t['tapd']['story_id']}"
            else:
                tapd_str = '⚠ 无 TAPD 链接'
            mod_str = t['dateModified'] or '未知'
            print(f"  {i+1}. [{t['status']}] {name}")
            print(f"     修改: {mod_str} | {tapd_str}")

        if len(active) > 15:
            print(f"  ... 还有 {len(active)-15} 个任务未显示")

        if not active:
            print("  （无活跃任务）")

        # Show tasks missing TAPD URLs
        no_tapd_active = [t for t in active if not t['tapd']]
        if no_tapd_active:
            print(f"\n⚠ 以下活跃任务缺少 TAPD 链接（{len(no_tapd_active)} 个）:")
            for t in no_tapd_active:
                print(f"  - {t['file']}")


if __name__ == '__main__':
    main()
