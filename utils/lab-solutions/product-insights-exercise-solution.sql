SELECT DISTINCT ON (category_name) 
        category_name, product_description, boughtinlastmonth
FROM bedrock_integration.product_catalog
ORDER BY category_name, boughtinlastmonth DESC
LIMIT %s