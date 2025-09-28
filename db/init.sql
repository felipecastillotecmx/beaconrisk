-- Schema básico para PoC CNP
DROP DATABASE IF EXISTS cnpdb;
CREATE DATABASE cnpdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cnpdb;

CREATE TABLE merchants (
  id VARCHAR(32) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  fraud_rate DECIMAL(5,4) NOT NULL DEFAULT 0.050
);

INSERT INTO merchants (id, name, fraud_rate) VALUES
('m_low',  'Tienda Segura', 0.010),
('m_mid',  'Tienda Media',  0.080),
('m_high', 'Tienda Riesgo', 0.150);

CREATE TABLE transactions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts DATETIME NOT NULL,
  merchant_id VARCHAR(32) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency CHAR(3) NOT NULL,
  country CHAR(2) NOT NULL,
  email VARCHAR(255) NOT NULL,
  ip VARCHAR(45) NOT NULL,
  device_id VARCHAR(64) NOT NULL,
  card_bin VARCHAR(8) NOT NULL,
  card_hash VARCHAR(128) NOT NULL,
  decision ENUM('APPROVE','REVIEW','DECLINE') NULL,
  risk_score DECIMAL(5,4) NULL,
  INDEX idx_ts (ts),
  INDEX idx_email (email),
  INDEX idx_ip (ip),
  INDEX idx_card (card_hash),
  INDEX idx_merchant (merchant_id),
  CONSTRAINT fk_t_m FOREIGN KEY (merchant_id) REFERENCES merchants(id)
) ENGINE=InnoDB;

-- Semillas
INSERT INTO transactions (ts, merchant_id, amount, currency, country, email, ip, device_id, card_bin, card_hash, decision, risk_score) VALUES
(NOW() - INTERVAL 25 MINUTE, 'm_high', 7800.00, 'MXN', 'MX', 'fraudster@example.com', '187.190.10.10', 'dev_x1', '520157', 'card_risky', NULL, NULL),
(NOW() - INTERVAL 20 MINUTE, 'm_high', 8200.00, 'MXN', 'MX', 'fraudster@example.com', '187.190.10.10', 'dev_x1', '520157', 'card_risky', NULL, NULL),
(NOW() - INTERVAL 15 MINUTE, 'm_high', 6400.00, 'MXN', 'MX', 'fraudster@example.com', '187.190.10.10', 'dev_x1', '520157', 'card_risky', NULL, NULL),
(NOW() - INTERVAL 10 MINUTE, 'm_high', 9000.00, 'MXN', 'MX', 'fraudster@example.com', '187.190.10.10', 'dev_x2', '520157', 'card_risky', NULL, NULL),
(NOW() - INTERVAL 5  MINUTE, 'm_high', 5000.00, 'MXN', 'MX', 'fraudster@example.com', '187.190.10.10', 'dev_x3', '520157', 'card_risky', NULL, NULL);

INSERT INTO transactions (ts, merchant_id, amount, currency, country, email, ip, device_id, card_bin, card_hash) VALUES
(NOW() - INTERVAL 40 MINUTE, 'm_mid', 1500.00, 'MXN', 'MX', 'repeat@example.com', '187.190.20.20', 'dev_y1', '520157', 'card_mid'),
(NOW() - INTERVAL 30 MINUTE, 'm_mid', 1200.00, 'MXN', 'MX', 'repeat@example.com', '187.190.20.20', 'dev_y1', '520157', 'card_mid');

INSERT INTO transactions (ts, merchant_id, amount, currency, country, email, ip, device_id, card_bin, card_hash) VALUES
(NOW() - INTERVAL 2 DAY, 'm_low', 300.00, 'MXN', 'MX', 'benign@example.com', '187.190.30.30', 'dev_z1', '520157', 'card_low');
