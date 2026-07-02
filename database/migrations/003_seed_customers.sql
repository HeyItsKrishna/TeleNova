BEGIN;

TRUNCATE TABLE customers RESTART IDENTITY CASCADE;

INSERT INTO customers (
    account_number,
    first_name,
    last_name,
    email,
    phone_number,
    account_status,
    plan_id
)
VALUES

(
'TN100001',
'Rahul',
'Sharma',
'rahul.sharma@telenova.demo',
'9876543201',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='BASIC_5G')
),

(
'TN100002',
'Priya',
'Verma',
'priya.verma@telenova.demo',
'9876543202',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='STANDARD_5G')
),

(
'TN100003',
'Amit',
'Patel',
'amit.patel@telenova.demo',
'9876543203',
'SUSPENDED',
(SELECT id FROM plans WHERE plan_code='PREMIUM_UNLIMITED')
),

(
'TN100004',
'Neha',
'Gupta',
'neha.gupta@telenova.demo',
'9876543204',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='FAMILY_MAX')
),

(
'TN100005',
'Arjun',
'Mehta',
'arjun.mehta@telenova.demo',
'9876543205',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='STUDENT_SAVER')
),

(
'TN100006',
'Sneha',
'Reddy',
'sneha.reddy@telenova.demo',
'9876543206',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='STANDARD_5G')
),

(
'TN100007',
'Karan',
'Malhotra',
'karan.malhotra@telenova.demo',
'9876543207',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='PREMIUM_UNLIMITED')
),

(
'TN100008',
'Ananya',
'Joshi',
'ananya.joshi@telenova.demo',
'9876543208',
'INACTIVE',
(SELECT id FROM plans WHERE plan_code='BASIC_5G')
),

(
'TN100009',
'Rohit',
'Singh',
'rohit.singh@telenova.demo',
'9876543209',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='FAMILY_MAX')
),

(
'TN100010',
'Pooja',
'Nair',
'pooja.nair@telenova.demo',
'9876543210',
'ACTIVE',
(SELECT id FROM plans WHERE plan_code='STUDENT_SAVER')
);

COMMIT;