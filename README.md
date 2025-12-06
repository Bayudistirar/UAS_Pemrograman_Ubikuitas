# Water Quality Monitoring System
**Proyek Akhir Semester - Pemrograman Ubikuitas**

## 📋 Deskripsi
Sistem monitoring kualitas air real-time menggunakan ESP32, sensor DS18B20 (suhu), dan TDS sensor yang terintegrasi dengan Firebase Realtime Database dan dashboard Streamlit.

## 🎯 Fitur
- Pembacaan suhu air real-time
- Pengukuran TDS (Total Dissolved Solids)
- Upload data otomatis ke Firebase setiap 3 detik
- Dashboard web interaktif dengan Streamlit
- Status kualitas air otomatis

## 🛠️ Komponen Hardware
- ESP32 DevKit
- DS18B20 Temperature Sensor
- TDS Sensor (Analog)
- Resistor 10kΩ (pull-up DS18B20)
- Kabel jumper

## 📐 Diagram Koneksi
```
DS18B20:
  - VCC  → 3.3V
  - GND  → GND
  - DATA → GPIO 27 (+ 10kΩ pull-up ke 3.3V)

TDS Sensor:
  - VCC → 5V
  - GND → GND
  - OUT → GPIO 34 (ADC1_6)
```

## 🚀 Instalasi

### Hardware (ESP32)
1. Install Arduino IDE + ESP32 board support
2. Install libraries:
   - OneWire
   - DallasTemperature
   - FirebaseESP32
3. Upload `hardware/esp32_code/water_monitor.ino`
4. Update WiFi credentials di code

### Dashboard (Streamlit)
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

## 📊 Live Dashboard
[Link Streamlit App deployed]

## 🔧 Teknologi
- **Hardware**: ESP32, DS18B20, TDS Sensor
- **Backend**: Firebase Realtime Database
- **Frontend**: Streamlit (Python)
- **Protocol**: WiFi, HTTPS

## 👥 Tim
- [Nama] - [NIM]

## 📝 Lisensi
MIT License - Proyek Akademik

## 📚 Referensi
- ESP32 Documentation
- Firebase Realtime Database
- Streamlit Documentation
