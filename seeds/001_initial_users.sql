INSERT INTO users (email, full_name)
VALUES
    ('demo1@example.com', 'Demo User 1'),
    ('demo2@example.com', 'Demo User 2')
ON CONFLICT (email) DO NOTHING;
