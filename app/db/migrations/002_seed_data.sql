INSERT INTO accounts (account_number, customer_name, status, plan, balance_due, due_date, autopay_enabled) VALUES
('TN-100001', 'Maria Chen', 'active', 'unlimited_pro', 65.00, '2025-11-15', TRUE),
('TN-100002', 'James Okafor', 'suspended_nonpayment', 'connect', 135.50, '2025-10-15', FALSE),
('TN-100003', 'Aisha Rahman', 'active', 'starter', 0.00, '2025-11-22', TRUE),
('TN-100004', 'Daniel Petrov', 'active', 'business_pro', 275.00, '2025-11-10', TRUE);

WITH cycle AS (
    INSERT INTO billing_cycles (account_number, cycle_label, plan_charge, taxes_and_fees, add_ons, overages, credits, total)
    VALUES ('TN-100001', 'current', 65.00, 9.75, 12.00, 0.00, -5.00, 81.75)
    RETURNING id
)
INSERT INTO billing_line_items (billing_cycle_id, description, amount, line_order)
SELECT id, description, amount, line_order FROM cycle, (VALUES
    ('Unlimited Pro Plan', 65.00, 1),
    ('Device Protection', 12.00, 2),
    ('AutoPay Discount', -5.00, 3),
    ('Regulatory Recovery Fee', 3.50, 4),
    ('State & Local Taxes', 6.25, 5)
) AS items(description, amount, line_order);

WITH cycle AS (
    INSERT INTO billing_cycles (account_number, cycle_label, plan_charge, taxes_and_fees, add_ons, overages, credits, total)
    VALUES ('TN-100002', 'current', 45.00, 7.25, 0.00, 10.00, 0.00, 62.25)
    RETURNING id
)
INSERT INTO billing_line_items (billing_cycle_id, description, amount, line_order)
SELECT id, description, amount, line_order FROM cycle, (VALUES
    ('Connect Plan', 45.00, 1),
    ('Data Overage (1 GB)', 10.00, 2),
    ('Regulatory Recovery Fee', 3.50, 3),
    ('State & Local Taxes', 3.75, 4)
) AS items(description, amount, line_order);

INSERT INTO payments (account_number, payment_date, amount, method, status) VALUES
('TN-100001', '2025-10-15', 81.75, 'AutoPay (Visa •••• 4242)', 'Paid'),
('TN-100001', '2025-09-15', 81.75, 'AutoPay (Visa •••• 4242)', 'Paid'),
('TN-100001', '2025-08-15', 81.75, 'AutoPay (Visa •••• 4242)', 'Paid'),
('TN-100002', '2025-10-01', 0.00, '—', 'Missed'),
('TN-100002', '2025-09-22', 62.25, 'Manual (Debit •••• 8910)', 'Paid (Late)'),
('TN-100002', '2025-08-22', 52.25, 'Manual (Debit •••• 8910)', 'Paid');

INSERT INTO data_usage (account_number, cycle_end, used_gb, plan_limit_gb, priority_gb_used, priority_gb_limit, hotspot_used_gb, hotspot_limit_gb) VALUES
('TN-100001', '2025-11-15', 45.20, NULL, 45.20, 100, 12.10, 50),
('TN-100002', '2025-11-22', 22.80, 25, NULL, NULL, 8.50, 10),
('TN-100003', '2025-11-22', 3.10, 5, NULL, NULL, 0.00, 0);

INSERT INTO network_diagnostics (account_number, sim_status, network_registration, signal_strength, technology, last_data_session, volte_enabled, issues_detected) VALUES
('TN-100001', 'Active', 'Registered (Home Network)', '-85 dBm (Good)', '5G NR', '2025-10-31 15:22:00+00', TRUE, '{}'),
('TN-100002', 'Active', 'Registered (Roaming - AT&T)', '-102 dBm (Weak)', 'LTE', '2025-10-31 12:10:00+00', FALSE, ARRAY['VoLTE not enabled — enabling may improve call quality', 'Weak signal — consider Wi-Fi Calling']),
('TN-100003', 'Active', 'Not Registered', 'No Signal', 'None', '2025-10-30 09:45:00+00', FALSE, ARRAY['Device not registered on network', 'Possible SIM issue or device outside coverage area']);

INSERT INTO network_outages (zip_code, incident_id, status, network_type, started_at, estimated_resolution, affected_services) VALUES
('90210', 'INC-2024-789', 'Outage Active', '5G/LTE', '2025-10-31 14:30:00+00', '2025-10-31 18:00:00+00', ARRAY['Data', 'Voice']),
('94102', 'INC-2024-790', 'Degraded Performance', 'LTE', '2025-10-31 10:00:00+00', '2025-11-01 08:00:00+00', ARRAY['Data speeds reduced']);

INSERT INTO tickets (ticket_id, account_number, category, status, description, assigned_team, resolution_notes, created_at, updated_at) VALUES
('BIL-78231', 'TN-100001', 'billing', 'in_progress', 'Customer disputes data overage charge', 'Billing Specialist', NULL, '2025-10-28', '2025-10-30'),
('NET-45901', 'TN-100001', 'network', 'resolved', 'No service reported in home area', 'Network Ops', 'Tower maintenance completed in your area.', '2025-10-25', '2025-10-26'),
('ACC-12344', 'TN-100002', 'account', 'pending_customer', 'Identity verification required for plan change', 'Account Specialist', NULL, '2025-10-29', '2025-10-29'),
('GEN-99102', 'TN-100003', 'general', 'open', 'General inquiry about plan features', 'Support Queue', NULL, '2025-10-31', '2025-10-31');
