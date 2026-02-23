SELECT c.*
FROM closure_table_comments AS c
    JOIN tree_paths AS t ON c.comment_id = t.descendant
WHERE t.ancestor = 4;
