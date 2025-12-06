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

OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

int analogBuffer[SCOUNT];
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;

unsigned long lastRead = 0;
const unsigned long READ_INTERVAL = 3000;

void setup() {
  Serial.begin(115200);

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi: Connected");
  Serial.println(WiFi.localIP());

  // Firebase
  config.database_url = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("Firebase: Initializing...");
  delay(2000);

  if (Firebase.ready()) {
    Serial.println("Firebase: Ready ✓");
  } else {
    Serial.println("Firebase: Failed ✗");
  }

  // Sensors
  tempSensor.begin();
  pinMode(TDS_PIN, INPUT);

  Serial.println("\nTemp | TDS | Status | Firebase");
  Serial.println("────────────────────────────────");
}

void loop() {
  // Background TDS sampling
  static unsigned long sampleTime = millis();
  if (millis() - sampleTime > 40U) {
    sampleTime = millis();
    analogBuffer[analogBufferIndex++] = analogRead(TDS_PIN);
    if (analogBufferIndex == SCOUNT) analogBufferIndex = 0;
  }

  // Read and upload every 3 seconds
  if (millis() - lastRead >= READ_INTERVAL) {
    lastRead = millis();

    // Get temperature
    tempSensor.requestTemperatures();
    delay(100);
    float tempC = tempSensor.getTempCByIndex(0);

    // Get TDS
    for (int i = 0; i < SCOUNT; i++) {
      analogBufferTemp[i] = analogBuffer[i];
    }
    int medianADC = getMedianNum(analogBufferTemp, SCOUNT);
    float voltage = medianADC * (VREF / 4095.0);
    float compensationCoefficient = 1.0 + 0.02 * (tempC - 25.0);
    float compensationVoltage = voltage / compensationCoefficient;
    float tdsValue = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage
                      - 255.86 * compensationVoltage * compensationVoltage
                      + 857.39 * compensationVoltage)
                     * 0.5;

    // Status check
    bool tempOK = (tempC > 0 && tempC < 50);
    bool tdsOK = (medianADC >= 50 && medianADC <= 4000);
    String status = (tempOK && tdsOK) ? "OK" : "ERROR";

    // Console output
    Serial.printf("%.1f | %.0f | %s | ", tempC, tdsValue, status.c_str());

    // Firebase upload
    if (Firebase.ready()) {
      FirebaseJson json;
      json.set("temperature", tempC);
      json.set("tds", tdsValue);
      json.set("status", status);
      json.set("timestamp", (unsigned long)(millis() / 1000));

      if (Firebase.setJSON(firebaseData, "/current", json)) {
        Serial.println("SENT ✓");
      } else {
        Serial.println("FAILED");
        Serial.println(firebaseData.errorReason());
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

  return ((iFilterLen & 1) > 0) ? bTab[(iFilterLen - 1) / 2] : (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
}
