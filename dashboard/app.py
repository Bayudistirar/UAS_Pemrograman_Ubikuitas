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

# Title
st.title("🌊 Water Quality Monitoring System")
st.markdown("**Real-time monitoring menggunakan ESP32, DS18B20, dan TDS Sensor**")

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
st.subheader("📊 Current Reading")

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
    
    with col2:
        st.metric("💧 TDS", f"{tds:.0f} ppm")
    
    with col3:
        st.metric("📊 Status", status)
        st.caption(f"Updated: {time_str}")
    
    with col4:
        if tds < 300:
            quality = "Excellent"
            color = "🟢"
        elif tds < 600:
            quality = "Good"
            color = "🟡"
        elif tds < 900:
            quality = "Fair"
            color = "🟠"
        else:
            quality = "Poor"
            color = "🔴"
        st.metric("Quality", f"{color} {quality}")
    
    # Alert banner for poor quality
    if tds > 900 or temp < 15 or temp > 35:
        st.error("🚨 **ALERT: Water quality is POOR!** TDS too high or temperature out of range.")
    elif tds > 600 or temp < 20 or temp > 30:
        st.warning("⚠️ **WARNING: Water quality is declining.** Monitor closely.")
    
else:
    st.warning("⚠️ No data available. Check ESP32 connection.")

st.divider()

# Historical Trends Section
st.subheader("📈 Historical Trends")

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
            line=dict(color='#FF6B6B', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)',
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M:%S}</b><br>Temp: %{y:.1f}°C<extra></extra>'
        )
    )
    
    fig_temp.update_layout(
        title="🌡️ Temperature Trend",
        xaxis_title="Time (Real Clock)",
        yaxis_title="Temperature (°C)",
        height=300,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=50, b=50)
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
            line=dict(color='#4ECDC4', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(78, 205, 196, 0.2)',
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M:%S}</b><br>TDS: %{y:.0f} ppm<extra></extra>'
        )
    )
    
    fig_tds.update_layout(
        title="💧 TDS Trend",
        xaxis_title="Time (Real Clock)",
        yaxis_title="TDS (ppm)",
        height=300,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    if time_span_hours < 1:
        fig_tds.update_xaxes(tickformat='%H:%M:%S', tickangle=-45)
    elif time_span_hours < 24:
        fig_tds.update_xaxes(tickformat='%H:%M', tickangle=-45)
    else:
        fig_tds.update_xaxes(tickformat='%m-%d %H:%M', tickangle=-45)
    
    st.plotly_chart(fig_tds, use_container_width=True)
    
    # Statistics
    st.subheader("📊 Statistics")
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

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
