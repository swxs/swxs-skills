# 开发类型技术文档

文档以代码为准。路由、枚举名、DDL、路径参数都从源码读出。未实现的接口和字段不写入。

## 1. 确定输出路径

用户给出路径则用该路径。未给出则提问，得到路径再写。

要我们起文件名时，用 `开发-<功能名>.md`。功能名可以再带连字符。

已有 frontmatter 时保持原样。新建且需要 frontmatter 时，用 [templates.md](templates.md) 的 Frontmatter 块，键按用户任务插件增减。

完成：目标路径已确定。文件名由我们起时，符合 `开发-<功能名>.md`。

## 2. 采集事实

按文档会写到的部分逐项读取。读不到的标成「无」。

| 事实                     | 来源                                        |
| ------------------------ | ------------------------------------------- |
| 表名、列类型、索引       | `models.py`                                 |
| 枚举常量名与值           | `model_enums.py`                            |
| 路由（方法、路径）       | `handler/__init__.py`                       |
| Handler 返回字段         | 对应 Handler                                |
| CodeFactory 的 YAML 路径 | 发生变更的 YAML；记在 init 说明或枚举表脚注 |

有 alembic migration 时，DDL 原文取 `mysqlengine` 目录下 `alembic upgrade <revision> --sql` 的输出。DEFAULT、索引名、反引号与该输出一致。

没有 migration、但是新表时，按 `models.py` 写 `CREATE TABLE` 与 `CREATE INDEX`。

两种 DDL 都带上 ModelBase 固定列：`id`、`created_dt`、`updated_dt`、`created_id`、`updated_id`、`version_id`、`deleted`。

完成：上表每一行都是「已采集」或「无」；需要 DDL 时，SQL 原文已经在手。

## 3. 定章节

```
主要目标
└─ 总是写在最前。有模型调整时，紧挨在 ## 模型调整 之前

模型调整
├─ 有表结构变更 → DDL，有枚举再接模型说明
├─ 仅枚举或语义变更 → 只写模型说明
└─ 无模型变更 → 整节省略

交互
├─ HTTP ≥ 2 → 接口一览，再接各场景
├─ HTTP = 1 → 一个场景节
└─ 无 HTTP → 整节省略
```

主要目标写这次要达成的结果，一两句。实现步骤和字段表不放在这一章。

模型调整里先 DDL，后枚举。列的含义写在 DDL 的 COMMENT 里。

每个场景的顺序：约束（有则写）→ curl → 响应示例。

块的写法见 [templates.md](templates.md)。

完成：主要目标已列入章节；模型调整与交互各自走哪一支已经定下。

## 4. 写入

把定下的块写入目标路径。

- `## 主要目标` 在 `## 模型调整` 之前；没有模型调整时，它仍是第一个二级标题
- DDL 的标题是 `### 模型调整DDL`，SQL 放在裸代码块里
- 枚举标题是 `` #### `model.field` ``，模型名小写；表头为常量名、值、描述
- 接口一览的方法、路径与 `handler/__init__.py` 一致
- curl 带 `Authorization: Bearer <token>`；主机与 id 用 `<env-host>`、`<id>`
- 响应与 Handler 返回字段对齐；一行能写清用一行，否则用 `json` 块
- DDL 后的 `sh`：源码里已有 init 命令则原样写入，否则在 `mysqlengine` 目录执行 `alembic upgrade head`

完成：文件已写入；章节与第 3 步的分支一致；正文与第 2 步的事实一致。

## 5. 自检

- [ ] 正文以 `## 主要目标` 开头；有 `## 模型调整` 时，主要目标紧挨在它前面
- [ ] 有 DDL 时标题为 `### 模型调整DDL`，含 ModelBase 列与索引
- [ ] 仅枚举变更时，模型调整下只有 `### 模型说明`
- [ ] 枚举常量名、值与 `model_enums` 一致
- [ ] 有 migration 时，文档 DDL 与 `alembic upgrade --sql` 输出一致
- [ ] 接口路径与 `handler/__init__.py` 一致

完成：每一项为通过，或不适用并注明原因。
