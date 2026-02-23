UPDATE nested_set_comments
    SET nsleft = CASE WHEN nsleft > 7 THEN nsleft+2 ELSE nsleft END,
        nsright = nsright + 2
WHERE nsright >= 7;
