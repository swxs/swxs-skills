只返回文字：先写一句中文理由，再给出 YAML。不要写文件，不要调用工具。

目标是这个人的大致偏好，不是把 pick 和 ban 完美分开。例外可以漏掉几条，也可以误伤几条。不要逐条抄标题来凑满。

这次的 default 由外面给定，照写，不要改。default 为 ban 时，只写 `pick` 例外：没命中的清掉，命中的留下。default 为 pick 时，只写 `ban` 例外：没命中的留下，命中的清掉。不要写 `keep`。

例外下面只有 `all` 或 `any` 一个，两者可以嵌套。每一条条件都有 `field`，再加 `equals`、`contains`、`llm` 里的一个。`field` 只能是 `categories`、`title`、`description`、`url`、`author`。`equals` 和 `contains` 忽略大小写。`categories` 的 `equals` 是其中某一项完全相等，`contains` 是其中某一项包含这段文字。另外四个字段里，`equals` 是整段相等，`contains` 是包含。`llm` 的值是一句短描述，只根据这一个字段判断。

规则从你收到的 JSON 来。下面的例子只说明形状，不要照抄例子里的值和 default。

例子：

```yaml
default: ban
pick:
  any:
    - field: categories
      equals: bases
    - field: description
      llm: 疑似广告
```

用户这次的 default 和 JSON 在这段说明之后。
