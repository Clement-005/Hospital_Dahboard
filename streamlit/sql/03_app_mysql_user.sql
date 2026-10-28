-- =====================================================================
-- Step 12: a limited MySQL account for the app, so it stops using root.
-- Run in MySQL Workbench as root, AFTER setup_security.sql.
-- First replace  ChooseAStrongPassword_2026  with your own password.
-- =====================================================================

CREATE USER IF NOT EXISTS 'hospital_app'@'localhost' IDENTIFIED BY 'ChooseAStrongPassword_2026';

-- Read and add records, but never update or delete them
GRANT SELECT, INSERT ON hospital_db.patients   TO 'hospital_app'@'localhost';
GRANT SELECT, INSERT ON hospital_db.admissions TO 'hospital_app'@'localhost';
GRANT SELECT, INSERT ON hospital_db.billings   TO 'hospital_app'@'localhost';

-- Can check logins, but cannot create or change staff accounts
GRANT SELECT ON hospital_db.app_users TO 'hospital_app'@'localhost';

-- Can add to the audit log and read it, but never edit or erase it
GRANT SELECT, INSERT ON hospital_db.audit_log TO 'hospital_app'@'localhost';

FLUSH PRIVILEGES;

-- Check what the app is allowed to do
SHOW GRANTS FOR 'hospital_app'@'localhost';

-- Then edit .streamlit/secrets.toml:
--   user = "hospital_app"
--   password = "ChooseAStrongPassword_2026"   (the one you chose above)
-- Keep using root only in Workbench for admin work.
