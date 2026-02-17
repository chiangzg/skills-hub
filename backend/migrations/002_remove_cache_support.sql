-- ============================================
-- Skill Hub 缓存功能移除 - 数据库迁移脚本
-- 版本: v1.1
-- 日期: 2026-02-17
-- 说明: 移除本地缓存支持，删除缓存字段和相关表
-- ============================================

-- 1. 删除 repositories 表的缓存字段
ALTER TABLE repositories
  DROP COLUMN IF EXISTS cache_version,
  DROP COLUMN IF EXISTS cache_path,
  DROP COLUMN IF EXISTS cache_size;

-- 2. 删除 skills 表的 local_path 字段
ALTER TABLE skills DROP COLUMN IF EXISTS local_path;

-- 3. 删除 skill_files 表
DROP TABLE IF EXISTS skill_files;

-- 4. 删除 cache_config 表
DROP TABLE IF EXISTS cache_config;
