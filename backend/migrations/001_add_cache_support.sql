-- ============================================
-- Skill Hub 缓存功能 - 数据库迁移脚本
-- 版本: v1.0
-- 日期: 2026-02-15
-- 说明: 添加本地缓存支持，包括缓存字段和新表
-- ============================================

-- 1. 修改 repositories 表：添加缓存相关字段
ALTER TABLE repositories 
    ADD COLUMN IF NOT EXISTS cache_version VARCHAR(64) COMMENT '缓存版本标识（压缩包Hash）' AFTER last_sync_at,
    ADD COLUMN IF NOT EXISTS cache_path VARCHAR(500) COMMENT '本地缓存绝对路径' AFTER cache_version,
    ADD COLUMN IF NOT EXISTS cache_size BIGINT DEFAULT 0 COMMENT '缓存占用空间（字节）' AFTER cache_path;

-- 2. 修改 skills 表：添加本地路径字段
ALTER TABLE skills 
    ADD COLUMN IF NOT EXISTS local_path VARCHAR(500) COMMENT '本地缓存中的绝对路径' AFTER directory;

-- 3. 创建 skill_files 表（如果不存在）
CREATE TABLE IF NOT EXISTS skill_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skill_id INT NOT NULL,
    file_path VARCHAR(500) NOT NULL COMMENT '相对于 Skill 目录的文件路径',
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_size INT DEFAULT 0 COMMENT '文件大小（字节）',
    file_type VARCHAR(50) DEFAULT 'text' COMMENT '文件类型',
    is_main BOOLEAN DEFAULT FALSE COMMENT '是否为主文件 SKILL.md',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    INDEX idx_skill_id (skill_id),
    INDEX idx_file_path (file_path(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 创建 cache_config 表（如果不存在）
CREATE TABLE IF NOT EXISTS cache_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 初始化缓存配置
INSERT INTO cache_config (config_key, config_value, description) VALUES
('cache_base_path', './cache', '缓存根目录'),
('max_cache_size_gb', '10', '最大缓存大小 GB'),
('max_file_size_mb', '10', '单个文件最大大小 MB'),
('max_skill_size_mb', '50', '单个 Skill 最大总大小 MB'),
('cleanup_strategy', 'lru', '缓存清理策略'),
('skill_hub_url', 'http://localhost:8000', 'Skill Hub 服务器地址（用于 CLI）'),
('skill_download_dir', './skills', 'CLI 默认下载目录')
ON DUPLICATE KEY UPDATE config_key=config_key;
