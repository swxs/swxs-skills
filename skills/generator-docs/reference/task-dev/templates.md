# 文档块

选用哪一块由 [guide.md](guide.md) 第 3 步决定。复制对应块，删掉用不到的行。

## Frontmatter

```yaml
---
status: in-progress
priority: normal
scheduled: YYYY-MM-DD
tags:
  - task
tapd_url: https://www.tapd.cn/...
wiki_url: https://wiki.idiaoyan.cn/...
---
```

## 主要目标

```markdown
## 主要目标

<这次要达成的结果，一两句>
```

有 `## 模型调整` 时，这一章紧挨在它前面。

## 模型调整 · DDL + init

````markdown
## 模型调整

### 模型调整DDL

```
CREATE TABLE bi_xxx (
    id BINARY(12) NOT NULL,
    created_dt DATETIME(6),
    updated_dt DATETIME(6),
    created_id BINARY(12),
    updated_id BINARY(12),
    version_id INTEGER,
    deleted BOOL,
    ... 业务列 COMMENT '...',
    PRIMARY KEY (id)
);

CREATE INDEX ix_... ON bi_xxx (...);
```

```sh
cd mysqlengine
alembic upgrade head
```
````

类型用源码里的类型。常见的有 `BINARY(12)`、`VARCHAR(n)`、`TEXT`、`SMALLINT`、`JSON`、`DATETIME(6)`、`BOOL`。

## 模型调整 · 模型说明

```markdown
### 模型说明

#### `model.field`

| 常量名        | 值  | 描述 |
| ------------- | --- | ---- |
| ENUM_NAME_FOO | 0   | 说明 |
```

多个枚举时，重复 `` #### `model.field` `` 和表格。模型名小写，如 `aicolumn.ttype`、`dataagentcolumn.ttype`。状态机可加第四列「描述/场景」。

## 交互 · 接口一览

两个及以上 HTTP 接口时使用。

```markdown
## 交互

### 接口一览

| 方法 | 路径                                | 说明                     |
| ---- | ----------------------------------- | ------------------------ |
| POST | `/api/bi/v5/worktablepackages/`     | 创建分组（含层级校验）   |
| PUT  | `/api/bi/v5/worktablepackages/{id}` | 更新分组名称/排序/父节点 |
```

只有一个接口时，省去接口一览，直接写 `### <场景>`。

## 交互 · 场景

约束写在 curl 前面。响应一行能写清时用一行。

````markdown
### 创建子分组（指定父节点）

`parent_id` 为上一级分组 ID；整树不超过 3 层。

```sh
curl --location 'http://<env-host>/api/bi/v5/worktablepackages/' \
--header 'Authorization: Bearer <token>' \
--header 'Content-Type: application/json' \
--data '{"name": "文件夹1", "order": 0, "parent_id": "<id>"}'
```

响应示例：`{"code":0,"data":{"id":"<package_id>"}}`
````

响应需要展开结构时用 `json` 块，字段与 Handler 返回对齐。

````markdown
### 获取分组树

仅返回分组嵌套结构，不含工作表叶子节点。

```sh
curl --location "http://<env-host>/api/bi/v2/worktable_packages/tree/" \
--header "Authorization: Bearer <token>"
```

响应示例（结构示意）：

```json
{
  "code": 0,
  "data": {
    "children": [
      { "ttype": "worktable_package", "id": "<package_id>", "children": [] }
    ]
  }
}
```
````
