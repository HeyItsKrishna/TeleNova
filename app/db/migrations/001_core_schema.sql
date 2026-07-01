CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE account_status AS ENUM (
    'active',
    'suspended_voluntary',
    'suspended_nonpayment',
    'restricted',
    'closed'
);

CREATE TYPE plan_type AS ENUM (
    'starter',
    'connect',
    'unlimited_pro',
    'business_pro'
);

CREATE TYPE ticket_category AS ENUM (
    'billing',
    'network',
    'account',
    'device',
    'general'
);

CREATE TYPE ticket_status AS ENUM (
    'open',
    'in_progress',
    'pending_customer',
    'resolved',
    'closed'
);

CREATE TABLE accounts (
    account_number VARCHAR(10) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    status account_status NOT NULL DEFAULT 'active',
    plan plan_type NOT NULL,
    balance_due NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    due_date DATE,
    autopay_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_account_number_format CHECK (account_number ~ '^TN-[0-9]{6}$'),
    CONSTRAINT chk_balance_non_negative CHECK (balance_due >= 0)
);

CREATE TABLE billing_cycles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(10) NOT NULL REFERENCES accounts(account_number) ON DELETE CASCADE,
    cycle_label VARCHAR(20) NOT NULL,
    plan_charge NUMERIC(10, 2) NOT NULL,
    taxes_and_fees NUMERIC(10, 2) NOT NULL DEFAULT 0,
    add_ons NUMERIC(10, 2) NOT NULL DEFAULT 0,
    overages NUMERIC(10, 2) NOT NULL DEFAULT 0,
    credits NUMERIC(10, 2) NOT NULL DEFAULT 0,
    total NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_account_cycle UNIQUE (account_number, cycle_label)
);

CREATE TABLE billing_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    billing_cycle_id UUID NOT NULL REFERENCES billing_cycles(id) ON DELETE CASCADE,
    description VARCHAR(255) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    line_order SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(10) NOT NULL REFERENCES accounts(account_number) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    method VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE data_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(10) NOT NULL REFERENCES accounts(account_number) ON DELETE CASCADE,
    cycle_end DATE NOT NULL,
    used_gb NUMERIC(8, 2) NOT NULL DEFAULT 0,
    plan_limit_gb NUMERIC(8, 2),
    priority_gb_used NUMERIC(8, 2),
    priority_gb_limit NUMERIC(8, 2),
    hotspot_used_gb NUMERIC(8, 2) NOT NULL DEFAULT 0,
    hotspot_limit_gb NUMERIC(8, 2) NOT NULL DEFAULT 0,
    CONSTRAINT uq_account_cycle_end UNIQUE (account_number, cycle_end)
);

CREATE TABLE network_diagnostics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(10) NOT NULL REFERENCES accounts(account_number) ON DELETE CASCADE,
    sim_status VARCHAR(30) NOT NULL,
    network_registration VARCHAR(100) NOT NULL,
    signal_strength VARCHAR(50),
    technology VARCHAR(20),
    last_data_session TIMESTAMPTZ,
    volte_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    issues_detected TEXT[] NOT NULL DEFAULT '{}',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE network_outages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zip_code VARCHAR(10) NOT NULL,
    incident_id VARCHAR(30) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL,
    network_type VARCHAR(20),
    started_at TIMESTAMPTZ NOT NULL,
    estimated_resolution TIMESTAMPTZ,
    affected_services TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE tickets (
    ticket_id VARCHAR(12) PRIMARY KEY,
    account_number VARCHAR(10) NOT NULL REFERENCES accounts(account_number) ON DELETE CASCADE,
    category ticket_category NOT NULL,
    status ticket_status NOT NULL DEFAULT 'open',
    description TEXT NOT NULL,
    assigned_team VARCHAR(100),
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_ticket_id_format CHECK (ticket_id ~ '^(BIL|NET|ACC|DEV|GEN)-[0-9]{5}$')
);

CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_billing_cycles_account ON billing_cycles(account_number, created_at DESC);
CREATE INDEX idx_payments_account ON payments(account_number, payment_date DESC);
CREATE INDEX idx_data_usage_account ON data_usage(account_number, cycle_end DESC);
CREATE INDEX idx_diagnostics_account ON network_diagnostics(account_number, recorded_at DESC);
CREATE INDEX idx_outages_zip ON network_outages(zip_code);
CREATE INDEX idx_tickets_account ON tickets(account_number, created_at DESC);
CREATE INDEX idx_tickets_status ON tickets(status);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
