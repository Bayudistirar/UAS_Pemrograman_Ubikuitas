import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
from datetime import datetime

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(
        "water-monitoring-54106-firebase-adminsdk-fbsvc-15fbb8feb0.json"
    )
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://water-monitoring-54106-default-rtdb.asia-southeast1.firebasedatabase.app"
        },
    )

st.set_page_config(page_title="Water Monitor", layout="wide")
st.title("🌊 Water Quality Monitor")

# Create placeholders
col1, col2, col3 = st.columns(3)

# Auto-refresh
placeholder = st.empty()

while True:
    ref = db.reference("/current")
    data = ref.get()

    if data:
        with placeholder.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Temperature", f"{data.get('temperature', 0):.1f}°C")

            with col2:
                tds = data.get("tds", 0)
                st.metric("TDS", f"{tds:.0f} ppm")

            with col3:
                status = data.get("status", "UNKNOWN")
                st.metric("Status", status)

            # Quality assessment
            if tds < 300:
                st.success("✓ Excellent water quality")
            elif tds < 600:
                st.info("✓ Good water quality")
            elif tds < 900:
                st.warning("⚠ Fair water quality")
            else:
                st.error("❌ Poor water quality")

            st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("No data available")

    time.sleep(3)
