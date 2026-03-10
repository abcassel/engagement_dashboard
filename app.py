import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="E-DUST Engagement Matrix", layout="wide")

# Constants for Math
W_CLICK, W_LIKE, W_COMMENT, W_SHARE = 1, 2, 3, 4

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

# 3. Data Loading
@st.cache_data
def load_data():
    # Load Substack
    df_ss = pd.read_csv('engagement_matrix_sample - Substack (sample).csv')
    
    # Load Bluesky (Defining headers manually as the file lacks them)
    bs_cols = ['Date', 'Platform', 'Post_Type', 'Likes', 'Clicks', 'Comments', 'Shares', 'Weighted_Engagement_Score']
    df_bs = pd.read_csv('engagement_matrix_sample - Bluesky (sample).csv', names=bs_cols, header=None)
    
    df = pd.concat([df_ss, df_bs], ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Recalculate score based on user's specific weights to ensure math matches display
    df['Calculated_Score'] = (df['Clicks'] * W_CLICK) + (df['Likes'] * W_LIKE) + \
                             (df['Comments'] * W_COMMENT) + (df['Shares'] * W_SHARE)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Helper for tooltip math
def generate_math_string(row, is_mean=False):
    prefix = "Avg: " if is_mean else ""
    return (f"{prefix}({row['Likes']:.1f}L × {W_LIKE}) + ({row['Clicks']:.1f}C × {W_CLICK}) + "
            f"({row['Comments']:.1f}Cm × {W_COMMENT}) + ({row['Shares']:.1f}S × {W_SHARE})")

# 4. Sidebar
st.sidebar.title("📊 Settings")
st.sidebar.markdown("### 🔑 Engagement Weights")
st.sidebar.markdown(f"""
<div class="weight-legend">
    <strong>Link Click:</strong> {W_CLICK}<br>
    <strong>Like:</strong> {W_LIKE}<br>
    <strong>Comment:</strong> {W_COMMENT}<br>
    <strong>Share:</strong> {W_SHARE}
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

# 5. Header & Links
st.title("🛰️ E-DUST engagement matrix")
col_links, col_kpis = st.columns([1, 3])
with col_links:
    st.markdown("### 🔗 Live Channels")
    st.markdown("[🦋 Bluesky](https://bsky.app/profile/cznews.bsky.social) | [✉️ Substack](https://criticalzonenews.substack.com/)")

with col_kpis:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg Score", f"{filtered_df['Calculated_Score'].mean():.1f}")
    m2.metric("Total Clicks", f"{filtered_df['Clicks'].sum():,}")
    m3.metric("Total Likes", f"{filtered_df['Likes'].sum():,}")
    m4.metric("Total Shares", f"{filtered_df['Shares'].sum():,}")

# 6. Main Charts
st.markdown("---")
col1, col2 = st.columns(2)

def create_platform_charts(data, color_scale, line_color, p_name):
    # Trend Chart
    trend = data.groupby('Date')[['Calculated_Score', 'Likes', 'Clicks', 'Comments', 'Shares']].sum().reset_index()
    trend['Math'] = trend.apply(generate_math_string, axis=1)
    
    fig_line = px.line(trend, x='Date', y='Calculated_Score', title=f"{p_name} Daily Engagement",
                       color_discrete_sequence=[line_color], hover_data={'Math': True, 'Calculated_Score': True})
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Bar Chart
    bar_data = data.groupby('Post_Type')[['Calculated_Score', 'Likes', 'Clicks', 'Comments', 'Shares']].mean().reset_index()
    bar_data['Math'] = bar_data.apply(lambda x: generate_math_string(x, is_mean=True), axis=1)
    
    fig_bar = px.bar(bar_data, x='Calculated_Score', y='Post_Type', orientation='h',
                     title=f"{p_name} Top Content Types (Avg)",
                     color='Calculated_Score', color_continuous_scale=color_scale,
                     hover_data={'Math': True, 'Calculated_Score': ':.2f'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col1:
    st.subheader("🦋 Bluesky Insights")
    bs_data = filtered_df[filtered_df['Platform'] == 'Bluesky']
    if not bs_data.empty:
        create_platform_charts(bs_data, 'Blues', '#0085FF', "Bluesky")

with col2:
    st.subheader("✉️ Substack Insights")
    ss_data = filtered_df[filtered_df['Platform'] == 'Substack']
    if not ss_data.empty:
        create_platform_charts(ss_data, 'Oranges', '#FF6719', "Substack")

# 7. Heatmap
st.markdown("---")
st.subheader("🎯 Strategy Heatmap (Avg Score)")
heat_data = filtered_df.groupby(['Post_Type', 'Platform'])[['Calculated_Score', 'Likes', 'Clicks', 'Comments', 'Shares']].mean().reset_index()
heat_data['Math'] = heat_data.apply(lambda x: generate_math_string(x, is_mean=True), axis=1)

fig_heat = px.density_heatmap(heat_data, x='Platform', y='Post_Type', z='Calculated_Score',
                              text_auto=".1f", color_continuous_scale='Viridis',
                              hover_data={'Math': True, 'Calculated_Score': ':.2f'})
st.plotly_chart(fig_heat, use_container_width=True)
