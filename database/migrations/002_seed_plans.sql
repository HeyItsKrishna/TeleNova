BEGIN;

TRUNCATE TABLE plans RESTART IDENTITY CASCADE;

INSERT INTO plans (
    plan_code,
    plan_name,
    monthly_price,
    data_limit_gb,
    voice_minutes,
    sms_limit,
    features
)
VALUES
(
    'BASIC_5G',
    'Basic 5G',
    299.00,
    20,
    500,
    100,
    '{"5g": true, "international": false, "hotspot": true}'
),
(
    'STANDARD_5G',
    'Standard 5G',
    499.00,
    75,
    1000,
    500,
    '{"5g": true, "international": false, "hotspot": true}'
),
(
    'PREMIUM_UNLIMITED',
    'Premium Unlimited',
    799.00,
    NULL,
    NULL,
    NULL,
    '{"5g": true, "international": true, "hotspot": true, "ott": ["Netflix","Prime"]}'
),
(
    'FAMILY_MAX',
    'Family Max',
    1499.00,
    NULL,
    NULL,
    NULL,
    '{"family": true, "connections": 5, "international": true}'
),
(
    'STUDENT_SAVER',
    'Student Saver',
    399.00,
    50,
    1000,
    500,
    '{"student": true, "5g": true}'
);

COMMIT;