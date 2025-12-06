import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
from datetime import datetime

# Initialize Firebase
if not firebase_admin._apps:
    # Use Streamlit secrets
    cred_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://water-monitoring-54106-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

st.set_page_config(page_title="Water Quality Monitor", layout="wide")
st.title("🌊 Water Quality Monitoring System")
st.markdown("**Real-time monitoring menggunakan ESP32, DS18B20, dan TDS Sensor**")

placeholder = st.empty()

while True:
    ref = db.reference('/current')
    data = ref.get()
    
    if data:
        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            
            temp = data.get('temperature', 0)
            tds = data.get('tds', 0)
            status = data.get('status', 'UNKNOWN')
            
            with col1:
                st.metric("🌡️ Temperature", f"{temp:.1f}°C")
            
            with col2:
                st.metric("💧 TDS", f"{tds:.0f} ppm")
            
            with col3:
                st.metric("📊 Status", status)
            
            st.divider()
            
            st.subheader("Kualitas Air")
            if tds < 50:
                st.success("✓ Excellent - Air murni/suling")
            elif tds < 300:
                st.success("✓ Excellent - Kualitas sangat baik")
            elif tds < 600:
                st.info("✓ Good - Kualitas baik")
            elif tds < 900:
                st.warning("⚠ Fair - Kualitas cukup")
            elif tds < 1200:
                st.warning("⚠ Poor - Kualitas buruk")
            else:
                st.error("❌ Very Poor - Kualitas sangat buruk")
            
            st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("⚠️ Tidak ada data. Pastikan ESP32 terkoneksi.")
    
    time.sleep(3)
