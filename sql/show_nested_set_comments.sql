select c2.*
FROM nested_set_comments AS c1
    JOIN nested_set_comments AS c2
        ON c2.nsleft BETWEEN c1.nsleft AND c1.nsright
WHERE c1.comment_id = 4
