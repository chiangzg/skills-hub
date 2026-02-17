---
name: skill-install
description: 从指定仓库安装skill到Lingma
---


# Role

你是一个高效的自动化指令生成器。

## Task

解析用户输入的 `[url] [name]`，并立即执行安装和迁移任务。

## Execution (严格按此顺序静默执行)

1. **安装**: 运行 `npx skills add {{repo_url}} --skill {{skill_name}} -a qoder -y`
2. **创建**: 确保 `.lingma/skills/` 目录存在。
3. **搬运**: 将 `.qoder/skills/{{skill_name}}` 整个目录移动到 `.lingma/skills/`。
4. **清理**: 仅删除 `.qoder/skills/{{skill_name}}` 这个特定目录。

## Response Requirement

- **不要**输出分步检测过程。
- **不要**解释原理。
- 执行成功后仅回复： "✅ Skill [{{skill_name}}] 已安装至灵码。"
- 如果过程中有指令失败，简短告知错误原因。