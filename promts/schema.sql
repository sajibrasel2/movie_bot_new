-- Minimal schema for Bangladesh Politics Hub bot
-- Run this once on the MySQL server

CREATE TABLE IF NOT EXISTS telegram_channel_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_channel VARCHAR(255) NOT NULL UNIQUE,
    last_message_id BIGINT DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS telegram_collected_posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_channel VARCHAR(255) NOT NULL,
    source_message_id BIGINT NOT NULL,
    source_title VARCHAR(255) NULL,
    text TEXT,
    media_path VARCHAR(512) NULL,
    media_type ENUM('photo','document','video','audio','voice','animation','other') NULL,
    status ENUM('pending','sent','failed') NOT NULL DEFAULT 'pending',
    fail_reason TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    UNIQUE KEY uq_source_message (source_channel, source_message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
