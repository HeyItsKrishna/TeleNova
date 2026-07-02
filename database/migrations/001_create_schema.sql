-- ==========================================================
-- TeleNova Enterprise Conversational AI Platform
-- Migration 001 - Initial Schema
-- ==========================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================================
-- Plans
-- ==========================================================

CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_code VARCHAR(30) UNIQUE NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    monthly_price NUMERIC(10,2) NOT NULL,
    data_limit_gb INTEGER,
    voice_minutes INTEGER,
    sms_limit INTEGER,
    features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Customers
-- ==========================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(30) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    account_status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Customer Subscriptions
-- ==========================================================

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(id),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE'
);

-- ==========================================================
-- Billing Accounts
-- ==========================================================

CREATE TABLE billing_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID UNIQUE NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    autopay_enabled BOOLEAN DEFAULT FALSE,
    preferred_payment_method VARCHAR(50),
    current_balance NUMERIC(10,2) DEFAULT 0
);

-- ==========================================================
-- Invoices
-- ==========================================================

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    billing_account_id UUID NOT NULL REFERENCES billing_accounts(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    billing_period_start DATE,
    billing_period_end DATE,
    amount NUMERIC(10,2),
    due_date DATE,
    payment_status VARCHAR(20),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Customer Devices
-- ==========================================================

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    device_name VARCHAR(100),
    imei VARCHAR(30),
    esim BOOLEAN DEFAULT FALSE,
    network_type VARCHAR(20),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Support Tickets
-- ==========================================================

CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    category VARCHAR(50),
    priority VARCHAR(20),
    status VARCHAR(20),
    summary TEXT,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Chat Sessions
-- ==========================================================

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id UUID REFERENCES customers(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- ==========================================================
-- Chat Messages
-- ==========================================================

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20),
    message TEXT,
    detected_intent VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Indexes
-- ==========================================================

CREATE INDEX idx_customer_account
ON customers(account_number);

CREATE INDEX idx_customer_phone
ON customers(phone_number);

CREATE INDEX idx_ticket_customer
ON support_tickets(customer_id);

CREATE INDEX idx_invoice_account
ON invoices(billing_account_id);

CREATE INDEX idx_chat_customer
ON chat_sessions(customer_id);

CREATE INDEX idx_chat_session
ON chat_messages(session_id);

CREATE INDEX idx_subscription_customer
ON subscriptions(customer_id);
