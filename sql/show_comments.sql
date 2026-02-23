SELECT
    c.comment_id,
    c.parent_id,
    c.comment,
    COALESCE(p.comment, 'ROOT') AS parent_comment
FROM comments c
LEFT JOIN comments p ON p.comment_id = c.parent_id
ORDER BY c.comment_id;
