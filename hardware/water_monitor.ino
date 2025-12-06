#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <FirebaseESP32.h>
#include <time.h>

#define WIFI_SSID "BAYU"
#define WIFI_PASSWORD "musabayu"

#define FIREBASE_HOST "water-monitoring-54106-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH "jb4Tk9uWl2s3Icsdq5KpyPy5QKuwbrzlO1WUDLsY"

#define TEMP_PIN 27
#define TDS_PIN 34
#define VREF 3.3
#define SCOUNT 30

#define CALIBRATION_MODE false

// NTP settings for WITA (UTC+8)
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 8 * 3600;  // WITA = UTC+8
const int daylightOffset_sec = 0;

OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;
FirebaseJson json;

int analogBuffer[SCOUNT];
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;

unsigned long lastRead = 0;
unsigned long lastHistory = 0;
const unsigned long READ_INTERVAL = 3000;
const unsigned long HISTORY_INTERVAL = 10000;

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi: Connected");
  Serial.println(WiFi.localIP());
  
  // Initialize NTP
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.print("Syncing time");
  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 10) {
    Serial.print(".");
    delay(1000);
    attempts++;
  }
  Serial.println();
  if (attempts < 10) {
    Serial.println("Time: Synced");
    Serial.println(&timeinfo, "Current time: %Y-%m-%d %H:%M:%S");
  } else {
    Serial.println("Time: Failed to sync (continuing anyway)");
  }
  
  // Initialize Firebase
  config.database_url = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  
  Serial.println("Firebase: Ready");
  
  tempSensor.begin();
  pinMode(TDS_PIN, INPUT);
  
  if (CALIBRATION_MODE) {
    Serial.println("\n=== CALIBRATION MODE ===");
    Serial.println("ADC | Voltage | TDS");
  } else {
    Serial.println("\nTime | Temp | TDS | Status | Firebase");
    Serial.println("────────────────────────────────────────────────");
  }
}

unsigned long getCurrentTimestamp() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return millis();
  }
  time_t now;
  time(&now);
  return (unsigned long)now * 1000;  // Convert to milliseconds
}

String getFormattedTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "??:??:??";
  }
  char buffer[9];
  strftime(buffer, sizeof(buffer), "%H:%M:%S", &timeinfo);
  return String(buffer);
}

void loop() {
  static unsigned long sampleTime = millis();
  if (millis() - sampleTime > 40U) {
    sampleTime = millis();
    analogBuffer[analogBufferIndex++] = analogRead(TDS_PIN);
    if (analogBufferIndex == SCOUNT) analogBufferIndex = 0;
  }
  
  if (millis() - lastRead >= READ_INTERVAL) {
    lastRead = millis();
    
    tempSensor.requestTemperatures();
    delay(100);
    float tempC = tempSensor.getTempCByIndex(0);
    
    for (int i = 0; i < SCOUNT; i++) {
      analogBufferTemp[i] = analogBuffer[i];
    }
    int medianADC = getMedianNum(analogBufferTemp, SCOUNT);
    float voltage = medianADC * (VREF / 4095.0);
    float compensationCoefficient = 1.0 + 0.02 * (tempC - 25.0);
    float compensationVoltage = voltage / compensationCoefficient;
    float tdsValue = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage 
                     - 255.86 * compensationVoltage * compensationVoltage 
                     + 857.39 * compensationVoltage) * 0.5;
    
    bool tempOK = (tempC > 0 && tempC < 50);
    bool tdsOK = (medianADC >= 50 && medianADC <= 4000);
    String status = (tempOK && tdsOK) ? "OK" : "ERROR";
    
    if (CALIBRATION_MODE) {
      Serial.printf("%4d | %.3fV | %.0f ppm\n", medianADC, voltage, tdsValue);
      return;
    }
    
    // Get current timestamp
    unsigned long timestamp = getCurrentTimestamp();
    String timeStr = getFormattedTime();
    
    Serial.printf("%s | %.1f | %.0f | %s | ", timeStr.c_str(), tempC, tdsValue, status.c_str());
    
    if (Firebase.ready()) {
      // Update current reading with real timestamp
      json.clear();
      json.set("temperature", tempC);
      json.set("tds", tdsValue);
      json.set("status", status);
      json.set("timestamp", timestamp);
      
      if (Firebase.setJSON(firebaseData, "/current", json)) {
        Serial.print("CURRENT ✓ ");
      } else {
        Serial.print("CURRENT ✗ ");
      }
      
      // Log history every 10 seconds with real timestamp
      if (millis() - lastHistory >= HISTORY_INTERVAL) {
        lastHistory = millis();
        
        json.clear();
        json.set("temperature", tempC);
        json.set("tds", tdsValue);
        json.set("status", status);
        json.set("timestamp", timestamp);
        
        if (Firebase.pushJSON(firebaseData, "/readings", json)) {
          Serial.println("HISTORY ✓");
        } else {
          Serial.println("HISTORY ✗");
        }
      } else {
        Serial.println("");
      }
    } else {
      Serial.println("NOT READY");
    }
  }
}

int getMedianNum(int bArray[], int iFilterLen) {
  int bTab[iFilterLen];
  for (byte i = 0; i < iFilterLen; i++) bTab[i] = bArray[i];
  
  for (int j = 0; j < iFilterLen - 1; j++) {
    for (int i = 0; i < iFilterLen - j - 1; i++) {
      if (bTab[i] > bTab[i + 1]) {
        int temp = bTab[i];
        bTab[i] = bTab[i + 1];
        bTab[i + 1] = temp;
      }
    }
  }
  
  return ((iFilterLen & 1) > 0) ? bTab[(iFilterLen - 1) / 2] : 
         (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
}
