只返回文字。每行一条：条目的 id，一个空格，然后是 0 或 1。1 是标已读，0 是留下。不要写文件，不要调用工具。

按后面给出的频道 YAML 判断这批条目。`except` 里满足任意一条就算命中。`default` 为 `ban` 时，没命中的回 1，命中的回 0。`default` 为 `pick` 时，没命中的回 0，命中的回 1。

`except` 是列表。每一项只有 `field` 和 `desc`。`field` 只能是 `categories`、`title`、`description`、`url`、`author`。`desc` 是一句短描述，只根据这一个字段判断。任意一项命中，结果就与 `default` 相反。

下一段是频道 YAML，再下一段是这批条目的 JSON。例子只说明行的形状，不要照抄例子里的 id：

entry-id 1
entry-id 0
