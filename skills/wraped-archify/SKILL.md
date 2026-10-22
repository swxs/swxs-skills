---
name: wrap-archify
description: 对 archify 技能的封装。当用户要求绘制架构图、工作流、时序图、数据流、生命周期图时触发。自动将输出文件放到 diagram/ 目录，使用三段式命名 {content}.{diagram_type}.{ext}。
---

# Wrap Archify

对 archify 技能做项目级封装，统一输出目录和命名规范。

## 约定

### 输出目录

所有图表文件放到 `我的笔记/_resources/refs/diagram/` 目录下。

### 文件命名

三段式：`{content}.{diagram_type}.{ext}`

| 段               | 含义                 | 示例                                                            |
| ---------------- | -------------------- | --------------------------------------------------------------- |
| `{content}`      | 内容标识，kebab-case | `speckit-workflow`, `bi-chart`, `cowagent`                      |
| `{diagram_type}` | 图表类型             | `workflow`, `architecture`, `sequence`, `dataflow`, `lifecycle` |
| `{ext}`          | 文件扩展名           | `json`（规格）、`html`（成品）、`webp`（导出）                  |

示例：

```
speckit-workflow.workflow.json
speckit-workflow.workflow.html
speckit-workflow.workflow.webp
```

### 关联映射

生成图表后，自动在 `我的笔记/.obsidian/plugins/attachment-management/data.json` 的 `originalNameStorage` 中添加 webp 到原始 json 的映射，确保附件管理插件能正确追踪。

## 流程

### 1. 确定图表类型和内容标识

根据用户需求判断 `diagram_type`（architecture / workflow / sequence / dataflow / lifecycle），并商定 `{content}` 标识。

### 2. 按 archify 规范生成 JSON 规格

完全遵循 archify 技能的 Fast authoring path：

- 读取对应 schema 和示例
- 编写候选 JSON，保存到 `diagram/{content}.{diagram_type}.json`
- 设 `meta.quality_profile` 为 `"showcase"`
- 设 `meta.output` 为 `diagram/{content}.{diagram_type}.html`

### 3. 验证和交付

```bash
# 验证
node ~/.claude/skills/archify/bin/archify.mjs validate {type} diagram/{content}.{type}.json --quality showcase --json

# 交付
node ~/.claude/skills/archify/bin/archify.mjs deliver {type} diagram/{content}.{type}.json diagram/{content}.{type}.html --quality showcase --json
```

### 4. 在浏览器中打开

交付成功后自动在浏览器中打开 HTML，由用户手动导出 WebP（或 PNG/SVG 等格式）：

```bash
cmd.exe /c start "" "$(wslpath -w "$(pwd)/我的笔记/_resources/refs/diagram/{content}.{type}.html")"
```

> WebP 导出由用户在浏览器中通过 archify 内建的 Export 菜单完成。导出后用户将 webp 路径告知，继续步骤 5。

### 5. 注册映射

在 `我的笔记/.obsidian/plugins/attachment-management/data.json` 的 `originalNameStorage` 中确保映射存在。

**规则**：

1. 先检查 `md5` 是否已存在记录
2. **已存在** → 验证 `n` 字段是否正确，若不正确则修改为 `{content}.{diagram_type}`
3. **不存在** → 新增记录

```json
{
  "n": "{content}.{diagram_type}",
  "md5": "<从 IMG-XXXX.webp 提取>"
}
```

> `n` 字段统一使用三段式命名中的前两段 `{content}.{diagram_type}`，不含路径、不含扩展名。如果已有记录但 `n` 是旧值（如旧的简短名称），改为新的三段式名称。

### 6. 归档到笔记附件目录（可选）

绘制完成后，用户可以指定一个目标路径，将 JSON 规格文件移入笔记附件目录。

**触发**：用户说"归档到 X 路径"或提供类似 `_resources/refs/体验/剪藏/xxx/IMG-XXXX.webp` 的路径。

**流程**：

1. **解析目标路径**：从用户提供的路径提取目标目录和 webp 文件名（如 `IMG-D697D5145544E61941189CF739A48590.webp`）

2. **移动 JSON 文件**：

```bash
mv "我的笔记/_resources/refs/diagram/{content}.{type}.json" "我的笔记/{目标目录}/{content}.{type}.json"
```

> JSON 规格文件移到与 webp 相同的目录，HTML 和 webp 留在 `diagram/` 下（webp 已通过附件管理插件追踪，无需移动）。

3. **注册映射**：确保 `originalNameStorage` 中有记录（如果步骤 5 尚未添加，此时补上）：

```json
{
  "n": "{content}.{diagram_type}",
  "md5": "<从 IMG-XXXX.webp 提取>"
}
```

> **注意**：如果 webp 已在目标路径下（由附件管理插件管理），`n` 依然用 `{content}.{diagram_type}`（不含路径），`md5` 从文件名提取。

### 7. 清理临时文件

删除 archify 在项目根目录可能遗留的临时文件（如 `speckit-workflow.json`、`speckit-workflow.html` 等未放入 `diagram/` 的文件）。

## 注意事项

- 不要使用 Archify 的 WebFetch/WebSearch，使用 tavily-search 代替
- 图表 JSON 文件中 `meta.output` 使用项目相对路径
- `originalNameStorage` 的 `n` 字段不含扩展名；`md5` 字段从 webp 文件名 `IMG-` 前缀后提取
- 归档时只移动 JSON 规格文件，HTML 和 webp 留在 `diagram/` 目录
- 如果目标目录不存在则先创建
