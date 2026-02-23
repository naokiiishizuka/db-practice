CREATE TABLE Comments(
    comment_id SERIAL PRIMARY KEY,
    parent_id BIGINT CHECK (parent_id >= 0),
    comment TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES Comments(comment_id)
)
