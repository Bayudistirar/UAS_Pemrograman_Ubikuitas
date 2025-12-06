#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <FirebaseESP32.h>

// WiFi credentials
#define WIFI_SSID "BAYU"
#define WIFI_PASSWORD "musabayu"

// Firebase credentials
#define FIREBASE_HOST "water-monitoring-54106-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH "jb4Tk9uWl2s3Icsdq5KpyPy5QKuwbrzlO1WUDLsY"

// Pins
#define TEMP_PIN 27
#define TDS_PIN 34

// TDS config
#define VREF 3.3
#define SCOUNT 30

// Calibration mode - set true untuk kalibrasi
#define CALIBRATION_MODE false

OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

int analogBuffer[SCOUNT];
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;

unsigned long lastRead = 0;
unsigned long lastHistory = 0;
const unsigned long READ_INTERVAL = 3000;      // Update current every 3s
const unsigned long HISTORY_INTERVAL = 60000;  // Log history every 1 min

void setup() {
  Serial.begin(115200);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi: Connected");
  Serial.println(WiFi.localIP());
  
  config.database_url = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  
  Serial.println("Firebase: Ready");
  
  tempSensor.begin();
  pinMode(TDS_PIN, INPUT);
  
  if (CALIBRATION_MODE) {
    Serial.println("\n=== CALIBRATION MODE ===");
    Serial.println("Place sensor in known TDS solution");
    Serial.println("ADC | Voltage | TDS");
  } else {
    Serial.println("\nTemp | TDS | Status | Firebase");
    Serial.println("────────────────────────────────");
  }
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
    
    // Calibration output
    if (CALIBRATION_MODE) {
      Serial.printf("%4d | %.3fV | %.0f ppm\n", medianADC, voltage, tdsValue);
      return; // Skip Firebase in calibration mode
    }
    
    // Normal output
    Serial.printf("%.1f | %.0f | %s | ", tempC, tdsValue, status.c_str());
    
    // Update current reading
    if (Firebase.ready()) {
      FirebaseJson current;
      current.set("temperature", tempC);
      current.set("tds", tdsValue);
      current.set("status", status);
      current.set("timestamp", millis() / 1000);
      
      if (Firebase.setJSON(firebaseData, "/current", current)) {
        Serial.print("CURRENT ✓ ");
      } else {
        Serial.print("FAILED ");
      }
      
      // Log history every minute
      if (millis() - lastHistory >= HISTORY_INTERVAL) {
        lastHistory = millis();
        
        FirebaseJson history;
        history.set("temperature", tempC);
        history.set("tds", tdsValue);
        history.set("status", status);
        history.set("timestamp", millis() / 1000);
        
        if (Firebase.pushJSON(firebaseData, "/readings", history)) {
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
