只返回文字：先写一段中文理由，给人物画像，再给出 YAML。不要写文件，不要调用工具。

目标是探究用户大致偏好，不是把 `pick` 和 `ban` 完美分开。不要局限于示例数据，从更高的视角分析用户倾向，不要逐条抄标题来凑满。

`default` 由用户指定。

`except` 是列表。每一项只有 `field` 和 `desc`。`field` 只能是 `categories`、`title`、`description`、`url`、`author`。`desc` 是一句短描述，只根据这一个字段判断。任意一项命中，结果就与 `default` 相反。

规则从你收到的 JSON 来。下面的例子只说明形状，不要照抄例子里的值和 default。

例子：

```yaml
default: ban
except:
  - field: categories
    desc: 包含 bases
  - field: description
    desc: 会议录音或实时转写
```

用户这次的 default 和 JSON 在这段说明之后。
