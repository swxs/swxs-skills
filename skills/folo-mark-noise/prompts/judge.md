只返回文字。每行一条：条目的 id，一个空格，然后是 0 或 1。1 是标已读，0 是留下。不要写文件，不要调用工具。

按后面给出的频道 YAML 判断这批条目。`default` 为 `ban` 时，没命中 `pick` 的回 1，命中的回 0。`default` 为 `pick` 时，没命中 `ban` 的回 0，命中的回 1。

例外下面是 `all` 或 `any`，可以嵌套。`all` 是每一条都成立，`any` 是有一条成立。每条条件有 `field`，再加 `equals`、`contains`、`llm` 里的一个。`field` 是 `categories`、`title`、`description`、`url`、`author`。`equals` 和 `contains` 忽略大小写。`categories` 的 `equals` 是其中某一项完全相等，`contains` 是其中某一项包含这段文字。另外四个字段里，`equals` 是整段相等，`contains` 是包含。`llm` 的值是一句短描述，只根据这一个字段判断。

条目里没有的字段当空。`categories` 为空时，它上面的 `equals` 和 `contains` 不成立。

下一段是频道 YAML，再下一段是这批条目的 JSON。例子只说明行的形状，不要照抄例子里的 id：

entry-id 1
entry-id 0
