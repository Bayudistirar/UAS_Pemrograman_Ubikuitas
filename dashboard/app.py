import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

# Title
st.title("🌊 Water Quality Monitoring System")
st.markdown("**Real-time monitoring menggunakan ESP32, DS18B20, dan TDS Sensor**")

def get_current_data():
    ref = db.reference('/current')
    return ref.get()

def get_history_data(limit):
    ref = db.reference('/readings').order_by_key().limit_to_last(limit)
    data = ref.get()
    if data:
        records = []
        for key, value in data.items():
            if 'timestamp' in value:
                # Firebase timestamp is in milliseconds
                value['datetime'] = pd.to_datetime(value['timestamp'], unit='ms')
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
    if 'timestamp' in current:
        last_update = datetime.fromtimestamp(current['timestamp'] / 1000)
        time_ago = datetime.now() - last_update
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
else:
    st.warning("⚠️ No data available. Check ESP32 connection.")

st.divider()

# Historical Trends Section
st.subheader("📈 Historical Trends")

if history_df is not None and len(history_df) > 0:
    # Create chart with formatted time
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=history_df['datetime'],
            y=history_df['temperature'],
            name="Temperature (°C)",
            line=dict(color='#FF6B6B', width=2),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=history_df['datetime'],
            y=history_df['tds'],
            name="TDS (ppm)",
            line=dict(color='#4ECDC4', width=2),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=True
    )
    
    fig.update_xaxes(
        title_text="Time",
        tickformat='%H:%M:%S',
        tickangle=-45
    )
    fig.update_yaxes(title_text="<b>Temperature</b> (°C)", secondary_y=False, titlefont=dict(color='#FF6B6B'))
    fig.update_yaxes(title_text="<b>TDS</b> (ppm)", secondary_y=True, titlefont=dict(color='#4ECDC4'))
    fig.update_layout(
        height=450,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=30, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
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
        time_span = (history_df['datetime'].max() - history_df['datetime'].min()).total_seconds() / 60
        st.caption(f"Span: {time_span:.0f} minutes")
    
    # Export section
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        csv = history_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"water_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
else:
    st.info("⏳ Waiting for historical data... (Data logged every minute)")

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
