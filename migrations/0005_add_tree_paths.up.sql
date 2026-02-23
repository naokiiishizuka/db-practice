CREATE TABLE tree_paths(
    ancestor BIGINT NOT NULL,
    descendant BIGINT NOT NULL,
    PRIMARY KEY(ancestor, descendant),
    FOREIGN KEY (ancestor) REFERENCES closure_table_comments(comment_id),
    FOREIGN KEY (descendant) REFERENCES closure_table_comments(comment_id)
)
