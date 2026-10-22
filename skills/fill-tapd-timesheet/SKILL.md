---
name: fill-tapd-timesheet
description: TAPD 自动填工时。分析缺失工时的日期，从本地任务笔记中提取 TAPD 任务，智能填写每日工时。当用户提到"填工时"、"补工时"、"工时填写"、"timesheet"、"今日工时"、"本周工时"、"上月工时"或需要向 TAPD 提交工时记录时触发此技能。
---

# TAPD 自动填工时

自动检测缺失工时的日期，从 Obsidian 本地任务笔记中匹配 TAPD 任务，智能填写工时。

## 前置条件

- TAPD MCP Server (`mcp-server-tapd`) 已配置并连接
- 本地任务笔记位于 `我的笔记/项目/众言/任务计划/` 目录下
- 标准化脚本 `scripts/tapd_mcp.py` 可直接调用

## 环境变量

从当前进程的环境读取 `SWXSSKILL_TAPD_ACCESS_TOKEN`。脚本把它传给 `mcp-server-tapd` 的 `TAPD_ACCESS_TOKEN`。为空时停下来，指出缺这个变量。

## 标准化脚本

`scripts/tapd_mcp.py` 封装了所有常用操作，支持子命令：

```bash
# 分析缺失工时
python3 tapd_mcp.py analyze --start 2026-06-01 --end 2026-07-14

# 查找 Story 下的任务
python3 tapd_mcp.py find-task --story-id STORY_ID

# 创建任务
python3 tapd_mcp.py create-task --story-id STORY_ID --name "任务名"

# 单条填写
python3 tapd_mcp.py fill --task-id TASK_ID --date 2026-06-29 --hours 8

# 批量填写（自动分析+确认）
python3 tapd_mcp.py batch-fill --task-id TASK_ID --start 2026-06-01 --end 2026-07-14 --yes
```

脚本自动处理：重复检测、响应丢失验证、全局工时上限检查。

## 常见问题与经验

### add_timesheets 返回 422 ParamError

这个错误**通常意味着该日期+实体已有工时记录**（重复提交），而非参数错误。填写前**必须**先用 `get_timesheets` 确认该日期无记录。

> 实际案例：首次调用 `add_timesheets` 成功写入但脚本超时未收到响应，重试时报 422。实际上第一条已写入成功。

### MCP 调用超时

每条 TAPD MCP 调用约需 4-6 秒。多条串行调用容易触发 30s 超时。**每条 add_timesheets 单独一个进程调用**，不要在一个脚本里塞多条。

### 创建任务重复（已修复）

`create_story_or_task` 同样存在"已写入但响应丢失"的问题。如果响应超时后直接重试，会创建出重复的 Task。

> 实际案例：首次调用 `create_story_or_task` 成功创建但脚本未收到响应，重试后又创建了第二个重复 Task。

**必须使用 `tapd_mcp.py create-task` 脚本**（内置查重+回查），禁止直接调用 MCP。

### 填写后验证

填写完成后，建议用 `get_timesheets` 重新查询日期范围，确认数据已写入。不要仅依赖 `add_timesheets` 的返回值（可能因超时而丢失）。

## 工作流程

### 第 1 步：确定日期范围

与用户确认需要检查的日期范围。如果用户未明确指定：

- 默认从**今天**往前追溯到**最后有工时的日期**，最多回溯 30 天
- 排除周末（周六、周日），除非用户明确包含
- 如果用户说"本周"：检查周一至今天
- 如果用户说"上月"：检查上个月所有工作日

### 第 2 步：分析缺失工时

使用 TAPD MCP 工具 `get_timesheets` 查询已填写的工时记录：

```
workspace_id: 57942251  (倍市得通用项目，默认)
options:
  owner: 居晓仁
  spentdate: {开始日期}~{结束日期}
  limit: 100
```

将查询结果与目标日期范围对比，列出**没有工时记录的日期**。

### 第 3 步：匹配任务

运行 `scripts/analyze_tasks.py` 分析本地任务笔记，获取活跃任务列表：

```bash
python3 .claude/skills/fill-tapd-timesheet/scripts/analyze_tasks.py \
  --task-dir "我的笔记/项目/众言/任务计划" \
  --days 14
```

脚本会输出：

- 最近修改的活跃任务（含 TAPD story URL）
- 每个任务的 TAPD workspace_id 和 story_id
- 任务状态（in-progress / open）

**任务匹配规则**：

- 优先使用 `status: in-progress` 的任务
- 其次使用最近 14 天内修改过的 `status: open` 的任务
- 在日期范围内，每天至少分配 8 小时（默认）

### 第 4 步：确保 TAPD 任务存在

对于每个需要填写工时的 TAPD Story，**使用脚本** `tapd_mcp.py create-task` 创建任务（脚本内置了查重和回查逻辑）：

```bash
python3 .claude/skills/fill-tapd-timesheet/scripts/tapd_mcp.py create-task \
  --story-id STORY_ID \
  --name "任务名称"
```

脚本自动执行：

1. 先查该 Story 下是否已存在同名任务 → 存在则直接返回已有 ID
2. 调用 `create_story_or_task` 创建
3. 如果响应丢失，回查确认是否实际已写入（防止误判失败后重试导致重复创建）

⚠ **禁止直接调用 MCP `create_story_or_task`**。必须通过脚本创建，否则无法防止重复。

创建 Task 后记录新的 task_id，后续工时填写到该 Task 上。

### 第 5 步：汇总确认 ⛔ 必须执行，不可跳过

> **🚨 此步骤是硬性阻断点。未获得用户明确确认（如"确认"、"可以"、"执行"）前，绝对禁止进入第 6 步。**

生成工时填写计划表格，通过对话展示给用户确认：

```
📋 工时填写计划

| 日期       | 任务                                    | 工时 | 状态   |
|------------|-----------------------------------------|------|--------|
| 2026-07-14 | 开发-客户旅程-AI生成 (task: xxx)         | 8h   | 待填写 |
| 2026-07-15 | 开发-AI场景洞察-壁挂空调 (task: xxx)     | 8h   | 待填写 |
| 2026-07-13 | 开发-数据源-AGENT (task: xxx)            | 8h   | 已有工时 |

共 2 天待填写，合计 16h
```

展示表格后，**使用 AskUserQuestion 工具**向用户确认是否执行填写。必须等待用户明确回复"确认"、"可以"、"是"、"执行"等肯定答复后，才能进入第 6 步。

### 第 6 步：填写工时

用户确认后，**逐条填写**。使用 MCP 工具 `add_timesheets` 逐条调用（不要用 `batch-fill --yes`，它绕过了第 5 步的确认）：

```
workspace_id: {workspace_id}
options:
  entity_type: task
  entity_id: {task_id}
  timespent: {小时数}
  spentdate: {日期 YYYY-MM-DD}
  owner: 居晓仁
  memo: {任务名称}
```

**关键规则**：

1. **先查后填（必须）**：调用 `add_timesheets` 前，先用 `get_timesheets` 确认该日期+实体无记录。`add_timesheets` 的重复提交会返回 `422 ParamError` 而非明确的"重复"提示，容易误判。

2. **逐条执行**：每条 `add_timesheets` 单独一个进程/调用，不要在一个脚本里串联多条。单次调用约 4-6 秒，串行过多会超时。

3. **超时验证**：如果调用超时，先查 `get_timesheets` 确认是否实际已写入（TAPD 可能已处理但响应未返回），再决定是否重试。

4. **工时上限**：如果某日期总工时已满 8h，跳过该日期。

5. **更新已有记录**：如果某日期已有该任务工时但需要修改，用 `update_timesheets` 而非 `add_timesheets`。

### 第 7 步：汇总报告

填写完成后，输出汇总：

```
✅ 工时填写完成

已填写：
  2026-07-14: 开发-客户旅程-AI生成 (8h)
  2026-07-15: 开发-AI场景洞察-壁挂空调 (8h)

已跳过（已有工时）：
  2026-07-13: 8h

共填写 X 天，Y 小时
```

## 配置

默认配置（可在技能内按需调整）：

| 配置项          | 默认值                        | 说明                             |
| --------------- | ----------------------------- | -------------------------------- |
| `workspace_id`  | `57942251`                    | 默认 TAPD 项目（倍市得通用项目） |
| `owner`         | `居晓仁`                      | 工时记录人                       |
| `hours_per_day` | `8`                           | 默认每天工时                     |
| `task_dir`      | `我的笔记/项目/众言/任务计划` | 本地任务笔记目录                 |

## TAPD URL 解析

笔记中的 `tapd_url` 格式：

```
https://www.tapd.cn/tapd_fe/{workspace_id}/story/detail/{story_id}
```

提取规则：

- `workspace_id`: URL 路径中 `tapd_fe/` 后的数字
- `story_id`: URL 路径中 `detail/` 后的 19 位数字
