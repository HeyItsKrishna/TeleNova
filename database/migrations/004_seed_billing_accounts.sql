BEGIN;

TRUNCATE TABLE billing_accounts RESTART IDENTITY CASCADE;

INSERT INTO billing_accounts (
    customer_id,
    autopay_enabled,
    preferred_payment_method,
    current_balance
)
SELECT
    id,
    CASE
        WHEN account_number IN ('TN100001','TN100004','TN100006','TN100009')
        THEN TRUE
        ELSE FALSE
    END,
    CASE
        WHEN account_number IN ('TN100001','TN100004')
            THEN 'Credit Card'
        WHEN account_number IN ('TN100002','TN100006','TN100010')
            THEN 'UPI'
        WHEN account_number IN ('TN100003','TN100008')
            THEN 'Net Banking'
        ELSE 'Debit Card'
    END,
    CASE
        WHEN account_number='TN100001' THEN 0.00
        WHEN account_number='TN100002' THEN 249.50
        WHEN account_number='TN100003' THEN 799.00
        WHEN account_number='TN100004' THEN 0.00
        WHEN account_number='TN100005' THEN 125.00
        WHEN account_number='TN100006' THEN 0.00
        WHEN account_number='TN100007' THEN 420.75
        WHEN account_number='TN100008' THEN 999.00
        WHEN account_number='TN100009' THEN 0.00
        WHEN account_number='TN100010' THEN 89.00
        ELSE 0.00
    END
FROM customers;

COMMIT;