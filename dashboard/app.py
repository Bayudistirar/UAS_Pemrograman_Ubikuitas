import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
from datetime import datetime
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
st.title("🌊 Water Quality Monitoring System")
st.markdown("**Real-time monitoring menggunakan ESP32, DS18B20, dan TDS Sensor**")

# Sidebar controls
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
history_limit = st.sidebar.slider("History Data Points", 10, 100, 50)

# Main content
current_placeholder = st.empty()
chart_placeholder = st.empty()
stats_placeholder = st.empty()
export_placeholder = st.empty()

def get_current_data():
    ref = db.reference('/current')
    return ref.get()

def get_history_data(limit):
    ref = db.reference('/readings').order_by_key().limit_to_last(limit)
    data = ref.get()
    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df.sort_values('datetime')
    return None

while auto_refresh:
    # Current data
    current = get_current_data()
    
    if current:
        with current_placeholder.container():
            st.subheader("📊 Current Reading")
            col1, col2, col3, col4 = st.columns(4)
            
            temp = current.get('temperature', 0)
            tds = current.get('tds', 0)
            status = current.get('status', 'UNKNOWN')
            
            with col1:
                st.metric("🌡️ Temperature", f"{temp:.1f}°C")
            
            with col2:
                st.metric("💧 TDS", f"{tds:.0f} ppm")
            
            with col3:
                st.metric("📊 Status", status)
            
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
            
            st.divider()
        
        # Historical data & charts
        history_df = get_history_data(history_limit)
        
        if history_df is not None and len(history_df) > 0:
            with chart_placeholder.container():
                st.subheader("📈 Historical Trends")
                
                # Create dual-axis chart
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(
                    go.Scatter(
                        x=history_df['datetime'],
                        y=history_df['temperature'],
                        name="Temperature (°C)",
                        line=dict(color='red', width=2)
                    ),
                    secondary_y=False
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=history_df['datetime'],
                        y=history_df['tds'],
                        name="TDS (ppm)",
                        line=dict(color='blue', width=2)
                    ),
                    secondary_y=True
                )
                
                fig.update_xaxes(title_text="Time")
                fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False)
                fig.update_yaxes(title_text="TDS (ppm)", secondary_y=True)
                fig.update_layout(height=400, hovermode='x unified')
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            with stats_placeholder.container():
                st.subheader("📊 Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Avg Temperature", f"{history_df['temperature'].mean():.1f}°C")
                    st.metric("Min", f"{history_df['temperature'].min():.1f}°C")
                    st.metric("Max", f"{history_df['temperature'].max():.1f}°C")
                
                with col2:
                    st.metric("Avg TDS", f"{history_df['tds'].mean():.0f} ppm")
                    st.metric("Min", f"{history_df['tds'].min():.0f} ppm")
                    st.metric("Max", f"{history_df['tds'].max():.0f} ppm")
                
                with col3:
                    ok_count = (history_df['status'] == 'OK').sum()
                    total = len(history_df)
                    st.metric("OK Status", f"{ok_count}/{total}")
                    st.metric("Success Rate", f"{(ok_count/total*100):.1f}%")
                
                with col4:
                    st.metric("Total Readings", len(history_df))
                    st.metric("Data Points", history_limit)
            
            # Export data
            with export_placeholder.container():
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
            with chart_placeholder.container():
                st.info("⏳ Waiting for historical data... (Data logged every minute)")
    
    else:
        with current_placeholder.container():
            st.warning("⚠️ Tidak ada data. Pastikan ESP32 terkoneksi.")
    
    time.sleep(3)

# If auto-refresh disabled
if not auto_refresh:
    st.info("Auto-refresh disabled. Toggle in sidebar to enable.")
