INSERT INTO nested_set_comments (comment_id, nsleft, nsright, comment)
VALUES
    (1, 1, 14, 'コメント1'),
    (2, 2, 5, 'コメント1の子1'),
    (3, 3, 4, 'コメント1の子2'),
    (4, 6, 13, 'コメント1の子2'),
    (5, 7, 8, 'コメント4の子1'),
    (6, 9, 12, 'コメント4の子2'),
    (7, 10, 11, 'コメント6の子')
ON CONFLICT (comment_id) DO NOTHING;
