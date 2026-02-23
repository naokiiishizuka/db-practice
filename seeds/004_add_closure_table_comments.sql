INSERT INTO closure_table_comments (comment_id, comment)
VALUES
    (1, 'コメント1'),
    (2, 'コメント1の子1'),
    (3, 'コメント2の子'),
    (4, 'コメント1の子2'),
    (5, 'コメント4の子1'),
    (6, 'コメント4の子2'),
    (7, 'コメント6の子')
ON CONFLICT (comment_id) DO NOTHING;
