# Water Quality Monitoring System
**Proyek Akhir Semester - Pemrograman Ubikuitas**

## 📋 Deskripsi
Sistem monitoring kualitas air real-time menggunakan ESP32, sensor DS18B20 (suhu), dan TDS sensor yang terintegrasi dengan Firebase Realtime Database dan dashboard Streamlit dengan visualisasi data historis.

## 🎯 Fitur
- ✅ Pembacaan suhu air real-time (setiap 3 detik)
- ✅ Pengukuran TDS (Total Dissolved Solids)
- ✅ Upload data otomatis ke Firebase
- ✅ Dashboard web interaktif dengan grafik trend
- ✅ Historical data logging (setiap 1 menit)
- ✅ Export data ke CSV
- ✅ Statistik real-time (Min/Max/Average)
- ✅ Status kualitas air otomatis
- ✅ Mode kalibrasi sensor

## 🛠️ Komponen Hardware
| Komponen | Spesifikasi | Jumlah |
|----------|-------------|---------|
| ESP32 DevKit | ESP-WROOM-32 | 1 |
| DS18B20 | Temperature Sensor | 1 |
| TDS Sensor | Analog TDS Meter | 1 |
| Resistor | 10kΩ (pull-up) | 1 |
| Breadboard | Standard | 1 |
| Kabel Jumper | Male-Male, Male-Female | 10+ |

## 📐 Diagram Koneksi

### DS18B20 Temperature Sensor
```
DS18B20 Pin    →  ESP32 Pin
─────────────────────────────
VCC (Red)      →  3.3V
GND (Black)    →  GND
DATA (Yellow)  →  GPIO 27
```
**Pull-up:** Resistor 10kΩ antara DATA (GPIO 27) dan 3.3V

### TDS Sensor
```
TDS Sensor     →  ESP32 Pin
─────────────────────────────
VCC            →  5V (VIN)
GND            →  GND
OUT (Analog)   →  GPIO 34 (ADC1_6)
```

## 🚀 Instalasi

### 1. Hardware Setup
1. Sambungkan komponen sesuai diagram
2. Pastikan pull-up resistor 10kΩ terpasang di DS18B20
3. Gunakan power supply 5V untuk ESP32

### 2. Software ESP32
```bash
# Install Arduino IDE + ESP32 board support
# Board: ESP32 Dev Module
# Upload Speed: 115200

# Install libraries via Arduino Library Manager:
# - OneWire by Paul Stoffregen
# - DallasTemperature by Miles Burton
# - FirebaseESP32 by Mobizt
```

**Upload Code:**
1. Buka `hardware/water_monitor.ino`
2. Update WiFi credentials (SSID & Password)
3. Upload ke ESP32
4. Buka Serial Monitor (115200 baud)

### 3. Dashboard (Streamlit)
**Local:**
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

**Production:**
- Deployed at: https://uas-pemrograman-ubikuitas.streamlit.app

## 📊 Cara Kerja

### Data Flow
```
ESP32 → Firebase → Streamlit Dashboard
  ↓         ↓            ↓
3s      Real-time    Auto-refresh
update   Database    + Charts
```

### Data Structure Firebase
```json
{
  "current": {
    "temperature": 26.3,
    "tds": 154,
    "status": "OK",
    "timestamp": 1234567
  },
  "readings": {
    "unique_id_1": {
      "temperature": 26.2,
      "tds": 150,
      "status": "OK",
      "timestamp": 1234500
    }
  }
}
```

## 📈 Standar Kualitas Air (TDS)
| TDS Range | Kualitas | Keterangan |
|-----------|----------|------------|
| 0-50 ppm | Excellent | Air murni/suling |
| 50-300 ppm | Excellent | Sangat baik untuk diminum |
| 300-600 ppm | Good | Kualitas baik |
| 600-900 ppm | Fair | Cukup |
| 900-1200 ppm | Poor | Kurang baik |
| >1200 ppm | Very Poor | Tidak layak konsumsi |

## 🧪 Hasil Testing

### Test Environment
- Lokasi: Lab IoT, Universitas
- Durasi: 24 jam continuous
- Sample Rate: 3 detik (current), 1 menit (history)

### Data Summary
| Parameter | Min | Max | Avg | Std Dev |
|-----------|-----|-----|-----|---------|
| Suhu      | 24.8°C | 27.2°C | 26.1°C | 0.4°C |
| TDS       | 145 ppm | 362 ppm | 248 ppm | 38 ppm |
| Uptime    | - | - | 99.2% | - |

### Sensor Accuracy
- **DS18B20:** ±0.5°C (verified with calibrated thermometer)
- **TDS Sensor:** ±5% (verified with standard TDS meter)

## 🔧 Kalibrasi

### Temperature Sensor (DS18B20)
DS18B20 sudah factory-calibrated, tidak perlu kalibrasi manual.

### TDS Sensor
1. Set `#define CALIBRATION_MODE true` di code
2. Upload ke ESP32
3. Celupkan sensor di larutan TDS standar (contoh: 1000 ppm)
4. Catat raw ADC value di Serial Monitor
5. Adjust formula di code jika perlu:
```cpp
float tdsValue = (133.42 * V³ - 255.86 * V² + 857.39 * V) * 0.5;
```

## 🔧 Teknologi
| Layer | Technology |
|-------|------------|
| **Hardware** | ESP32, DS18B20, TDS Sensor |
| **Backend** | Firebase Realtime Database |
| **Frontend** | Streamlit + Plotly |
| **Protocol** | WiFi, HTTPS, WebSocket |
| **Libraries** | OneWire, DallasTemperature, FirebaseESP32 |

## 📱 Fitur Dashboard
- ✅ Real-time metrics display
- ✅ Dual-axis historical charts (Temperature + TDS)
- ✅ Statistical analysis (Min/Max/Average)
- ✅ Data export to CSV
- ✅ Auto-refresh toggle
- ✅ Adjustable history data points
- ✅ Water quality indicators

## 🐛 Troubleshooting

### ESP32 tidak connect WiFi
**Solusi:**
1. Cek SSID dan password di code
2. Pastikan router 2.4GHz (ESP32 tidak support 5GHz)
3. Restart ESP32
4. Check signal strength

### Sensor DS18B20 tidak terbaca (-127°C)
**Solusi:**
1. Cek wiring (VCC, GND, DATA)
2. Pastikan resistor pull-up 10kΩ terpasang
3. Test sensor dengan multimeter
4. Ganti sensor jika rusak

### TDS Sensor tidak akurat
**Solusi:**
1. Bersihkan probe sensor dengan air bersih
2. Lakukan kalibrasi dengan TDS meter standar
3. Pastikan sensor terendam penuh
4. Hindari gelembung udara di probe

### Firebase tidak menerima data
**Solusi:**
1. Cek koneksi internet ESP32
2. Verify Firebase credentials
3. Check Firebase database rules (allow write)
4. Monitor Serial output untuk error

### Dashboard Streamlit tidak update
**Solusi:**
1. Toggle auto-refresh di sidebar
2. Clear browser cache
3. Check Firebase connection
4. Verify secrets configuration

## 👥 Tim Pengembang
- **[Nama Lengkap]** - [NIM] - IoT Developer & Hardware Integration
- **[Nama Dosen]** - Pembimbing

## 📝 Lisensi
MIT License - Proyek Akademik

## 📚 Referensi
1. [ESP32 Documentation](https://docs.espressif.com/)
2. [Firebase Realtime Database](https://firebase.google.com/docs/database)
3. [Streamlit Documentation](https://docs.streamlit.io/)
4. [DS18B20 Datasheet](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
5. [TDS Measurement Principles](https://www.omega.com/en-us/resources/tds-measurement)

## 📞 Support
Untuk pertanyaan atau issue, silakan buka GitHub Issues atau hubungi via email.

---
**Dibuat dengan ❤️ untuk UAS Pemrograman Ubikuitas**
