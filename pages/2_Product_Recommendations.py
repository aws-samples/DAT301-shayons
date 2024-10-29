import streamlit as st
import psycopg
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import boto3
import json
import base64
from botocore.exceptions import ClientError
import time

# Load environment variables and set up configurations
load_dotenv()

# Initialize Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime', region_name=os.environ.get('AWS_REGION')
)

# Constants and configurations
LOGO_URL = "static/Blaize.png"
CLAUDE_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# Helper functions
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
        return base64.b64encode(data).decode()

# Database functions
def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

def keyword_search(query, top_k=5):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                start_time = time.time()
                cur.execute("""
                    SELECT "productId", product_description, category_name, stars, price, boughtinlastmonth,
                           imgURL, producturl
                    FROM bedrock_integration.product_catalog
                    WHERE to_tsvector('english', product_description || ' ' || category_name) @@ plainto_tsquery('english', %s)
                    ORDER BY ts_rank(to_tsvector('english', product_description || ' ' || category_name), plainto_tsquery('english', %s)) DESC
                    LIMIT %s
                """, (query, query, top_k))
                results = cur.fetchall()
                end_time = time.time()
                query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            except psycopg.Error as e:
                st.error(f"Error: {e}. Please check your database configuration.")
                st.stop()

    return pd.DataFrame(results, columns=['productId', 'product_description', 'category_name', 'stars', 'price', 'boughtinlastmonth', 'imgURL', 'producturl']), query_time

def similarity_search(query_embedding, top_k=5):
    query_embedding_list = query_embedding.tolist()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                start_time = time.time()
                cur.execute("""
                    SELECT "productId", product_description, category_name, stars, price, boughtinlastmonth,
                           imgURL, producturl,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM bedrock_integration.product_catalog
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding_list, query_embedding_list, top_k))
                results = cur.fetchall()
                end_time = time.time()
                query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            except psycopg.errors.InvalidTextRepresentation as e:
                st.error(f"Error: {e}. The embedding data type might not match. Please check your database schema.")
                st.stop()

    return pd.DataFrame(results, columns=['productId', 'product_description', 'category_name', 'stars', 'price', 'boughtinlastmonth', 'imgURL', 'producturl', 'similarity']), query_time

# Bedrock functions
def generate_embedding(text):
    body = json.dumps({"inputText": text})
    modelId = 'amazon.titan-embed-text-v2:0'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    embedding = response_body.get('embedding')
    return np.array(embedding, dtype=np.float32)

def get_claude_response(prompt, max_tokens=4096):
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        response = bedrock.invoke_model(
            body=body,
            modelId=CLAUDE_MODEL_ID,
            accept="application/json",
            contentType="application/json"
        )

        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
    except ClientError as e:
        st.error(f"An error occurred: {e}")
        return None

def get_personalized_recommendations(user_preferences, top_k=3):
    # Generate embedding for user preferences
    preference_embedding = generate_embedding(user_preferences)
    
    # Perform similarity search in product catalog
    results, query_time = similarity_search(preference_embedding, top_k)
    
    # Prepare the prompt for Claude
    recommendations_prompt = f"""
    Based on the user's preferences: "{user_preferences}"
    And considering these top products from our catalog:
    {results.to_dict('records')}

    Provide {top_k} personalized product recommendations. For each recommendation:
    1. Explain why it's a good fit for the user
    2. Highlight key features or benefits
    3. Suggest how it compares to similar products

    Format your response in markdown for easy reading.
    """
    
    # Get recommendations from Claude
    claude_recommendations = get_claude_response(recommendations_prompt)
    
    return claude_recommendations, results, query_time

def display_products(results, query_time):
    st.subheader(f"Search Results (Query Time: {query_time:.2f} ms)")
    for _, product in results.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(product['imgURL'], width=100)
        with col2:
            st.write(f"**[{product['product_description']}]({product['producturl']})**")
            st.write(f"Category: {product['category_name']}")
            st.write(f"Price: ${product['price']:.2f}")
            st.write(f"Rating: {product['stars']:.1f}")
            if 'similarity' in product:
                st.write(f"Similarity: {product['similarity']:.4f}")
        st.write("---")

def show_product_recommendations():
    st.subheader("Product Search Comparison")
    
    # Example queries dropdown
    example_queries = [
        "Select an example query",
        "affordable portable computers",
        "I need something to keep my drinks cold on a picnic",
        "light jacket for spring evenings",
        "duffel bags for the gym",
        "eco-friendly cleaning products",
        "gift for a tech-savvy teenager",
        "wirless blutooth headfones",
        "outdoor cooking equipment",
        "vacation-ready camera",
        "stylish but professional attire for a creative office",
        "cozy home decor"
    ]
    selected_query = st.selectbox("Choose an example query or enter your own:", example_queries)
    
    search_query = st.text_input("Enter a product description:", value=selected_query if selected_query != example_queries[0] else "")
    if st.button("Search"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Keyword-based Search")
            with st.spinner("Performing keyword search..."):
                keyword_results, keyword_query_time = keyword_search(search_query)
            display_products(keyword_results, keyword_query_time)
        
        with col2:
            st.subheader("Semantic Search")
            with st.spinner("Generating embedding..."):
                query_embedding = generate_embedding(search_query)
            with st.spinner("Performing semantic search..."):
                semantic_results, semantic_query_time = similarity_search(query_embedding)
            display_products(semantic_results, semantic_query_time)
            
        st.subheader("Search Comparison Explanation")
        st.write("""
        Semantic search often outperforms keyword-based search because it understands context and intent:
        - It can handle synonyms and related concepts
        - It works well with natural language queries
        - It can infer meaning from complex or abstract queries
        - It's more resilient to misspellings and variations
            
        In this example, notice how semantic search might return more relevant results,
        especially for queries that don't exactly match product descriptions.
        """)
    else:
        st.warning("Please enter a search query.")
    

    # Personalized AI Recommendations
    st.subheader("Personalized AI Recommendations")
    user_preferences = st.text_area("Tell us about your preferences and what you're looking for:")
    if st.button("Get Personalized Recommendations"):
        with st.spinner("Generating personalized recommendations..."):
            recommendations, top_products, query_time = get_personalized_recommendations(user_preferences)
        if recommendations:
            st.markdown(recommendations)
            st.subheader(f"Top Matching Products (Query Time: {query_time:.2f} ms)")
            display_products(top_products, query_time)
        else:
            st.error("Failed to generate personalized recommendations. Please try again later.")

def main():
    st.set_page_config(page_title="Product Recommendations - Blaize Bazaar", page_icon="🛍️", layout="wide")
    st.subheader('Product Recommendations - Blaize Bazaar', divider='orange')
    st.sidebar.image(LOGO_URL, use_column_width=True)
    st.sidebar.title('**About**')
    st.sidebar.info("This page provides product recommendations using AI-powered similarity search and analysis, comparing traditional keyword-based search with semantic search.")

    show_product_recommendations()

if __name__ == "__main__":
    main()