-- hospital_db schema (MySQL 8). The live system uses these tables; the online demo loads the same
-- columns from CSV into an in-memory database.
CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

CREATE TABLE patients (
  patient_id  VARCHAR(10) PRIMARY KEY,
  name        VARCHAR(100) NOT NULL,
  age         INT,
  gender      VARCHAR(10),
  blood_type  VARCHAR(3),
  CONSTRAINT chk_age CHECK (age BETWEEN 0 AND 120)
);

CREATE TABLE admissions (
  admission_id      VARCHAR(10) PRIMARY KEY,
  patient_id        VARCHAR(10) NOT NULL,
  date_of_admission DATE NOT NULL,
  discharge_date    DATE NULL,
  admission_type    VARCHAR(20),
  hospital          VARCHAR(100),
  doctor            VARCHAR(100),
  room_number       INT,
  medical_condition VARCHAR(60),
  medication        VARCHAR(60),
  test_results      VARCHAR(20),
  FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
  CONSTRAINT chk_dates CHECK (discharge_date IS NULL OR discharge_date >= date_of_admission)
);

CREATE TABLE billings (
  bill_id            VARCHAR(10) PRIMARY KEY,
  admission_id       VARCHAR(10) NOT NULL,
  billing_amount     DECIMAL(12,2) NULL,
  insurance_provider VARCHAR(60),
  FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
  CONSTRAINT chk_bill_nonneg CHECK (billing_amount >= 0)
);

CREATE TABLE app_users (
  user_id       INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(50) NOT NULL UNIQUE,
  full_name     VARCHAR(100),
  password_hash VARCHAR(100) NOT NULL,
  role          ENUM('front_desk','doctor','billing','admin') NOT NULL,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
  log_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NULL,
  username   VARCHAR(50),
  action     VARCHAR(20) NOT NULL,
  table_name VARCHAR(30),
  record_id  VARCHAR(30),
  details    VARCHAR(255),
  logged_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_logged_at (logged_at),
  FOREIGN KEY (user_id) REFERENCES app_users(user_id)
);

-- Least-privilege account used by the app (never root)
-- CREATE USER 'hospital_app'@'localhost' IDENTIFIED BY '<password>';
-- GRANT SELECT, INSERT ON hospital_db.patients   TO 'hospital_app'@'localhost';
-- GRANT SELECT, INSERT ON hospital_db.admissions TO 'hospital_app'@'localhost';
-- GRANT SELECT, INSERT ON hospital_db.billings   TO 'hospital_app'@'localhost';
-- GRANT SELECT         ON hospital_db.app_users  TO 'hospital_app'@'localhost';
-- GRANT SELECT, INSERT ON hospital_db.audit_log  TO 'hospital_app'@'localhost';
