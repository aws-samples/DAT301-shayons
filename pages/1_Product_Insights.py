import streamlit as st
import psycopg
import pandas as pd
import plotly.express as px
import numpy as np
import os
from dotenv import load_dotenv
import boto3
import json
import base64
import warnings
from botocore.exceptions import ClientError

# Suppress the specific SQLAlchemy warning
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable.*")

# Load environment variables
load_dotenv()

# Initialize Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime', region_name=os.environ.get('AWS_REGION')
)

# Constants and configurations
LOGO_URL = "static/Blaize.png"
CLAUDE_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"  # Update this to the Bedrock model ID for Claude

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

# Functions for graphs
def get_product_data():
    """
    SELECT "productId", product_description, category_name, stars, price, boughtinlastmonth, embedding
    FROM bedrock_integration.product_catalog
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_product_data.__doc__, conn)

def similarity_search(query_embedding, top_k=5):
    """
    SELECT "productId", product_description, category_name, stars, price, boughtinlastmonth,
           imgURL, producturl,
           1 - (embedding <=> %s::vector) AS similarity
    FROM bedrock_integration.product_catalog
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """
    query_embedding_list = query_embedding.tolist()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(similarity_search.__doc__, (query_embedding_list, query_embedding_list, top_k))
                results = cur.fetchall()
            except psycopg.errors.InvalidTextRepresentation as e:
                st.error(f"Error: {e}. The embedding data type might not match. Please check your database schema.")
                st.stop()

    return pd.DataFrame(results, columns=['productId', 'product_description', 'category_name', 'stars', 'price', 'boughtinlastmonth', 'imgURL', 'producturl', 'similarity'])

def get_top_trending_categories(top_n=10):
    """
    SELECT category_name, SUM(boughtinlastmonth) as total_bought
    FROM bedrock_integration.product_catalog
    GROUP BY category_name
    ORDER BY total_bought DESC
    LIMIT %s
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_top_trending_categories.__doc__, conn, params=(top_n,))
        
def get_top_grossing_products(top_n=10):
    """
    SELECT product_description, category_name, price * boughtinlastmonth as total_revenue, 
           boughtinlastmonth, stars, price
    FROM bedrock_integration.product_catalog
    ORDER BY total_revenue DESC
    LIMIT %s
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_top_grossing_products.__doc__, conn, params=(top_n,))
        
def get_top_selling_products(top_n=10):
    """
    SELECT product_description, category_name, boughtinlastmonth, stars, price
    FROM bedrock_integration.product_catalog
    ORDER BY boughtinlastmonth DESC
    LIMIT %s
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_top_selling_products.__doc__, conn, params=(top_n,))

def get_top_rated_categories(top_n=10):
    """
    SELECT category_name, AVG(stars) as avg_rating
    FROM bedrock_integration.product_catalog
    GROUP BY category_name
    ORDER BY avg_rating DESC
    LIMIT %s
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_top_rated_categories.__doc__, conn, params=(top_n,))

def get_best_selling_by_category(top_n=10):
    """
    SELECT DISTINCT ON (category_name) 
           category_name, product_description, boughtinlastmonth
    FROM bedrock_integration.product_catalog
    ORDER BY category_name, boughtinlastmonth DESC
    LIMIT %s
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_best_selling_by_category.__doc__, conn, params=(top_n,))

def get_spending_habits():
    """
    WITH price_ranges AS (
        SELECT 
            CASE 
                WHEN price < 20 THEN 'Under $20'
                WHEN price >= 20 AND price < 50 THEN '$20 - $49.99'
                WHEN price >= 50 AND price < 100 THEN '$50 - $99.99'
                WHEN price >= 100 AND price < 200 THEN '$100 - $199.99'
                ELSE '$200 and above'
            END AS price_range,
            boughtinlastmonth
        FROM bedrock_integration.product_catalog
    )
    SELECT 
        price_range,
        COUNT(*) as product_count,
        SUM(boughtinlastmonth) as total_sold
    FROM price_ranges
    GROUP BY price_range
    ORDER BY 
        CASE price_range
            WHEN 'Under $20' THEN 1
            WHEN '$20 - $49.99' THEN 2
            WHEN '$50 - $99.99' THEN 3
            WHEN '$100 - $199.99' THEN 4
            ELSE 5
        END
    """
    with get_db_connection() as conn:
        return pd.read_sql(get_spending_habits.__doc__, conn)

# Bedrock functions
def generate_embedding(text):
    body = json.dumps({"inputText": text})
    modelId = 'amazon.titan-embed-text-v1'
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

# UI functions
def show_product_insights():
    st.subheader("Product Insights Dashboard")

    # Create three columns for the first row of charts
    col1, col2, col3 = st.columns(3)

    with col1:
        # Top 10 Trending Categories
        trending_categories = get_top_trending_categories(10)
        fig_trending = px.bar(trending_categories.sort_values('total_bought', ascending=True), 
                              x='total_bought', y='category_name',
                              labels={'total_bought': 'Units Sold Last Month', 'category_name': 'Category'},
                              title="Top 10 Trending Categories",
                              orientation='h',
                              color='total_bought',
                              color_continuous_scale=px.colors.sequential.Viridis)
        fig_trending.update_layout(showlegend=True, height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_trending, use_container_width=True)

    with col2:
        # Top 10 Highest Grossing Products
        top_grossing = get_top_grossing_products(10)
        # Create a shortened product name
        top_grossing['short_name'] = top_grossing['product_description'].str[:20] + '...'
        fig_grossing = px.bar(top_grossing, x='total_revenue', y='short_name',
                          color='category_name', 
                          hover_data=['product_description', 'boughtinlastmonth', 'price'],
                          labels={'total_revenue': 'Total Revenue', 
                                  'short_name': 'Product',
                                  'product_description': 'Full Product Name'},
                          title="Top 10 Highest Grossing Products",
                          color_discrete_sequence=px.colors.qualitative.Vivid)
        fig_grossing.update_layout(showlegend=True, height=400, legend_title_text='Category', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_grossing, use_container_width=True)

    with col3:
        # Top 10 Best Selling Products
        top_selling = get_top_selling_products(10)
        top_selling['short_name'] = top_selling['product_description'].str[:20] + '...'
    
        fig_top_selling = px.bar(top_selling, x='boughtinlastmonth', y='short_name',
                             color='category_name', 
                             hover_data=['product_description', 'stars', 'price'],
                             labels={'boughtinlastmonth': 'Units Sold Last Month', 
                                     'short_name': 'Product',
                                     'product_description': 'Full Product Name'},
                             title="Top 10 Best Selling Products",
                             orientation='h',
                             height=500,
                             color_discrete_sequence=px.colors.qualitative.Bold)
        fig_top_selling.update_layout(showlegend=True, legend_title_text='Category', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top_selling, use_container_width=True)

    # Create three columns for the second row of charts
    col4, col5, col6 = st.columns(3)
    with col4:
        # Top 10 Categories
        top_categories = get_top_rated_categories(10)
        fig_categories = px.bar(top_categories.sort_values('avg_rating', ascending=True), 
                                x='avg_rating', y='category_name',
                                labels={'avg_rating': 'Average Rating', 'category_name': 'Category'},
                                title="Top 10 Categories by Average Rating",
                                orientation='h',
                                color='avg_rating',
                                color_continuous_scale=px.colors.sequential.Magma)
        fig_categories.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_categories, use_container_width=True)

    with col5:
        # Best Selling Products in each category
        best_selling_by_category = get_best_selling_by_category()
        fig_best_selling = px.bar(best_selling_by_category.sort_values('boughtinlastmonth', ascending=True), 
                                  x='boughtinlastmonth', y='category_name',
                                  labels={'boughtinlastmonth': 'Units Sold Last Month', 'category_name': 'Category'},
                                  title="Best Selling Product in Each Category",
                                  orientation='h',
                                  color='product_description',
                                  hover_data=['product_description'],
                                  color_continuous_scale=px.colors.sequential.Inferno)
        fig_best_selling.update_layout(showlegend=False, height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_best_selling, use_container_width=True)

    with col6:
        # General Spending Habits of Online Shoppers
        spending_habits = get_spending_habits()
        fig_spending = px.pie(spending_habits.sort_values('total_sold', ascending=False), 
                              values='total_sold', names='price_range',
                              title="General Spending Habits of Online Shoppers",
                              hover_data=['product_count'],
                              color_discrete_sequence=px.colors.qualitative.G10)
        fig_spending.update_traces(textposition='inside', textinfo='percent+label')
        fig_spending.update_layout(showlegend=True, legend_title_text='Price Range', height=400)
        st.plotly_chart(fig_spending, use_container_width=True)
    
    # Show SQL queries in expanders
    with st.expander("View SQL Queries"):
        st.caption("These are the SQL Queries used to generate the Product Insights Dashboard.")
        st.code(get_top_trending_categories.__doc__, language="sql")
        st.code(get_top_grossing_products.__doc__, language="sql")
        st.code(get_top_selling_products.__doc__, language="sql")
        st.code(get_top_rated_categories.__doc__, language="sql")
        st.code(get_best_selling_by_category.__doc__, language="sql")
        st.code(get_spending_habits.__doc__, language="sql")

    # AI-Powered Market Insights
    st.subheader("AI-Powered Market Insights")
    
    # Prepare and show the AI prompt
    insights_prompt = f"""
    Based on the following product data:
    Top Trending Categories: {trending_categories.to_dict()}
    Top Grossing Products: {top_grossing.to_dict()}
    Top Selling Products: {top_selling.to_dict()}
    Top Rated Categories: {top_categories.to_dict()}
    Best Selling by Category: {best_selling_by_category.to_dict()}
    Spending Habits: {spending_habits.to_dict()}

    First, provide a summary of the market trends, customer preferences and potential areas for improvement or expansion. 
    Second , provide a detailed analysis of the market trends, customer preferences, and potential areas for improvement or expansion.
    Focus on actionable insights that could help drive business decisions. Format your response in markdown for easy reading.
    """
    
    with st.expander("View AI Prompt"):
        st.code(insights_prompt, language="markdown")
    
    with st.spinner("Generating AI insights..."):
        claude_insights = get_claude_response(insights_prompt)
    if claude_insights:
        st.write(claude_insights)
    else:
        st.error("Failed to generate AI insights. Please try again later.")

def main():
    st.set_page_config(page_title="Product Insights", page_icon="📊", layout="wide")
    st.subheader('Product Insights - Blaize Bazaar', divider='orange')
    st.sidebar.image(LOGO_URL, use_column_width=True)
    st.sidebar.title('**About**')
    st.sidebar.info("This page provides comprehensive product insights using AI-powered analysis.")

    show_product_insights()

if __name__ == "__main__":
    main()