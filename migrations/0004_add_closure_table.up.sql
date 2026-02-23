CREATE TABLE closure_table_comments(
    comment_id SERIAL PRIMARY KEY,
    comment_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    comment TEXT NOT NULL
)
