---
name: folo-mark-noise
description: 按频道 YAML 清理 Folo 未读。先按 folo-cli 确认 whoami，再建立频道配置或执行清理脚本。用户要清理 Folo 未读、过滤低价值 RSS、给订阅源写清理规则时使用。
---

# 目标

按频道配置清理未读 RSS。

## 确认登录

按 [folo-cli](../folo-cli/SKILL.md) 跑通 `whoami`。

完成：`whoami` 的 `ok` 为 true。

## 建立频道配置

1. 锁定源：按 [folo-cli](../folo-cli/SKILL.md) 跑 `subscription list --format json`，或 `feed get <feedId|url>`。记下 `feedId`。

完成：有一个 `feedId`。

2. 在 `skills/folo-mark-noise` 执行：

```powershell
node scripts/ban-pick.mjs <feedId>
```

脚本打开对开页面并停住。等待用户选择倾向后生成标准输出JSON，退出码为 0。JSON 里有 `feedId`、`title`、`entries`。`entries` 只有点过的条目，每条有 `decision`：`pick` 或 `ban`。

完成：退出码为 0，且标准输出能解析成这份 JSON。退出码不是 0 时标准输出为空，停，不要启动子代理。

3. 用步骤 2 的 JSON 算 `default`：`ban` 的比例大于等于 75% 则为 `ban`，否则为 `pick`。读 [prompts/keep-yaml.md](prompts/keep-yaml.md)。新开一个子代理，模型沿用当前这个，不带这段对话。提示只有该文件的全文，加一行 `default: ban` 或 `default: pick`，再加上这份 JSON。

完成：子代理返回一段文字。

4. 这段文字里要有给定的 `default`，以及对应的例外：`default` 为 `ban` 时是 `pick`，为 `pick` 时是 `ban`。把理由和 YAML 给用户。用户接受后，把 JSON 里的 `feedId`、`title` 和这段 YAML 写入 `channels/<slug>.yaml`。slug 用小写英文短横线。对不上这个形状，就把整段给用户，停，不要再叫一次子代理。

```yaml
feedId: "<id>"
title: "<订阅标题>"
default: ban
pick:
  any:
    - field: description
      llm: 会议录音或实时转写
```

`default` 为 `ban` 时，没命中 `pick` 的条目清掉，命中的留下。`default` 为 `pick` 时，没命中 `ban` 的条目留下，命中的清掉。例外下面只能有 `all` 或 `any` 一个，两者可以嵌套。每一条都有 `field`，再加 `equals`、`contains`、`llm` 里的一个。

完成：用户接受，且文件里有 `feedId`、`title`、`default`，以及 `pick` 或 `ban`。或者用户看到了理由，且没有新文件。

## 清理

在 `skills/folo-mark-noise` 目录下执行。token 和代理按 [folo-cli](../folo-cli/SKILL.md) 的本机调用。

1. 拉未读：

```powershell
node scripts/clean.mjs list channels/<slug>.yaml
```

标准输出是 JSON 数组。每条有 `id`、`title`、`description`、`categories`、`url`、`author`。

完成：退出码为 0，且标准输出能解析成这个数组。退出码不是 0 时标准输出为空，停。

2. 数组为空时，把 `[]` 写成 id 文件，进入步骤 4。

数组非空时，按每批最多 20 条切开。同一轮为每一批新开一个子代理，模型沿用当前这个，不带这段对话。提示只有三段，中间各空一行：[prompts/judge.md](prompts/judge.md) 的全文、频道 YAML 的全文、这批条目的 JSON。每条只留 `id`，以及 YAML 里每个 `field` 写到的字段。

完成：每一批都有了结果。子代理没有返回文字的批，整批留下。

3. 逐行收集。一行去掉首尾空白后是 `id 0` 或 `id 1`，并且这个 id 在这批里，才算对上。`1` 的 id 标已读，`0` 的留下。缺了的 id、多出来的 id、不是 0 或 1 的行、同一个 id 既有 0 又有 1，都留下。某一批没有对上的行，这一批全部留下，其他批照常收集。把要标已读的 id 写成 JSON 数组，放到当前会话目录的 `data/mark-ids.json`。数组可以是空的。会话目录按 `.scratch/README.md`。

完成：id 文件是一个 JSON 数组。

4. 标已读：

```powershell
node scripts/clean.mjs mark channels/<slug>.yaml <id文件>
```

成功时标准输出只有两行，都是这个频道的未读条数：标之前、标之后。id 文件是空数组时不提交标已读，仍然打印这两行。

完成：退出码为 0，且只看到这两行数字。退出码不是 0 时标准输出为空，停。
