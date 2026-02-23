CREATE TABLE nested_set_comments(
    comment_id SERIAL PRIMARY KEY,
    nsleft INTEGER NOT NULL, 
    nsright INTEGER NOT NULL, 
    comment TEXT NOT NULL   
)
