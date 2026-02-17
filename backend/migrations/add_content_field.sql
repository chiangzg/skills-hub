-- 添加 content 字段到 skills 表
-- 用于存储 SKILL.md 文件的 markdown 正文内容

ALTER TABLE skills ADD COLUMN content LONGTEXT NULL AFTER description;

-- 执行完成后，需要重新同步仓库以填充 content 字段
-- 可以通过管理后台的"同步"按钮或调用 API: POST /api/admin/repositories/{id}/sync
