BEGIN;

TRUNCATE TABLE chat_messages RESTART IDENTITY CASCADE;

INSERT INTO chat_messages (
    session_id,
    role,
    message,
    detected_intent
)

SELECT
cs.id,
'user',
'Why is my internet slow today?',
'network_issue'
FROM chat_sessions cs

UNION ALL

SELECT
cs.id,
'assistant',
'I''m checking your network connection. Please hold for a moment.',
'network_issue'
FROM chat_sessions cs

UNION ALL

SELECT
cs.id,
'user',
'Can you tell me my current bill?',
'billing_inquiry'
FROM chat_sessions cs

UNION ALL

SELECT
cs.id,
'assistant',
'Your billing information has been retrieved successfully.',
'billing_inquiry'
FROM chat_sessions cs;

COMMIT;