#include <Arduino.h>
#include <limits.h>  // for LONG_MAX

// -------- Pin Config (ESP8266 NodeMCU) --------
#define S0 D1
#define S1 D2
#define S2 D6
#define S3 D7
#define OUT D5
#define LED_PIN D0   // <-- yaha LED pin connect kar (TCS3200 ka LED pin)

// --------- Helpers ---------
static inline float clampf(float v, float lo, float hi) { 
  return v < lo ? lo : (v > hi ? hi : v); 
}

// --------- Simple Color Reference Table ---------
struct ColorRef {
  const char* name;
  int r, g, b;
};

ColorRef colors[] = {
  {"Red", 255, 0, 0},
  {"Green", 0, 255, 0},
  {"Blue", 0, 0, 255},
  {"White", 255, 255, 255},
  {"Black", 0, 0, 0},
  {"Gray", 128, 128, 128},
  {"Yellow", 255, 255, 0},
  {"Cyan", 0, 255, 255},
  {"Magenta", 255, 0, 255},
  {"Orange", 255, 165, 0},
  {"Purple", 128, 0, 128}
};
int numColors = sizeof(colors) / sizeof(colors[0]);

// --------- Read Color ---------
int readColor(bool s2, bool s3) {
  digitalWrite(S2, s2);
  digitalWrite(S3, s3);
  delay(20); // let sensor settle
  return pulseIn(OUT, LOW);
}

// Convert freq → 0–255 RGB
int scaleFreq(int f, int minF, int maxF) {
  f = constrain(f, minF, maxF);
  return map(f, minF, maxF, 255, 0); // higher freq = lower intensity
}

// Find nearest known color
String nearestColorName(int r, int g, int b) {
  long best = LONG_MAX;
  String name = "Unknown";
  for (int i = 0; i < numColors; i++) {
    long dr = r - colors[i].r;
    long dg = g - colors[i].g;
    long db = b - colors[i].b;
    long dist = dr*dr + dg*dg + db*db;
    if (dist < best) {
      best = dist;
      name = colors[i].name;
    }
  }
  return name;
}

void setup() {
  Serial.begin(9600);

  pinMode(S0, OUTPUT);
  pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT);
  pinMode(S3, OUTPUT);
  pinMode(OUT, INPUT);
  pinMode(LED_PIN, OUTPUT);

  // set scaling
  digitalWrite(S0, HIGH);
  digitalWrite(S1, LOW);

  // ---- LEDs OFF ----
  digitalWrite(LED_PIN, HIGH);

  Serial.println("TCS3200 Color Sensor Ready (LEDs OFF)");
}

void loop() {
  int rFreq = readColor(LOW, LOW);
  int gFreq = readColor(HIGH, HIGH);
  int bFreq = readColor(LOW, HIGH);

  // Calibration ranges (adjust as per your sensor)
  int R = scaleFreq(rFreq, 200, 2000);
  int G = scaleFreq(gFreq, 200, 2000);
  int B = scaleFreq(bFreq, 200, 2000);

  // Clamp
  R = clampf(R, 0, 255);
  G = clampf(G, 0, 255);
  B = clampf(B, 0, 255);

  // HEX string
  char hexCol[8];
  sprintf(hexCol, "#%02X%02X%02X", R, G, B);

  // Nearest name
  String cname = nearestColorName(R, G, B);

  // Print
  Serial.print("Color -> R: ");
  Serial.print(R);
  Serial.print("  G: ");
  Serial.print(G);
  Serial.print("  B: ");
  Serial.print(B);
  Serial.print("  |  HEX: ");
  Serial.print(hexCol);
  Serial.print("  |  Name: ");
  Serial.println(cname);

  delay(500);
}