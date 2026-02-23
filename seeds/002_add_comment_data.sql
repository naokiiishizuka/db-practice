INSERT INTO comments (comment_id, parent_id, comment)
VALUES
    (1, null, 'コメント1'),
    (2, 1, 'コメント1の子1'),
    (3, 1, 'コメント1の子2'),
    (4, 2, 'コメント2の子1'),
    (5, null, 'コメント5'),
    (6, 5, 'コメント5の子')
ON CONFLICT (comment_id) DO NOTHING;
