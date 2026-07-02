BEGIN;

TRUNCATE TABLE support_tickets RESTART IDENTITY CASCADE;

INSERT INTO support_tickets (
    ticket_number,
    customer_id,
    category,
    priority,
    status,
    summary,
    resolution
)
SELECT
    CASE account_number
        WHEN 'TN100001' THEN 'TKT-000001'
        WHEN 'TN100002' THEN 'TKT-000002'
        WHEN 'TN100003' THEN 'TKT-000003'
        WHEN 'TN100004' THEN 'TKT-000004'
        WHEN 'TN100005' THEN 'TKT-000005'
        WHEN 'TN100006' THEN 'TKT-000006'
        WHEN 'TN100007' THEN 'TKT-000007'
        WHEN 'TN100008' THEN 'TKT-000008'
        WHEN 'TN100009' THEN 'TKT-000009'
        WHEN 'TN100010' THEN 'TKT-000010'
    END,

    id,

    CASE account_number
        WHEN 'TN100001' THEN 'Billing'
        WHEN 'TN100002' THEN 'Network'
        WHEN 'TN100003' THEN 'Plan'
        WHEN 'TN100004' THEN 'Device'
        WHEN 'TN100005' THEN 'Billing'
        WHEN 'TN100006' THEN 'SIM'
        WHEN 'TN100007' THEN 'Roaming'
        WHEN 'TN100008' THEN 'Network'
        WHEN 'TN100009' THEN 'Plan'
        WHEN 'TN100010' THEN 'General'
    END,

    CASE account_number
        WHEN 'TN100003' THEN 'HIGH'
        WHEN 'TN100008' THEN 'HIGH'
        WHEN 'TN100007' THEN 'MEDIUM'
        ELSE 'LOW'
    END,

    CASE account_number
        WHEN 'TN100001' THEN 'RESOLVED'
        WHEN 'TN100002' THEN 'OPEN'
        WHEN 'TN100003' THEN 'IN_PROGRESS'
        WHEN 'TN100004' THEN 'RESOLVED'
        WHEN 'TN100005' THEN 'OPEN'
        WHEN 'TN100006' THEN 'RESOLVED'
        WHEN 'TN100007' THEN 'IN_PROGRESS'
        WHEN 'TN100008' THEN 'OPEN'
        WHEN 'TN100009' THEN 'RESOLVED'
        WHEN 'TN100010' THEN 'OPEN'
    END,

    CASE account_number
        WHEN 'TN100001' THEN 'Incorrect monthly bill generated.'
        WHEN 'TN100002' THEN 'Frequent 5G network drops.'
        WHEN 'TN100003' THEN 'Requested upgrade to Premium Unlimited.'
        WHEN 'TN100004' THEN 'Unable to activate eSIM.'
        WHEN 'TN100005' THEN 'Outstanding payment clarification.'
        WHEN 'TN100006' THEN 'SIM replacement request.'
        WHEN 'TN100007' THEN 'International roaming not working.'
        WHEN 'TN100008' THEN 'Poor signal strength in home area.'
        WHEN 'TN100009' THEN 'Family plan member addition.'
        WHEN 'TN100010' THEN 'General account enquiry.'
    END,

    CASE account_number
        WHEN 'TN100001' THEN 'Billing adjustment applied successfully.'
        WHEN 'TN100004' THEN 'eSIM activated successfully.'
        WHEN 'TN100006' THEN 'Replacement SIM issued.'
        WHEN 'TN100009' THEN 'Family member added successfully.'
        ELSE NULL
    END

FROM customers;

COMMIT;