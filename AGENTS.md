# swxs-skills

个人技能仓库。每份技能是 `skills/` 下一个技能文件夹（目录里有 `SKILL.md`）。

## 地图

```
skills/
├── fill-tapd-timesheet/    填写工时
├── folo-cli/               用 folocli 调 Folo
├── folo-mark-noise/        按频道规范标记低价值 RSS
├── wraped-archify/         封装archify技能
└── query-work-1/           查询众言工作记录
```

## 新增技能

在 `skills/<名字>/SKILL.md` 建一份技能。目录名与 frontmatter 的 `name` 写成同一个名字。

### 环境变量

技能读取的环境变量一律以 `SWXSSKILL_` 开头，例如 `SWXSSKILL_OBSIDIAN_VAULT`。

### 临时脚本与临时产物

- **临时内容必须归档到规范位置**：会话中新增的脚本及各种临时内容前，**必须** 读取 **`.scratch/README.md`**约定, 一律放到`.scratch/<会话编号>`目录中
- 需要长期复用的资产在 **`.scratch/资产索引.md`** 中登记, 登记文件需要用户同意
- **禁止**使用`.scratch/<会话编号>`以外的目录
