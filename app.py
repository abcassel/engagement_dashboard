import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Multi-Platform Engagement Dashboard", layout="wide", page_icon="📊")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #eee; }
    h1, h2, h3 { color: #0f172a; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_index=True)

# Data Loading and Merging
@st.cache_data
def load_combined_data():
    # 1. Load Substack (Has headers)
    df_ss = pd.read_csv('engagement_matrix_sample - Substack (sample).csv')
    
    # 2. Load Bluesky (No headers in file, we must assign them)
    cols = ['Date', 'Platform', 'Post_Type', 'Likes', 'Clicks', 'Comments', 'Shares', 'Weighted_Engagement_Score']
    df_bs = pd.read_csv('engagement_matrix_sample - Bluesky (sample).csv', names=cols, header=None)
    
    # Combine data
    df = pd.concat([df_ss, df_bs], ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

try:
    df = load_combined_data()
except Exception as e:
    st.error(f"Error loading files: {e}")
    st.info("Ensure both 'engagement_matrix_sample - Bluesky (sample).csv' and 'engagement_matrix_sample - Substack (sample).csv' are in your GitHub repository.")
    st.stop()

# Sidebar
st.sidebar.header("🗓️ Filter by Date")
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()
date_range = st.sidebar.date_input("Select Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Apply Filter
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    filtered_df = df.loc[mask]
else:
    filtered_df = df

# Main Title
st.title("🚀 Social Engagement Matrix")
st.markdown("Comparing performance between **Bluesky** and **Substack** content strategies.")

# --- LAYOUT: Two Columns ---
col_left, col_right = st.columns(2)

# --- BLUESKY (LEFT) ---
with col_left:
    st.subheader("🦋 Bluesky Performance")
    df_bs_filtered = filtered_df[filtered_df['Platform'] == 'Bluesky']
    
    k1, k2 = st.columns(2)
    k1.metric("Avg Engagement", f"{df_bs_filtered['Weighted_Engagement_Score'].mean():.1f}")
    k2.metric("Total Shares", f"{df_bs_filtered['Shares'].sum():,}")
    
    # Trend Chart
    fig_bs_trend = px.area(df_bs_filtered.groupby('Date')['Weighted_Engagement_Score'].sum().reset_index(), 
                          x='Date', y='Weighted_Engagement_Score', 
                          title="Daily Engagement Trend", color_discrete_sequence=['#0085FF'])
    fig_bs_trend.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_bs_trend, use_container_width=True)
    
    # Content Mix
    fig_bs_bar = px.bar(df_bs_filtered.groupby('Post_Type')['Weighted_Engagement_Score'].mean().reset_index().sort_values('Weighted_Engagement_Score'), 
                       x='Weighted_Engagement_Score', y='Post_Type', orientation='h', 
                       title="Top Performing Content Types", color='Weighted_Engagement_Score', color_continuous_scale='Blues')
    st.plotly_chart(fig_bs_bar, use_container_width=True)

# --- SUBSTACK (RIGHT) ---
with col_right:
    st.subheader("✉️ Substack Performance")
    df_ss_filtered = filtered_df[filtered_df['Platform'] == 'Substack']
    
    k1, k2 = st.columns(2)
    k1.metric("Avg Engagement", f"{df_ss_filtered['Weighted_Engagement_Score'].mean():.1f}")
    k2.metric("Total Clicks", f"{df_ss_filtered['Clicks'].sum():,}")
    
    # Trend Chart
    fig_ss_trend = px.area(df_ss_filtered.groupby('Date')['Weighted_Engagement_Score'].sum().reset_index(), 
                          x='Date', y='Weighted_Engagement_Score', 
                          title="Daily Engagement Trend", color_discrete_sequence=['#FF6719'])
    fig_ss_trend.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_ss_trend, use_container_width=True)
    
    # Content Mix
    fig_ss_bar = px.bar(df_ss_filtered.groupby('Post_Type')['Weighted_Engagement_Score'].mean().reset_index().sort_values('Weighted_Engagement_Score'), 
                       x='Weighted_Engagement_Score', y='Post_Type', orientation='h', 
                       title="Top Performing Content Types", color='Weighted_Engagement_Score', color_continuous_scale='Oranges')
    st.plotly_chart(fig_ss_bar, use_container_width=True)

# --- BOTTOM COMPARISON ---
st.markdown("---")
st.header("📊 Multi-Channel Deep Dive")
comp_metric = st.selectbox("Select Metric to Compare", ['Likes', 'Clicks', 'Comments', 'Shares', 'Weighted_Engagement_Score'])

fig_compare = px.box(filtered_df, x='Platform', y=comp_metric, color='Platform',
                    color_discrete_map={'Bluesky': '#0085FF', 'Substack': '#FF6719'},
                    points="all", title=f"Distribution of {comp_metric} across Platforms")
st.plotly_chart(fig_compare, use_container_width=True)
