BEGIN;

TRUNCATE TABLE chat_sessions RESTART IDENTITY CASCADE;

INSERT INTO chat_sessions (
    session_id,
    customer_id,
    started_at,
    ended_at
)
SELECT
    'SESSION-' || account_number,
    id,
    NOW() - INTERVAL '7 days' + (ROW_NUMBER() OVER ()) * INTERVAL '4 hours',
    NOW() - INTERVAL '7 days' + (ROW_NUMBER() OVER ()) * INTERVAL '4 hours' + INTERVAL '18 minutes'
FROM customers
ORDER BY account_number;

COMMIT;