WITH RECURSIVE comment_tree AS (
    SELECT
        comment_id,
        parent_id,
        comment,
        0::INT AS level,
        LPAD(comment_id::TEXT, 4, '0') AS sort_key
    FROM comments
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        c.comment_id,
        c.parent_id,
        c.comment,
        ct.level + 1 AS level,
        ct.sort_key || '.' || LPAD(c.comment_id::TEXT, 4, '0') AS sort_key
    FROM comments c
    JOIN comment_tree ct ON c.parent_id = ct.comment_id
)
SELECT
    comment_id,
    parent_id,
    level,
    repeat('  ', level) || '- ' || comment AS indented_comment
FROM comment_tree
ORDER BY sort_key;
