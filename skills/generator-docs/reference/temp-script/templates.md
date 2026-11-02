# 文档块

选用哪一块由 [guide.md](guide.md) 第 3 步决定。复制对应块，删掉用不到的行。函数名从源码来，不从这里抄。

## Frontmatter

```yaml
---
status: in-progress
priority: normal
scheduled: YYYY-MM-DD
tags:
  - task
---
```

## 多步，后步依赖前步

````markdown
### <操作名>

```python title:<步骤名>
from <module> import <func>

<id> = "<用户给出的 id>"
await <func>(<id>)
```

```python title:<下一步>
<下一步要用的对象> = await <func>(<id>)
```

```python title:<可跳过的步骤>(Optional)
<下一步要用的对象> = await <func>(<id>)
```

<等待或人工条件，一两句>

```python
await <func>(<下一步要用的对象>)
```
````

## 同一目的，不同范围

````markdown
## 脚本

### <范围：一批>

```python
from <module> import <func>


async def run(<参数>: str) -> None:
    await <func>(<参数>)


await run("<用户给出的 id>")
```

### <范围：单条>

```python
<PARAM> = ""

from <module> import <func>

await <func>(<PARAM>)
```
````
