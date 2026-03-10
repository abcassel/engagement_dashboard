import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="E-DUST Engagement Matrix", layout="wide")

# 2. Custom Styling
st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #f0f2f6;
    }
    .weight-legend {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #1E3A8A;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Robust Data Loading
@st.cache_data
def load_data():
    # Load Substack
    df_ss = pd.read_csv('engagement_matrix_sample - Substack (sample).csv')
    
    # Load Bluesky (Assumes NO headers)
    bs_cols = ['Date', 'Platform', 'Post_Type', 'Likes', 'Clicks', 'Comments', 'Shares', 'Weighted_Engagement_Score']
    df_bs = pd.read_csv('engagement_matrix_sample - Bluesky (sample).csv', names=bs_cols, header=None)
    
    # Merge and clean
    df = pd.concat([df_ss, df_bs], ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 4. Sidebar Filters & Legend
st.sidebar.title("📊 Settings")

# Engagement Weights Legend
st.sidebar.markdown("### 🔑 Engagement Weights")
st.sidebar.markdown("""
<div class="weight-legend">
    <strong>Link Click:</strong> 1<br>
    <strong>Like:</strong> 2<br>
    <strong>Comment:</strong> 3<br>
    <strong>Share:</strong> 4
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

platforms = st.sidebar.multiselect("Select Platforms", ["Bluesky", "Substack"], default=["Bluesky", "Substack"])
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])

# Filter data
mask = (df['Platform'].isin(platforms))
if len(date_range) == 2:
    mask = mask & (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
filtered_df = df.loc[mask]

# 5. Dashboard Header
st.title("🛰️ E-DUST engagement matrix")
st.markdown("---")

# 6. Platform Links & Top Level KPIs
col_links, col_kpis = st.columns([1, 3])

with col_links:
    st.markdown("### 🔗 Live Channels")
    st.markdown("[🦋 Bluesky Profile](https://bsky.app/profile/cznews.bsky.social)")
    st.markdown("[✉️ Substack Newsletter](https://criticalzonenews.substack.com/)")

with col_kpis:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg. Engagement", f"{filtered_df['Weighted_Engagement_Score'].mean():.1f}")
    m2.metric("Total Clicks", f"{filtered_df['Clicks'].sum():,}")
    m3.metric("Total Likes", f"{filtered_df['Likes'].sum():,}")
    m4.metric("Total Shares", f"{filtered_df['Shares'].sum():,}")

# 7. Main Visuals
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("🦋 Bluesky Insights")
    bs_df = filtered_df[filtered_df['Platform'] == 'Bluesky']
    if not bs_df.empty:
        fig_bs_line = px.line(bs_df.groupby('Date')['Weighted_Engagement_Score'].sum().reset_index(), 
                             x='Date', y='Weighted_Engagement_Score', 
                             title="Engagement Trend", color_discrete_sequence=['#0085FF'])
        st.plotly_chart(fig_bs_line, use_container_width=True)
        
        fig_bs_bar = px.bar(bs_df.groupby('Post_Type')['Weighted_Engagement_Score'].mean().reset_index(), 
                           x='Weighted_Engagement_Score', y='Post_Type', orientation='h',
                           color='Weighted_Engagement_Score', color_continuous_scale='Blues')
        st.plotly_chart(fig_bs_bar, use_container_width=True)

with col2:
    st.subheader("✉️ Substack Insights")
    ss_df = filtered_df[filtered_df['Platform'] == 'Substack']
    if not ss_df.empty:
        fig_ss_line = px.line(ss_df.groupby('Date')['Weighted_Engagement_Score'].sum().reset_index(), 
                             x='Date', y='Weighted_Engagement_Score', 
                             title="Engagement Trend", color_discrete_sequence=['#FF6719'])
        st.plotly_chart(fig_ss_line, use_container_width=True)
        
        fig_ss_bar = px.bar(ss_df.groupby('Post_Type')['Weighted_Engagement_Score'].mean().reset_index(), 
                           x='Weighted_Engagement_Score', y='Post_Type', orientation='h',
                           color='Weighted_Engagement_Score', color_continuous_scale='Oranges')
        st.plotly_chart(fig_ss_bar, use_container_width=True)

# 8. Comparison Heatmap
st.markdown("---")
st.subheader("🎯 Strategy Matrix (Post Type vs Platform)")
heat_df = filtered_df.groupby(['Post_Type', 'Platform'])['Weighted_Engagement_Score'].mean().unstack()
fig_heat = px.imshow(heat_df, text_auto=".1f", color_continuous_scale='Viridis', aspect="auto")
st.plotly_chart(fig_heat, use_container_width=True)
