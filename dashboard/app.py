import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import pytz

# Initialize Firebase
if not firebase_admin._apps:
    cred_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://water-monitoring-54106-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

st.set_page_config(page_title="Water Quality Monitor", layout="wide")

# ============= CSS CUSTOM =============
st.markdown("""
<style>
    /* Main Background */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Metric Cards Styling */
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Metric Label */
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        font-weight: 600;
        color: #64748b;
    }
    
    /* Metric Value */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: #1e293b;
    }
    
    /* Metric Delta */
    [data-testid="stMetricDelta"] {
        font-size: 14px;
        font-weight: 600;
    }
    
    /* Progress Bar Styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%);
        border-radius: 10px;
        height: 8px;
    }
    
    .stProgress > div > div > div {
        background-color: #e2e8f0;
        border-radius: 10px;
        height: 8px;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e40af 0%, #3b82f6 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: white;
    }
    
    /* Sidebar Checkbox */
    [data-testid="stSidebar"] .stCheckbox label {
        color: white !important;
    }
    
    /* Headers */
    h1 {
        color: white;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 600;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
    
    /* Alert Boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Info Box */
    .element-container div[data-testid="stAlert"] {
        border-radius: 10px;
    }
    
    /* Buttons */
    .stDownloadButton button {
        background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stDownloadButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Caption Text */
    .caption {
        color: #64748b;
        font-size: 14px;
    }
    
    /* Plotly Charts */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# ============= HEADER WITH GRADIENT =============
st.markdown("""
<div style='background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%); 
            padding: 35px; border-radius: 15px; margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);'>
    <h1 style='color: white; margin: 0; font-size: 2.5rem;'>💧 Water Quality Monitoring System</h1>
    <p style='color: #e0f2fe; margin: 10px 0 0 0; font-size: 1.1rem;'>
        Real-time monitoring menggunakan ESP32, DS18B20, dan TDS Sensor
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 10, 3)
history_limit = st.sidebar.slider("History Data Points", 10, 100, 50)

# Timezone selector - DEFAULT WITA
timezone_options = {
    "WIB (UTC+7)": "Asia/Jakarta",
    "WITA (UTC+8)": "Asia/Makassar",
    "WIT (UTC+9)": "Asia/Jayapura",
    "UTC": "UTC"
}
selected_tz = st.sidebar.selectbox("Timezone", list(timezone_options.keys()), index=1)
user_timezone = pytz.timezone(timezone_options[selected_tz])

st.sidebar.markdown("---")
st.sidebar.markdown("**Last Update:**")
current_time = datetime.now(user_timezone).strftime("%H:%M:%S")
st.sidebar.code(current_time)

def convert_timestamp_to_datetime(timestamp_value):
    """Convert timestamp to datetime with timezone"""
    try:
        if isinstance(timestamp_value, (int, float)):
            # Check if milliseconds or seconds
            if timestamp_value > 1e12:  # Milliseconds
                dt = datetime.fromtimestamp(timestamp_value / 1000, tz=user_timezone)
            else:  # Seconds
                dt = datetime.fromtimestamp(timestamp_value / 1000, tz=user_timezone)
        else:
            dt = datetime.now(user_timezone)
        return dt
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return datetime.now(user_timezone)

def get_current_data():
    ref = db.reference('/current')
    return ref.get()

def get_history_data(limit):
    ref = db.reference('/readings').order_by_key().limit_to_last(limit)
    data = ref.get()
    if data:
        records = []
        for key, value in data.items():
            if 'timestamp' in value and value['timestamp'] is not None:
                value['datetime'] = convert_timestamp_to_datetime(value['timestamp'])
                records.append(value)
        
        if records:
            df = pd.DataFrame(records)
            return df.sort_values('datetime')
    return None

# Get data
current = get_current_data()
history_df = get_history_data(history_limit)

# Current Reading Section
st.markdown("### 📊 Current Reading")

if current:
    col1, col2, col3, col4 = st.columns(4)
    
    temp = current.get('temperature', 0)
    tds = current.get('tds', 0)
    status = current.get('status', 'UNKNOWN')
    
    # Format timestamp
    if 'timestamp' in current and current['timestamp'] is not None:
        last_update = convert_timestamp_to_datetime(current['timestamp'])
        time_ago = datetime.now(user_timezone) - last_update
        seconds_ago = int(time_ago.total_seconds())
        
        if seconds_ago < 60:
            time_str = f"{seconds_ago}s ago"
        elif seconds_ago < 3600:
            time_str = f"{seconds_ago // 60}m ago"
        else:
            time_str = last_update.strftime('%H:%M:%S')
    else:
        time_str = "Unknown"
    
    with col1:
        st.metric("🌡️ Temperature", f"{temp:.1f}°C")
        # Progress bar untuk Temperature
        temp_percentage = min(max((temp - 15) / 20, 0), 1)
        st.progress(temp_percentage)
        if 20 <= temp <= 30:
            st.caption("Status: 🟢 IDEAL")
        else:
            st.caption("Status: 🟡 WARNING")
    
    with col2:
        st.metric("💧 TDS", f"{tds:.0f} ppm")
        # Progress bar untuk TDS
        tds_percentage = min(tds / 300, 1.0)
        st.progress(tds_percentage)
        if tds < 300:
            st.caption("Status: 🟢 GOOD")
        elif tds < 600:
            st.caption("Status: 🟡 FAIR")
        else:
            st.caption("Status: 🔴 POOR")
    
    with col3:
        st.metric("📊 Status", status)
        st.caption(f"Updated: {time_str}")
    
    with col4:
        if tds < 300:
            quality = "Excellent"
            color = "🟢"
            quality_score = 90
        elif tds < 600:
            quality = "Good"
            color = "🟡"
            quality_score = 70
        elif tds < 900:
            quality = "Fair"
            color = "🟠"
            quality_score = 50
        else:
            quality = "Poor"
            color = "🔴"
            quality_score = 30
        
        st.metric("Quality", f"{color} {quality}")
        st.progress(quality_score / 100)
        if quality_score > 70:
            st.caption("🟢 Air layak konsumsi")
        else:
            st.caption("🟡 Perlu perhatian")
    
    # Alert banner for poor quality
    if tds > 900 or temp < 15 or temp > 35:
        st.error("🚨 **ALERT: Water quality is POOR!** TDS too high or temperature out of range.")
    elif tds > 600 or temp < 20 or temp > 30:
        st.warning("⚠️ **WARNING: Water quality is declining.** Monitor closely.")
    
else:
    st.warning("⚠️ No data available. Check ESP32 connection.")

st.divider()

# Historical Trends Section
st.markdown("### 📈 Historical Trends")

if history_df is not None and len(history_df) > 0:
    
    # Show time range with date if spanning multiple days
    time_start = history_df['datetime'].min()
    time_end = history_df['datetime'].max()
    
    if time_start.date() == time_end.date():
        range_str = f"{time_start.strftime('%H:%M:%S')} to {time_end.strftime('%H:%M:%S')} ({time_start.strftime('%Y-%m-%d')})"
    else:
        range_str = f"{time_start.strftime('%Y-%m-%d %H:%M:%S')} to {time_end.strftime('%Y-%m-%d %H:%M:%S')}"
    
    st.caption(f"📅 Showing data from {range_str}")
    
    # Temperature Chart
    fig_temp = go.Figure()
    fig_temp.add_trace(
        go.Scatter(
            x=history_df['datetime'],
            y=history_df['temperature'],
            name="Temperature",
            line=dict(color='#ef4444', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.2)',
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M:%S}</b><br>Temp: %{y:.1f}°C<extra></extra>'
        )
    )
    
    fig_temp.update_layout(
        title="🌡️ Temperature Trend",
        xaxis_title="Time (Real Clock)",
        yaxis_title="Temperature (°C)",
        height=350,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Format x-axis based on time span
    time_span_hours = (time_end - time_start).total_seconds() / 3600
    if time_span_hours < 1:
        fig_temp.update_xaxes(tickformat='%H:%M:%S', tickangle=-45)
    elif time_span_hours < 24:
        fig_temp.update_xaxes(tickformat='%H:%M', tickangle=-45)
    else:
        fig_temp.update_xaxes(tickformat='%m-%d %H:%M', tickangle=-45)
    
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # TDS Chart
    fig_tds = go.Figure()
    fig_tds.add_trace(
        go.Scatter(
            x=history_df['datetime'],
            y=history_df['tds'],
            name="TDS",
            line=dict(color='#3b82f6', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.2)',
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M:%S}</b><br>TDS: %{y:.0f} ppm<extra></extra>'
        )
    )
    
    fig_tds.update_layout(
        title="💧 TDS Trend",
        xaxis_title="Time (Real Clock)",
        yaxis_title="TDS (ppm)",
        height=350,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    if time_span_hours < 1:
        fig_tds.update_xaxes(tickformat='%H:%M:%S', tickangle=-45)
    elif time_span_hours < 24:
        fig_tds.update_xaxes(tickformat='%H:%M', tickangle=-45)
    else:
        fig_tds.update_xaxes(tickformat='%m-%d %H:%M', tickangle=-45)
    
    st.plotly_chart(fig_tds, use_container_width=True)
    
    st.info("💡 **Tip:** Grafik interaktif - hover untuk melihat detail, zoom in/out dengan mouse")
    
    # Statistics
    st.divider()
    st.markdown("### 📊 Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Temperature", f"{history_df['temperature'].mean():.1f}°C")
        st.caption(f"Min: {history_df['temperature'].min():.1f}°C")
        st.caption(f"Max: {history_df['temperature'].max():.1f}°C")
    
    with col2:
        st.metric("Avg TDS", f"{history_df['tds'].mean():.0f} ppm")
        st.caption(f"Min: {history_df['tds'].min():.0f} ppm")
        st.caption(f"Max: {history_df['tds'].max():.0f} ppm")
    
    with col3:
        ok_count = (history_df['status'] == 'OK').sum()
        total = len(history_df)
        st.metric("OK Status", f"{ok_count}/{total}")
        st.caption(f"Success: {(ok_count/total*100):.1f}%")
    
    with col4:
        st.metric("Total Readings", len(history_df))
        time_span = (history_df['datetime'].max() - history_df['datetime'].min()).total_seconds()
        if time_span < 60:
            st.caption(f"Span: {time_span:.0f} seconds")
        elif time_span < 3600:
            st.caption(f"Span: {time_span/60:.1f} minutes")
        else:
            st.caption(f"Span: {time_span/3600:.1f} hours")
    
    # Export section
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        current_time = datetime.now(user_timezone)
        st.caption(f"🕐 Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} ({selected_tz})")
    with col2:
        csv = history_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"water_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
else:
    st.info("⏳ Waiting for historical data... (Data logged every 10 seconds)")

# ============= FOOTER =============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; font-size: 13px; padding: 20px 0;'>
    <p style='margin: 5px 0;'><strong>Built with Streamlit + Firebase + ESP32</strong></p>
    <p style='margin: 5px 0;'>Water Quality Monitoring System v1.0</p>
    <p style='margin: 5px 0; font-size: 11px;'>© 2024 - Real-time IoT Monitoring</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
