---
name: tapd
description: 用 Python 标准库调用 TAPD 开放 API，查询或改写需求、任务、缺陷、评论、工作流、迭代、测试用例、Wiki、工时和发布计划。当用户要查 TAPD、建需求或任务、改工时、或提到 workspace、story、task、timesheet 时使用。认证读 SWXSSKILL_TAPD_ACCESS_TOKEN。
---

# TAPD

通过 TAPD 开放 API 操作用例、需求、任务、缺陷、评论、迭代、Wiki、工时。调用 `skills/tapd/scripts/tapd_client_stdlib.py`（仅标准库）。字段见 [reference/api_reference.md](reference/api_reference.md)。

## 环境

| 变量                               | 必填   | 说明                                 |
| ---------------------------------- | ------ | ------------------------------------ |
| `SWXSSKILL_TAPD_ACCESS_TOKEN`      | 二选一 | 个人访问令牌                         |
| `SWXSSKILL_TAPD_API_USER`          | 二选一 | API 账号，与密码搭配                 |
| `SWXSSKILL_TAPD_API_PASSWORD`      | 二选一 | API 密码                             |
| `SWXSSKILL_TAPD_API_BASE_URL`      | 可选   | 默认 `https://api.tapd.cn`           |
| `SWXSSKILL_TAPD_BASE_URL`          | 可选   | 前端链接，默认 `https://www.tapd.cn` |
| `SWXSSKILL_TAPD_BOT_URL`           | 可选   | 企业微信机器人 webhook               |
| `SWXSSKILL_TAPD_CURRENT_USER_NICK` | 可选   | 未传 nick 时用于参与项目、待办       |

令牌为空且账号密码也空时停下来，指出缺 `SWXSSKILL_TAPD_ACCESS_TOKEN`。

请求：base 后加 `s=mcp`；`Authorization: Bearer <token>` 或 Basic；`Content-Type: application/json`；`Via: mcp`。客户端已绕过系统代理直连（本机代理指向无人监听的端口）。

## 短号转长号

短 ID（≤9 位）调用前转换：云环境（base 含 `api.tapd.cn`）前缀 `11`，否则 `10`。格式 `{prefix}{workspace_id}{id.zfill(9)}`。多 ID 逐个转换后逗号拼接。

## 写入约束

- 父需求不能挂任务。`POST tasks` 返回 `422`，`info` 含 `is a parent story`。判断：`children_id` 非空，或 `parent_id` 为 `0` 且子项多。挂到叶子需求，或先 `POST stories` 带 `parent_id` 建子需求。
- 更新工时只吃 `timespent`、`timeremain`、`memo`。带上 `entity_id` 仍返回成功，记录还在旧任务上。换任务 = 新任务下新建 + 旧记录软删。
- `DELETE /timesheets` 返回 403。软删用 `POST timesheets`，body `{"id":"…","is_delete":"1"}`。删后按 id 查不到。
- `POST tasks` 带 `id` 和 `story_id` 能把任务换到另一个需求。任务 ID 不变，其下工时跟着走。能改任务就改任务。
- 同一 `(owner, spentdate, entity)` 再提交返回 422。先查后写。
- `GET timesheets` 的 `spentdate` 支持 `YYYY-MM-DD~YYYY-MM-DD`。

## 操作清单

| 能力                | 方法     | 端点                                              | 主要参数                                                         |
| ------------------- | -------- | ------------------------------------------------- | ---------------------------------------------------------------- |
| 参与项目            | GET      | workspaces/user_participant_projects              | nick。过滤 category=organization                                 |
| 需求或任务          | GET      | stories 或 tasks                                  | workspace_id, entity_type, page, limit, id, name, status, fields |
| 数量                | GET      | stories/count 或 tasks/count                      | 与列表相同的筛选                                                 |
| 创建/更新需求或任务 | POST     | stories 或 tasks                                  | workspace_id, name(创建), id(更新), parent_id, story_id          |
| 自定义字段          | GET      | {entity_type}/custom_fields_settings              | stories / tasks / iterations / tcases                            |
| 图片                | GET      | files/get_image                                   | workspace_id, image_path                                         |
| 附件                | GET      | attachments；attachments/down                     | workspace_id, entry_id, type                                     |
| 缺陷                | GET/POST | bugs                                              | 列表同需求；创建要 title                                         |
| 评论                | GET/POST | comments                                          | entry_id, entry_type, author, description                        |
| 工作流              | GET      | workflows/all_transitions、status_map、last_steps | workspace_id, system, workitem_type_id                           |
| 工作项类型          | GET      | workitem_types                                    | workspace_id                                                     |
| 需求字段            | GET      | stories/get_fields_lable、get_fields_info         | workspace_id                                                     |
| 项目信息            | GET      | workspaces/get_workspace_info                     | workspace_id                                                     |
| 迭代                | GET/POST | iterations                                        | name, startdate, enddate, creator                                |
| 需求关联缺陷        | GET/POST | stories/get_related_bugs；relations               | story_id；source_id, target_id                                   |
| 测试用例            | GET/POST | tcases；tcases/batch_save                         | 批量最多 200                                                     |
| Wiki                | GET/POST | tapd_wikis                                        | name, markdown_description                                       |
| 待办                | GET      | users/todo/{user_nick}/{entity_type}              | story / bug / task                                               |
| 工时                | GET/POST | timesheets                                        | owner, spentdate, entity_type, entity_id, timespent              |
| 发布计划            | GET      | releases                                          | workspace_id                                                     |
| 提交关键字          | GET      | svn_commits/get_scm_copy_keywords                 | object_id, type                                                  |
| 需求分类            | GET      | story_categories                                  | workspace_id, name                                               |
| 用户信息            | GET      | users/info                                        | 解析当前 nick                                                    |
| 企业微信            | POST     | `SWXSSKILL_TAPD_BOT_URL`                          | markdown 或 markdown_v2                                          |

用 `custom_field_*` 之前先调该实体的 `custom_fields_settings`。任务状态只有 `open`、`progressing`、`done`。需求状态从 `workflows/status_map` 或 `stories/get_fields_info` 取。

## 链接

`SWXSSKILL_TAPD_BASE_URL` 默认 `https://www.tapd.cn`。

- 需求：`/{workspace_id}/prong/stories/view/{id}`
- 任务：`/{workspace_id}/prong/tasks/view/{id}`
- 缺陷：`/{workspace_id}/bugtrace/bugs/view/{id}`
- 迭代：`/{workspace_id}/prong/iterations/card_view/{id}`
- 用例：`/{workspace_id}/sparrow/tcase/view/{id}`
- Wiki：`/{workspace_id}/markdown_wikis/show/#{id}`

## 命令

```bash
python skills/tapd/scripts/tapd_client_stdlib.py projects [--nick 昵称]
python skills/tapd/scripts/tapd_client_stdlib.py workspace --workspace-id <项目ID>
python skills/tapd/scripts/tapd_client_stdlib.py stories --workspace-id <项目ID> [--entity-type stories|tasks] [--id ID] [--name 标题] [--fields id,name]
python skills/tapd/scripts/tapd_client_stdlib.py bugs --workspace-id <项目ID>
python skills/tapd/scripts/tapd_client_stdlib.py iterations --workspace-id <项目ID>
python skills/tapd/scripts/tapd_client_stdlib.py releases --workspace-id <项目ID>
python skills/tapd/scripts/tapd_client_stdlib.py get --endpoint "stories/count" -p workspace_id=<项目ID> -p entity_type=stories
python skills/tapd/scripts/tapd_client_stdlib.py post --endpoint "stories" -b "{\"workspace_id\":123,\"name\":\"标题\"}"
```

未单列的端点用 `get` / `post` 按参考文档拼。stdout 是 JSON。HTTP 错误体带 `http_status`，进程以非 0 退出。
