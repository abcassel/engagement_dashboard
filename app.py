import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="E-DUST Engagement Matrix", layout="wide")

# Constants & Colors
METRIC_COLORS = {
    'Likes': '#3B82F6',    # Blue
    'Clicks': '#10B981',   # Green
    'Comments': '#F59E0B', # Amber
    'Shares': '#8B5CF6',   # Purple
    'Reads': '#FF6719'     # Substack Orange
}
WEIGHTS = {'Likes': 2, 'Clicks': 1, 'Comments': 3, 'Shares': 4, 'Reads': 1}

# 2. Custom Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #f0f2f6; }
    .weight-legend { background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 5px solid #1E3A8A; font-size: 0.85em; }
    h3 { font-size: 1.1rem !important; margin-bottom: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Loading
@st.cache_data
def load_data():
    # Load Bluesky
    df_bs = pd.read_csv('engagement_matrix_sample - Bluesky (sample).csv')
    df_bs['Date'] = pd.to_datetime(df_bs['Date'])
    
    # Load Substack
    df_ss = pd.read_csv('engagement_matrix_sample - Substack (sample).csv')
    df_ss['Date'] = pd.to_datetime(df_ss['Date'])
    
    return df_bs, df_ss

try:
    df_bs, df_ss = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 4. Sidebar: Control Panel
st.sidebar.title("📊 Control Panel")
available_metrics = ['Likes', 'Clicks', 'Shares', 'Comments']
selected_metrics = st.sidebar.multiselect("Active Interaction Metrics", options=available_metrics, default=available_metrics)

st.sidebar.markdown("### 🔑 Calculation Logic")
legend_html = "<div class='weight-legend'>"
for m in selected_metrics:
    legend_html += f"<strong>{m}:</strong> {WEIGHTS[m]} Engagement Points<br>"
legend_html += f"<strong>Reads (SS):</strong> {WEIGHTS['Reads']} Engagement Points</div>"
st.sidebar.markdown(legend_html, unsafe_allow_html=True)

st.sidebar.markdown("---")
min_date = min(df_bs['Date'].min(), df_ss['Date'].min())
max_date = max(df_bs['Date'].max(), df_ss['Date'].max())
date_range = st.sidebar.date_input("Timeframe", [min_date, max_date])

# Filter and Calculate
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_bs_f = df_bs[(df_bs['Date'] >= start) & (df_bs['Date'] <= end)].copy()
    df_ss_f = df_ss[(df_ss['Date'] >= start) & (df_ss['Date'] <= end)].copy()
else:
    df_bs_f, df_ss_f = df_bs.copy(), df_ss.copy()

# Score Calculation
def calc_bs(row):
    val = sum(row[m] * WEIGHTS[m] for m in selected_metrics)
    math = " + ".join([f"{row[m]}{m[0]}×{WEIGHTS[m]}" for m in selected_metrics])
    return val, math

if not df_bs_f.empty:
    df_bs_f['Score'], df_bs_f['Math'] = zip(*df_bs_f.apply(calc_bs, axis=1))
if not df_ss_f.empty:
    df_ss_f['Score'] = df_ss_f['Reads_per_Post'] + (df_ss_f['Link_Clicks_in_Post'] if 'Clicks' in selected_metrics else 0)

# 5. Header & Primary KPIs
st.title("🛰️ E-DUST engagement matrix")
st.markdown(f"[🦋 Bluesky](https://bsky.app/profile/cznews.bsky.social)  •  [✉️ Substack](https://criticalzonenews.substack.com/)")

# New: Total Dataset Downloads right under the title
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Dataset Downloads", "13") # Dummy value as requested

total_likes = df_bs_f['Likes'].sum() if not df_bs_f.empty else 0
total_clicks = (df_bs_f['Clicks'].sum() if not df_bs_f.empty else 0) + (df_ss_f['Link_Clicks_in_Post'].sum() if not df_ss_f.empty else 0)

c2.metric("Total Post Likes", f"{total_likes:,}")
c3.metric("Total Link Clicks", f"{total_clicks:,}")
c4.metric("Avg daily Bluesky Engagement Points", f"{df_bs_f['Score'].mean():.1f}" if not df_bs_f.empty else "0")
c5.metric("Avg daily Substack Engagement Points", f"{df_ss_f['Score'].mean():.1f}" if not df_ss_f.empty else "0")

st.markdown("---")

# 6. Bluesky Section
st.header("🦋 Bluesky Deep Dive")

if not df_bs_f.empty:
    bs_trend = df_bs_f.groupby('Date')[['Score']].sum().reset_index()
    fig_bs_main = px.line(bs_trend, x='Date', y='Score', title="Overall Weighted Engagement Trend (Engagement Points)",
                         line_shape='spline')
    fig_bs_main.update_traces(line_color='#1E293B', line_width=4)
    st.plotly_chart(fig_bs_main, use_container_width=True)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    metric_map = [('Likes', m_col1), ('Clicks', m_col2), ('Comments', m_col3), ('Shares', m_col4)]

    for m_name, col in metric_map:
        with col:
            if m_name in selected_metrics:
                m_daily = df_bs_f.groupby('Date')[m_name].sum().reset_index()
                fig = px.area(m_daily, x='Date', y=m_name, title=f"Daily {m_name}",
                             color_discrete_sequence=[METRIC_COLORS[m_name]])
                fig.update_layout(height=220, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"{m_name} filter is OFF")

st.markdown("---")

# 7. Substack Section
st.header("✉️ Substack Insights")

if not df_ss_f.empty:
    sub_col1, sub_col2 = st.columns([2, 1])
    
    with sub_col1:
        fig_ss_mix = go.Figure()
        fig_ss_mix.add_trace(go.Bar(x=df_ss_f['Date'], y=df_ss_f['Reads_per_Post'], name='Reads', marker_color=METRIC_COLORS['Reads']))
        if 'Clicks' in selected_metrics:
            fig_ss_mix.add_trace(go.Bar(x=df_ss_f['Date'], y=df_ss_f['Link_Clicks_in_Post'], name='Clicks', marker_color=METRIC_COLORS['Clicks']))
        fig_ss_mix.update_layout(barmode='group', title="Content Reach: Reads vs Link Clicks", height=400)
        st.plotly_chart(fig_ss_mix, use_container_width=True)

    with sub_col2:
        fig_ss_growth = px.area(df_ss_f, x='Date', y='Followers_Over_Time', title="Follower Trend",
                               color_discrete_sequence=['#64748B'])
        fig_ss_growth.update_layout(height=400)
        st.plotly_chart(fig_ss_growth, use_container_width=True)

st.markdown("---")

# 8. Strategy Rose Diagram
st.subheader("🌹 Strategy Rose: Post Type Efficiency (Bluesky)")
if not df_bs_f.empty:
    rose_data = df_bs_f.groupby('Post_Type')['Score'].mean().reset_index()
    
    fig_rose = px.bar_polar(rose_data, r="Score", theta="Post_Type",
                            color="Score", template="plotly_white",
                            color_continuous_scale=px.colors.sequential.Plasma,
                            title="Average Engagement Points per Category")
    
    fig_rose.update_layout(
        polar=dict(
            radialaxis=dict(showticklabels=False, ticks='')
        ),
        height=600
    )
    st.plotly_chart(fig_rose, use_container_width=True)
else:
    st.info("No Bluesky data available for the Rose Chart.")
