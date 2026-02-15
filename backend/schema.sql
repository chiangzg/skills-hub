-- Skills Platform 数据库初始化脚本
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS skills CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE skills;

-- 1. users 表（用户管理）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('ADMIN', 'MAINTAINER') NOT NULL DEFAULT 'MAINTAINER',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. repositories 表（仓库配置）
CREATE TABLE IF NOT EXISTS repositories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('GITHUB', 'GITLAB') NOT NULL,
    owner VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    branch VARCHAR(50) DEFAULT 'main',
    gitlab_url VARCHAR(255),
    access_token VARCHAR(255),
    webhook_secret VARCHAR(255),
    webhook_enabled BOOLEAN DEFAULT FALSE,
    enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP NULL,
    cache_version VARCHAR(64) COMMENT '缓存版本标识（压缩包Hash）',
    cache_path VARCHAR(500) COMMENT '本地缓存绝对路径',
    cache_size BIGINT DEFAULT 0 COMMENT '缓存占用空间（字节）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type_enabled (type, enabled),
    INDEX idx_owner_name (owner, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. categories 表（多级分类）
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_parent (parent_id),
    INDEX idx_slug (slug),
    INDEX idx_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. skills 表（Skill 信息）
CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    repository_id INT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    directory VARCHAR(500) NOT NULL,
    local_path VARCHAR(500) COMMENT '本地缓存中的绝对路径',
    repo_owner VARCHAR(100),
    repo_name VARCHAR(100),
    repo_branch VARCHAR(50),
    readme_url TEXT,
    raw_content_url TEXT,
    stars INT DEFAULT 0,
    views INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE SET NULL,
    INDEX idx_repository (repository_id),
    FULLTEXT INDEX idx_search (name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. category_skills 表（分类与 Skill 关联）
CREATE TABLE IF NOT EXISTS category_skills (
    category_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (category_id, skill_id),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. webhooks 表（Webhook 日志）
CREATE TABLE IF NOT EXISTS webhooks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    repository_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSON,
    status ENUM('pending', 'processing', 'success', 'failed') DEFAULT 'pending',
    error_message TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
    INDEX idx_repository_status (repository_id, status),
    INDEX idx_triggered_at (triggered_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. skill_files 表（Skill 文件索引）[新增]
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

-- 8. cache_config 表（缓存配置）[新增]
CREATE TABLE IF NOT EXISTS cache_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 数据初始化
-- ============================================

-- 初始化缓存配置
INSERT INTO cache_config (config_key, config_value, description) VALUES
('cache_base_path', './cache', '缓存根目录'),
('max_cache_size_gb', '10', '最大缓存大小 GB'),
('max_file_size_mb', '10', '单个文件最大大小 MB'),
('max_skill_size_mb', '50', '单个 Skill 最大总大小 MB'),
('cleanup_strategy', 'lru', '缓存清理策略'),
('skill_hub_url', 'http://localhost:8000', 'Skill Hub 服务器地址（用于 CLI）'),
('skill_download_dir', './skills', 'CLI 默认下载目录')
ON DUPLICATE KEY UPDATE config_key=config_key;

-- 初始化 admin 账号（密码: Admin@123）
-- 注意：实际部署时需要修改密码
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$argon2id$v=19$m=65536,t=3,p=4$/Z+zVsq5t5byXuvd2zuH8A$bW1+7qhsYrgSMBupGM58f3m8QOJiLTEo4b3+WB41Y14', 'ADMIN')
ON DUPLICATE KEY UPDATE username=username;
