import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="E-DUST Engagement Matrix", layout="wide")

# Constants for Math
WEIGHTS = {
    'Clicks': 1,
    'Likes': 2,
    'Comments': 3,
    'Shares': 4,
    'Reads': 1  # Specific to Substack
}

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
    # Load Substack
    df_ss = pd.read_csv('engagement_matrix_sample - Substack (sample).csv')
    df_ss['Date'] = pd.to_datetime(df_ss['Date'])
    
    # Load Bluesky
    df_bs = pd.read_csv('engagement_matrix_sample - Bluesky (sample).csv')
    df_bs['Date'] = pd.to_datetime(df_bs['Date'])
    
    return df_bs, df_ss

try:
    df_bs, df_ss = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 4. Sidebar: Dynamic Filters
st.sidebar.title("📊 Control Panel")

# Metric Selector
st.sidebar.markdown("### 🔍 Display Metrics")
available_metrics = ['Likes', 'Clicks', 'Shares', 'Comments']
selected_metrics = st.sidebar.multiselect(
    "Include in Score:",
    options=available_metrics,
    default=available_metrics
)

# Legend showing weights for selected items
st.sidebar.markdown("### 🔑 Active Weights")
legend_html = "<div class='weight-legend'>"
for m in selected_metrics:
    legend_html += f"<strong>{m}:</strong> {WEIGHTS[m]}<br>"
if 'Reads' not in selected_metrics: # Reads are foundational for Substack reach
    legend_html += "<em>Reads (Substack): 1</em>"
legend_html += "</div>"
st.sidebar.markdown(legend_html, unsafe_allow_html=True)

st.sidebar.markdown("---")
min_date = min(df_bs['Date'].min(), df_ss['Date'].min())
max_date = max(df_bs['Date'].max(), df_ss['Date'].max())
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# 5. Dynamic Calculation Logic
def calculate_dynamic_score(row, platform):
    score = 0
    math_parts = []
    
    if platform == 'Bluesky':
        for m in selected_metrics:
            val = row.get(m, 0)
            weight = WEIGHTS[m]
            score += val * weight
            math_parts.append(f"{val}{m[0]}×{weight}")
    else: # Substack
        # Always include Reads as the base for Substack, plus Clicks if selected
        score += row['Reads_per_Post'] * WEIGHTS['Reads']
        math_parts.append(f"{row['Reads_per_Post']}R×{WEIGHTS['Reads']}")
        if 'Clicks' in selected_metrics:
            score += row['Link_Clicks_in_Post'] * WEIGHTS['Clicks']
            math_parts.append(f"{row['Link_Clicks_in_Post']}C×{WEIGHTS['Clicks']}")
            
    return score, " + ".join(math_parts)

# Apply Date Filter & Calculate Scores
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_bs_f = df_bs[(df_bs['Date'] >= start) & (df_bs['Date'] <= end)].copy()
    df_ss_f = df_ss[(df_ss['Date'] >= start) & (df_ss['Date'] <= end)].copy()
else:
    df_bs_f, df_ss_f = df_bs.copy(), df_ss.copy()

# Calculate Dynamic Scores and Math Strings
if not df_bs_f.empty:
    res_bs = df_bs_f.apply(lambda r: calculate_dynamic_score(r, 'Bluesky'), axis=1)
    df_bs_f['Score'], df_bs_f['Math'] = zip(*res_bs)

if not df_ss_f.empty:
    res_ss = df_ss_f.apply(lambda r: calculate_dynamic_score(r, 'Substack'), axis=1)
    df_ss_f['Score'], df_ss_f['Math'] = zip(*res_ss)

# 6. Header & Global KPIs
st.title("🛰️ E-DUST engagement matrix")
st.markdown(f"[🦋 Bluesky Profile](https://bsky.app/profile/cznews.bsky.social)  •  [✉️ Substack Newsletter](https://criticalzonenews.substack.com/)")
st.markdown("---")

# Global KPI Row: Focused on Total Likes and Total Clicks
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
total_likes = df_bs_f['Likes'].sum() # Substack sample doesn't have "Likes" column currently
total_clicks = df_bs_f['Clicks'].sum() + df_ss_f['Link_Clicks_in_Post'].sum()

kpi_col1.metric("Total Likes", f"{total_likes:,}")
kpi_col2.metric("Total Clicks", f"{total_clicks:,}")
kpi_col3.metric("Avg Score (BS)", f"{df_bs_f['Score'].mean():.1f}" if not df_bs_f.empty else "0")
kpi_col4.metric("Avg Score (SS)", f"{df_ss_f['Score'].mean():.1f}" if not df_ss_f.empty else "0")

st.markdown("---")

# 7. Insights Sections
col1, col2 = st.columns(2)

with col1:
    st.header("🦋 Bluesky Insights")
    if not df_bs_f.empty:
        # Trend
        fig_bs_line = px.line(df_bs_f.groupby('Date')[['Score']].sum().reset_index(), 
                             x='Date', y='Score', title="Filtered Engagement Trend",
                             line_shape='spline', color_discrete_sequence=['#0085FF'])
        st.plotly_chart(fig_bs_line, use_container_width=True)
        
        # Post Type
        df_bs_post = df_bs_f.groupby('Post_Type')['Score'].mean().reset_index().sort_values('Score')
        fig_bs_bar = px.bar(df_bs_post, x='Score', y='Post_Type', orientation='h',
                           title="Performance by Post Type (Avg)", 
                           color='Score', color_continuous_scale='Blues',
                           hover_data={'Score': ':.2f'})
        st.plotly_chart(fig_bs_bar, use_container_width=True)

with col2:
    st.header("✉️ Substack Insights")
    if not df_ss_f.empty:
        # Growth
        fig_ss_growth = px.area(df_ss_f, x='Date', y='Followers_Over_Time', title="Follower Growth",
                               color_discrete_sequence=['#FF6719'])
        st.plotly_chart(fig_ss_growth, use_container_width=True)
        
        # Reach vs Action (with Dynamic Hover Math)
        fig_ss_mix = go.Figure()
        fig_ss_mix.add_trace(go.Bar(x=df_ss_f['Date'], y=df_ss_f['Reads_per_Post'], name='Reads', marker_color='#FF6719', 
                                   customdata=df_ss_f['Math'], hovertemplate="Reads: %{y}<br>Math: %{customdata}"))
        if 'Clicks' in selected_metrics:
            fig_ss_mix.add_trace(go.Bar(x=df_ss_f['Date'], y=df_ss_f['Link_Clicks_in_Post'], name='Clicks', marker_color='#FFA07A',
                                       customdata=df_ss_f['Math'], hovertemplate="Clicks: %{y}<br>Math: %{customdata}"))
        fig_ss_mix.update_layout(barmode='group', title="Reads vs. Link Clicks", height=400)
        st.plotly_chart(fig_ss_mix, use_container_width=True)

# 8. Comparison Strategy Matrix
st.markdown("---")
st.subheader("🎯 Strategy Heatmap")
if not df_bs_f.empty:
    heat_df = df_bs_f.groupby(['Post_Type', 'Platform'])['Score'].mean().unstack()
    fig_heat = px.imshow(heat_df, text_auto=".1f", color_continuous_scale='Viridis', aspect="auto",
                         title="Bluesky Post Type Efficiency (Selected Metrics Only)")
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Select Bluesky to see the Strategy Matrix.")
