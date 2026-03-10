import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="E-DUST Engagement Matrix", layout="wide")

# Constants for Math (Bluesky)
W_CLICK, W_LIKE, W_COMMENT, W_SHARE = 1, 2, 3, 4
# Constants for Math (Substack - Reads and Clicks)
W_READ, W_SS_CLICK = 1, 1 

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
        font-size: 0.85em;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Loading
@st.cache_data
def load_data():
    # Load Substack (New Format: Date, Reads, Followers, Clicks)
    df_ss = pd.read_csv('engagement_matrix_sample - Substack (sample).csv')
    df_ss['Date'] = pd.to_datetime(df_ss['Date'])
    # Calculate Substack Score: Reads + Clicks
    df_ss['Score'] = (df_ss['Reads_per_Post'] * W_READ) + (df_ss['Link_Clicks_in_Post'] * W_SS_CLICK)
    
    # Load Bluesky (Existing Format)
    df_bs = pd.read_csv('engagement_matrix_sample - Bluesky (sample).csv')
    df_bs['Date'] = pd.to_datetime(df_bs['Date'])
    # Calculate Bluesky Score: L*2 + C*1 + Cm*3 + S*4
    df_bs['Score'] = (df_bs['Likes'] * W_LIKE) + (df_bs['Clicks'] * W_CLICK) + \
                     (df_bs['Comments'] * W_COMMENT) + (df_bs['Shares'] * W_SHARE)
    
    return df_bs, df_ss

try:
    df_bs, df_ss = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 4. Sidebar
st.sidebar.title("📊 Settings")
st.sidebar.markdown("### 🔑 Engagement Weights")
st.sidebar.markdown(f"""
<div class="weight-legend">
    <strong>Bluesky:</strong><br>
    Click: {W_CLICK} | Like: {W_LIKE}<br>
    Comment: {W_COMMENT} | Share: {W_SHARE}<br><br>
    <strong>Substack:</strong><br>
    Read: {W_READ} | Link Click: {W_SS_CLICK}
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
# Determine global date range across both files
min_date = min(df_bs['Date'].min(), df_ss['Date'].min())
max_date = max(df_bs['Date'].max(), df_ss['Date'].max())
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# Filter dataframes
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_bs_f = df_bs[(df_bs['Date'] >= start) & (df_bs['Date'] <= end)]
    df_ss_f = df_ss[(df_ss['Date'] >= start) & (df_ss['Date'] <= end)]
else:
    df_bs_f, df_ss_f = df_bs, df_ss

# 5. Header & Links
st.title("🛰️ E-DUST engagement matrix")
st.markdown(f"[🦋 Bluesky Profile](https://bsky.app/profile/cznews.bsky.social)  •  [✉️ Substack Newsletter](https://criticalzonenews.substack.com/)")
st.markdown("---")

# 6. Main Dashboard Layout
col1, col2 = st.columns(2)

with col1:
    st.header("🦋 Bluesky Insights")
    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Score", f"{df_bs_f['Score'].sum():,}")
    k2.metric("Avg Score", f"{df_bs_f['Score'].mean():.1f}")
    k3.metric("Total Shares", f"{df_bs_f['Shares'].sum():,}")

    # Trend with Math Tooltip
    df_bs_trend = df_bs_f.groupby('Date')[['Score', 'Likes', 'Clicks', 'Comments', 'Shares']].sum().reset_index()
    df_bs_trend['Math'] = df_bs_trend.apply(lambda r: f"({r['Likes']}L×{W_LIKE}) + ({r['Clicks']}C×{W_CLICK}) + ({r['Comments']}Cm×{W_COMMENT}) + ({r['Shares']}S×{W_SHARE})", axis=1)
    
    fig_bs_line = px.line(df_bs_trend, x='Date', y='Score', title="Engagement Over Time",
                         line_shape='spline', color_discrete_sequence=['#0085FF'],
                         hover_data={'Math': True, 'Score': True})
    st.plotly_chart(fig_bs_line, use_container_width=True)
    
    # Post Type Analysis
    df_bs_post = df_bs_f.groupby('Post_Type')['Score'].mean().reset_index().sort_values('Score')
    fig_bs_bar = px.bar(df_bs_post, x='Score', y='Post_Type', orientation='h',
                       title="Top Post Types (Avg Score)", color='Score', color_continuous_scale='Blues')
    st.plotly_chart(fig_bs_bar, use_container_width=True)

with col2:
    st.header("✉️ Substack Insights")
    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Current Followers", f"{df_ss_f['Followers_Over_Time'].iloc[-1] if not df_ss_f.empty else 0:,}")
    k2.metric("Total Reads", f"{df_ss_f['Reads_per_Post'].sum():,}")
    k3.metric("Total Clicks", f"{df_ss_f['Link_Clicks_in_Post'].sum():,}")

    # Growth Trend (Followers)
    fig_ss_growth = px.area(df_ss_f, x='Date', y='Followers_Over_Time', title="Follower Growth",
                           color_discrete_sequence=['#FF6719'])
    st.plotly_chart(fig_ss_growth, use_container_width=True)
    
    # Reach vs Action (Reads vs Clicks)
    df_ss_f['Math'] = df_ss_f.apply(lambda r: f"({r['Reads_per_Post']}R×{W_READ}) + ({r['Link_Clicks_in_Post']}C×{W_SS_CLICK})", axis=1)
    fig_ss_mix = go.Figure()
    fig_ss_mix.add_trace(go.Bar(x=df_ss_f['Date'], y=df_ss_f['Reads_per_Post'], name='Reads', marker_color='#FF6719', 
                               customdata=df_ss_f['Math'], hovertemplate="Reads: %{y}<br>Math: %{customdata}"))
    fig_ss_mix.add_trace(go.Bar(x=df_ss_f['Date'], y=df_ss_f['Link_Clicks_in_Post'], name='Clicks', marker_color='#FFA07A',
                               customdata=df_ss_f['Math'], hovertemplate="Clicks: %{y}<br>Math: %{customdata}"))
    fig_ss_mix.update_layout(barmode='group', title="Reads vs. Link Clicks", height=400)
    st.plotly_chart(fig_ss_mix, use_container_width=True)

# 7. Comparison Table
st.markdown("---")
st.subheader("📋 Recent Activity Raw Data")
tab1, tab2 = st.tabs(["Bluesky Posts", "Substack Daily Log"])
with tab1:
    st.dataframe(df_bs_f.sort_values('Date', ascending=False), use_container_width=True)
with tab2:
    st.dataframe(df_ss_f.sort_values('Date', ascending=False), use_container_width=True)
