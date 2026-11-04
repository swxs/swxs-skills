---
name: tapd-fill-timesheet
description: 按月为 TAPD 填写工时。先核对真实工作日和证据，对齐需求与任务，逐日明细经用户同意后再写入，写完回查。当用户要填工时、补工时、报工时，或提到本月工时、上月工时时使用。
---

# 填写 TAPD 工时

按月整理工时明细, 并使用 `/tapd` 技能填写项目工时。

## 环境

从当前进程读取：

- `SWXSSKILL_TAPD_ACCESS_TOKEN`：tapd 客户端认证。为空时停下来。
- `SWXSSKILL_OBSIDIAN_VAULT`：保险库目录名。为空时停下来。

每个工作日合计 8 小时。一天两件事写成 4 小时和 4 小时。

## 口径

工作日取当年国务院放假安排，含调休周末。

证据按这个顺序取：保险库 `项目/众言/` 笔记 frontmatter（`scheduled`、`dateCreated`、`dateModified`、`completedDate`、`tapd_url`）→ `git log --all`。

git 作者都是本人：`swxs <466565029@qq.com>`、`xr.ju <xr.ju@idiaoyan.com>`、`居晓仁`。仓库：`D:/codehouse/XM`（含 `vendor`），以及同级的 `xm-app`、`CodeFactory`、`xm-workspace`。缺的仓库跳过。

分支名里的 task 号是归属线索。先在 TAPD 查到该需求或任务再用。

技术任务名以 `-py` 结尾。每月一条 `问题排查-YYYYMM`，根据实际时间填写, 挂在当年叶子需求 `问题排查-YYYY` 下。对不上具体需求的排查归这条。

需要拍板的只有三件事：缺需求时怎么建、含糊日期归哪一边、某项算不算公司工时。给出选项并标出推荐项，等用户选定。文件、接口、环境自己查。

当月计划、结果和一次性脚本写到 `.scratch/<会话编号>/`，目录约定见 `.scratch/README.md`。不把这次流水线登记进 `.scratch/资产索引.md`。

## 1. 定工作日并取证

列出该月工作日，按证据顺序收集每天的工作内容。对不上内容的日子标成「无证据」。

完成：工作日清单已经用日历和两份证据核对；每个工作日要么有内容，要么标成无证据。

## 2. 核对需求与任务

按内容查 TAPD 里是否已有叶子需求和任务。

缺需求：停在这里，把建法选项和推荐项交给用户。
有需求、缺任务：先按名称查重，没有再 `POST tasks`。技术任务加 `-py`。兜底用当月 `问题排查-YYYYMM`。

完成：每个有内容的工作日都对上了叶子需求下的任务，或仍停在等用户定需求。

## 3. 逐日明细

把计划展示给用户，并写到 `.scratch/<会话编号>/data/<yyyy-mm>_plan.json`。每天合计 8 小时。

| 日期       | 工作内容 | 任务         | 工时 |
| ---------- | -------- | ------------ | ---- |
| YYYY-MM-DD | …        | 任务名（id） | 8    |

完成：用户明确同意这份计划。同意之前不写入工时。

## 4. 先查后填

对计划中每条 `(owner, spentdate, entity_id)` 先查工时。同一组合已有记录就跳过。

```bash
python skills/tapd/scripts/tapd_client_stdlib.py get --endpoint timesheets -p workspace_id=57942251 -p entity_type=task -p owner=居晓仁 -p spentdate=<月初>~<月末> -p limit=200

python skills/tapd/scripts/tapd_client_stdlib.py post --endpoint timesheets -p workspace_id=57942251 -p entity_type=task -p entity_id=<task_id> -p timespent=8 -p owner=居晓仁 -p spentdate=<YYYY-MM-DD> -p memo=<任务名>
```

一条失败就停，先回查这条是否已经写入。

完成：计划内每条都已写入或已跳过，没有未解释的失败。

## 5. 回查并归档

再查该月工时：条数、每个工作日是否合计 8 小时、按任务汇总。回查比计划少时先问用户，按用户的决定改归档。

归档写到 `.scratch/<会话编号>/data/`：计划、结果（含 timesheet id）、新建对象 id，以及用户在界面上删改的条目和原因。

完成：归档里的数字与回查到的 TAPD 状态一致。
