# Solutions Guide: AI-Powered Product Recommendation System 🎯
> This guide provides detailed solutions and explanations for all exercises and challenges in the workshop.

## Part 1: Database Structure Solutions

### 🤔 Question #1: TEXT[] vs. Junction Table
**Why use TEXT[] for category_preferences instead of a junction table?**

**Solution:**
```sql
-- Current approach using TEXT[]
CREATE TABLE user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    category_preferences TEXT[],
    -- other fields...
);

-- Alternative approach with junction table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name TEXT UNIQUE
);

CREATE TABLE user_category_preferences (
    user_id INTEGER REFERENCES users(user_id),
    category_id INTEGER REFERENCES categories(category_id),
    PRIMARY KEY (user_id, category_id)
);
```

**Trade-offs Analysis:**
1. **TEXT[] Approach**
   - ✅ Pros:
     - Simpler queries for reading preferences
     - Faster retrieval (single table access)
     - More flexible for user-specific category names
     - Easier to update all preferences at once
   - ❌ Cons:
     - No referential integrity for categories
     - More complex to query individual categories
     - Potential data inconsistency

2. **Junction Table Approach**
   - ✅ Pros:
     - Maintains referential integrity
     - Better for category analytics
     - Normalized design
   - ❌ Cons:
     - More complex queries
     - Multiple joins needed
     - Higher query overhead

**Choice Rationale:** TEXT[] was chosen for simplicity and performance in this case, as the category list is relatively stable and the primary use case is reading all preferences at once.

## Part 2: Search Methods Solutions

### 🧪 Query Test Results

1. **"Wireless blutooth headfones" (misspelled query)**

**Keyword Search Results:**
```sql
-- Low relevance due to exact match failure
SELECT COUNT(*) FROM (
    SELECT "productId"
    FROM bedrock_integration.product_catalog
    WHERE to_tsvector('english', product_description) @@ 
          plainto_tsquery('english', 'Wireless blutooth headfones')
) subq;
-- Returns: 0 matches
```

**Semantic Search Results:**
```python
# High relevance despite misspellings
query_embedding = generate_embedding("Wireless blutooth headfones")
results = similarity_search(query_embedding, top_k=3)

# Sample results:
# 1. "Wireless Bluetooth Headphones with Noise Cancellation" (similarity: 0.92)
# 2. "Bluetooth Wireless Earbuds with Charging Case" (similarity: 0.89)
# 3. "Premium Wireless Over-Ear Headphones" (similarity: 0.85)
```

2. **"Something to keep my drinks cold"**

**Keyword Search Results:**
```sql
-- Limited matches due to literal interpretation
SELECT COUNT(*) FROM (
    SELECT "productId"
    FROM bedrock_integration.product_catalog
    WHERE to_tsvector('english', product_description) @@ 
          plainto_tsquery('english', 'Something to keep my drinks cold')
) subq;
-- Returns: Very few or no exact matches
```

**Semantic Search Results:**
```python
# Understanding intent and context
query_embedding = generate_embedding("Something to keep my drinks cold")
results = similarity_search(query_embedding, top_k=3)

# Sample results:
# 1. "Insulated Cooler Bag with Shoulder Strap" (similarity: 0.88)
# 2. "Portable Mini Fridge for Travel" (similarity: 0.85)
# 3. "Stainless Steel Vacuum Insulated Water Bottle" (similarity: 0.82)
```

## Part 3: LLM Prompt Enhancement Solutions

### 🎮 Enhanced Prompt Templates

1. **Price-Sensitive Recommendations:**
```python
recommendations_prompt = f"""
Based on the user's preferences: "{user_preferences}"
And considering these products: {results.to_dict('records')}

Please provide {top_k} personalized recommendations while:
1. Strictly adhering to the user's budget constraints
2. Prioritizing best value-for-money options
3. Including both premium and budget alternatives when appropriate
4. Explaining price-performance trade-offs
5. Highlighting any ongoing deals or discounts

For each recommendation, explain:
- Why it provides good value
- How it compares to higher/lower priced alternatives
- Long-term cost considerations (durability, maintenance)
"""
```

2. **Seasonal Recommendations:**
```python
recommendations_prompt = f"""
Based on the user's preferences: "{user_preferences}"
And considering these products: {results.to_dict('records')}
Current season: {current_season}
Upcoming season: {next_season}

Please provide {top_k} personalized recommendations while:
1. Prioritizing season-appropriate items
2. Suggesting versatile products for seasonal transitions
3. Considering regional weather patterns
4. Including both immediate and upcoming seasonal needs
5. Highlighting seasonal features and benefits

For each recommendation, explain:
- Seasonal appropriateness
- Weather adaptability
- Transition potential to next season
"""
```

3. **Brand Preference-Aware:**
```python
recommendations_prompt = f"""
Based on the user's preferences: "{user_preferences}"
Previous purchases: {purchase_history}
Brand interactions: {brand_interactions}
Available products: {results.to_dict('records')}

Please provide {top_k} personalized recommendations while:
1. Considering previously purchased brands
2. Suggesting similar brands in style/quality
3. Balancing brand loyalty with product quality
4. Including mix of familiar and new brands
5. Explaining brand value propositions

For each recommendation, explain:
- Brand alignment with preferences
- Quality comparison with familiar brands
- Unique brand advantages
- Alternative brand options
"""
```