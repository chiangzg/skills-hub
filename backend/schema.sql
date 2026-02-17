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

-- ============================================
-- 数据初始化
-- ============================================

-- 初始化 admin 账号（密码: Admin@123）
-- 注意：实际部署时需要修改密码
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$argon2id$v=19$m=65536,t=3,p=4$/Z+zVsq5t5byXuvd2zuH8A$bW1+7qhsYrgSMBupGM58f3m8QOJiLTEo4b3+WB41Y14', 'ADMIN')
ON DUPLICATE KEY UPDATE username=username;
