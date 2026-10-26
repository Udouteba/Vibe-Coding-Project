-- 给排水智库 - 建库建表脚本（MySQL 8.0+）
-- 说明：应用启动时也会通过 Base.metadata.create_all 自动建表，
--       并自动播种演示账号；本脚本用于手动初始化或参考完整 DDL。

CREATE DATABASE IF NOT EXISTS drainage DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE drainage;

CREATE TABLE IF NOT EXISTS users (
  id            BIGINT NOT NULL AUTO_INCREMENT,
  username      VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role          VARCHAR(16) NOT NULL DEFAULT 'student',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS documents (
  id          BIGINT NOT NULL AUTO_INCREMENT,
  title       VARCHAR(255) NOT NULL,
  code        VARCHAR(128) NOT NULL DEFAULT '',
  version     VARCHAR(64)  NOT NULL DEFAULT '',
  category    VARCHAR(64)  NOT NULL DEFAULT '其他',
  status      VARCHAR(32)  NOT NULL DEFAULT 'pending',
  chunk_count INT NOT NULL DEFAULT 0,
  file_name   VARCHAR(255) NOT NULL DEFAULT '',
  file_path   VARCHAR(512) NOT NULL DEFAULT '',
  error       VARCHAR(1024) NOT NULL DEFAULT '',
  uploaded_by BIGINT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_documents_category (category),
  KEY idx_documents_uploaded_by (uploaded_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS document_chunks (
  id           BIGINT NOT NULL AUTO_INCREMENT,
  document_id  BIGINT NOT NULL,
  chunk_index  INT NOT NULL,
  content      TEXT NOT NULL,
  chapter      VARCHAR(128) NOT NULL DEFAULT '',
  clause       VARCHAR(128) NOT NULL DEFAULT '',
  vector_id    VARCHAR(128) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY idx_chunks_document_id (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS conversations (
  id          BIGINT NOT NULL AUTO_INCREMENT,
  user_id     BIGINT NOT NULL,
  title       VARCHAR(255) NOT NULL DEFAULT '新对话',
  is_pinned   TINYINT(1) NOT NULL DEFAULT 0,
  is_archived TINYINT(1) NOT NULL DEFAULT 0,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_conversations_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS messages (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  conversation_id BIGINT NOT NULL,
  role            VARCHAR(16) NOT NULL,
  content         TEXT NOT NULL,
  citations       JSON NULL,
  low_confidence  TINYINT(1) NOT NULL DEFAULT 0,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_messages_conversation_id (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS search_presets (
  id           BIGINT NOT NULL AUTO_INCREMENT,
  user_id      BIGINT NOT NULL,
  name         VARCHAR(128) NOT NULL,
  document_ids JSON NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_presets_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 演示账号（密码哈希为 bcrypt；应用启动时若账号不存在也会自动播种）
INSERT IGNORE INTO users (username, password_hash, role) VALUES
  ('admin', '$2b$12$C8IJb5fL8x.PcD6fbSz0o.lRmqqKYRXmsM/sDGr8crc0eOVks.t9S', 'admin'),
  ('aaa',   '$2b$12$P1sat/dOyQVv5nNNOEeOxO/Yc0wasVm56.t/r31.J4mGnixHjCC/2', 'student'),
  ('bbb',   '$2b$12$P1sat/dOyQVv5nNNOEeOxO/Yc0wasVm56.t/r31.J4mGnixHjCC/2', 'student');
