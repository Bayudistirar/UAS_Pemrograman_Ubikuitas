# Water Quality Monitoring System
**Proyek Akhir Semester - Pemrograman Ubikuitas**

## 📋 Deskripsi
Sistem monitoring kualitas air real-time menggunakan ESP32, sensor DS18B20 (suhu), dan TDS sensor yang terintegrasi dengan Firebase Realtime Database dan dashboard Streamlit.

## 🎯 Fitur
- ✓ Pembacaan suhu air real-time
- ✓ Pengukuran TDS (Total Dissolved Solids)
- ✓ Upload data otomatis ke Firebase setiap 3 detik
- ✓ Dashboard web interaktif dengan Streamlit
- ✓ Status kualitas air otomatis

## 🛠️ Komponen Hardware
- ESP32 DevKit
- DS18B20 Temperature Sensor
- TDS Sensor (Analog)
- Resistor 10kΩ (pull-up DS18B20)
- Kabel jumper

## 📐 Diagram Koneksi

### DS18B20 Temperature Sensor
```
VCC  → 3.3V
GND  → GND
DATA → GPIO 27 (+ resistor 10kΩ pull-up ke 3.3V)
```

### TDS Sensor
```
VCC → 5V
GND → GND
OUT → GPIO 34 (ADC1_6)
```

## 🚀 Instalasi

### 1. Hardware (ESP32)
```bash
# Install Arduino IDE + ESP32 board support
# Install libraries via Arduino Library Manager:
# - OneWire
# - DallasTemperature  
# - FirebaseESP32 (by Mobizt)
```

1. Buka `hardware/water_monitor.ino`
2. Update WiFi credentials
3. Upload ke ESP32

### 2. Dashboard (Streamlit)
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

## 📊 Cara Kerja
1. **ESP32** membaca data sensor setiap 3 detik
2. Data dikirim ke **Firebase Realtime Database**
3. **Streamlit dashboard** membaca dan menampilkan data real-time
4. Sistem mengevaluasi kualitas air berdasarkan nilai TDS

## 📈 Standar Kualitas Air (TDS)
- **0-50 ppm**: Excellent (Air murni/suling)
- **50-300 ppm**: Excellent (Sangat baik)
- **300-600 ppm**: Good (Baik)
- **600-900 ppm**: Fair (Cukup)
- **900-1200 ppm**: Poor (Buruk)
- **>1200 ppm**: Very Poor (Sangat buruk)

## 🔧 Teknologi
- **Hardware**: ESP32, DS18B20, TDS Sensor
- **Backend**: Firebase Realtime Database
- **Frontend**: Streamlit (Python)
- **Protocol**: WiFi, HTTPS
- **Libraries**: OneWire, DallasTemperature, FirebaseESP32

## 👥 Anggota Tim
- [Nama Lengkap] - [NIM]

## 📝 Lisensi
MIT License - Proyek Akademik

## 📚 Referensi
- [ESP32 Documentation](https://docs.espressif.com/)
- [Firebase Realtime Database](https://firebase.google.com/docs/database)
- [Streamlit Documentation](https://docs.streamlit.io/)
