-- =====================================================================
-- Steps 10 and 11: staff users, roles and the audit log
-- Run this ONCE in MySQL Workbench, logged in as root.
-- =====================================================================
USE hospital_db;

-- ---------- Staff accounts (step 10) ----------
CREATE TABLE IF NOT EXISTS app_users (
  user_id       INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  full_name     VARCHAR(100),
  password_hash VARCHAR(100) NOT NULL,          -- bcrypt hash, never the real password
  role          ENUM('front_desk','doctor','billing','admin') NOT NULL,
  is_active     TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- Four starter accounts, one per role.
-- Passwords:  admin = Admin@2026!   frontdesk = Front@2026!   drmensah = Doctor@2026!   billing1 = Billing@2026!
-- Change them before showing the app to anyone (use create_user.py to make new hashes).
INSERT INTO app_users (username, full_name, password_hash, role) VALUES
('admin',     'System Administrator', '$2b$12$Fb7w60zrJxasaXEmuXm6rug64FgtY5r1qFFCxvBKbgqz3RPSmyQkq', 'admin'),
('frontdesk', 'Front Desk Officer',   '$2b$12$zad8hQdlPBXqwlGRw2i30OCmuMyWbYUguU7DUNPh1CgPt8rMvWoFq', 'front_desk'),
('drmensah',  'Dr. Mensah',           '$2b$12$OyapILz/8fg31az71Z8RW.82tE9opyZskfgPhNT/2u9GGdWveviwK', 'doctor'),
('billing1',  'Billing Officer',      '$2b$12$5WYSUBVWj0wnlRGSND59ROUNRuxFPUmOZeXVq3X4UktEamVLYRNNO', 'billing');

-- ---------- Audit log (step 11) ----------
CREATE TABLE IF NOT EXISTS audit_log (
  log_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NULL,
  username    VARCHAR(50),
  action      VARCHAR(20)  NOT NULL,      -- LOGIN, LOGIN_FAILED, LOGOUT, VIEW, INSERT
  table_name  VARCHAR(30),
  record_id   VARCHAR(30),
  details     VARCHAR(255),
  logged_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_logged_at (logged_at),
  FOREIGN KEY (user_id) REFERENCES app_users(user_id)
);

-- Check
SELECT user_id, username, full_name, role FROM app_users;
